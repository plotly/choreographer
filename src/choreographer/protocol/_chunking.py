"""
Break up `Runtime.callFunctionOn` commands that are too big for the pipe.

Chrome reads one complete JSON message at a time off the devtools pipe, and
it won't read one bigger than 100MB (see `channels.pipe.MAX_MESSAGE_SIZE`).
The devtools protocol has no way to split a message, so in general an
oversized command is simply an error.

`Runtime.callFunctionOn` is the exception. We can stash pieces of the
message in a JavaScript array on the page, then run a function that glues
them back together. That's what this module does.

None of this is part of the public API. `Session.send_command` falls back to
it on its own, and the function you asked Chrome to run can't tell the
difference: it still receives the same parsed arguments it always would.
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

import logistro

from . import DevtoolsProtocolError

if TYPE_CHECKING:
    from typing import Any, MutableMapping

    from . import BrowserCommand, BrowserResponse
    from .devtools_async import Session

_logger = logistro.getLogger(__name__)

CHUNK_SIZE = 10 * 1024 * 1024
"""
How much of the message to put in each piece, in characters.

Deliberately well under `MAX_MESSAGE_SIZE`. Each piece travels as a JSON
string, and escaping can (in the worst case, a payload of nothing but
quotes) double its length, so we leave a lot of room.
"""

_CHUNKABLE_METHOD = "Runtime.callFunctionOn"
"""The one command we know how to break up."""

_HELPER_METHOD = "Runtime.callFunctionOn"
"""
How we send our own setup, push, and cleanup calls.

This is always `Runtime.callFunctionOn`, whatever the oversized command we
were handed happens to be. It only matches `_CHUNKABLE_METHOD` today because
that is the one method we can break up.
"""

_STORE = "window.__choreo_chunks"

# `arguments` entries can also be `objectId` or `unserializableValue`
# handles, which refer to things that only exist in the browser. Those can't
# be rebuilt from the text of the message, so we only take the plain ones.
_VALUE_KEY = "value"

_INIT_FN = f"function(k){{ ({_STORE} = {_STORE} || {{}})[k] = []; }}"

_PUSH_FN = f"function(k, c){{ {_STORE}[k].push(c); }}"

_DELETE_FN = f"function(k){{ if ({_STORE}) {{ delete {_STORE}[k]; }} }}"

_counter = itertools.count()


def is_chunkable(command: BrowserCommand) -> bool:
    """
    Report whether we know how to break this command up.

    Args:
        command: The command that was too big to send

    """
    if command.get("method") != _CHUNKABLE_METHOD:
        return False
    params = command.get("params") or {}
    if not params.get("functionDeclaration"):
        return False
    arguments = params.get("arguments") or []
    # If even one argument is a browser-side handle we can't rebuild the call
    # from the message text, so we don't try
    return bool(arguments) and all(
        isinstance(argument, dict) and _VALUE_KEY in argument for argument in arguments
    )


def _build_wrapper(user_fn: str) -> str:
    """
    Wrap the caller's function in one that rebuilds its arguments first.

    What we glue back together is the whole original command, not just the
    big argument, because that is exactly what we already had serialized.
    The extra envelope is a few hundred bytes on top of a very large
    message, and pulling the arguments out of it in JavaScript is cheap.
    """
    return (
        "function(k){"
        "try{"
        f"var cmd = JSON.parse({_STORE}[k].join(''));"
        "var args = cmd.params.arguments.map(function(a){ return a.value; });"
        f"return ({user_fn}).apply(this, args);"
        "}finally{"
        f"delete {_STORE}[k];"
        "}"
        "}"
    )


def _raise_for_error(response: BrowserResponse) -> BrowserResponse:
    if "error" in response:
        raise DevtoolsProtocolError(response)
    return response


def _js_error_text(details: MutableMapping[str, Any]) -> str:
    """Pull the readable part out of a `Runtime.exceptionDetails`."""
    # `text` is usually just "Uncaught", so check exception
    exception = details.get("exception") or {}

    return exception.get("description") or details.get("text") or "unknown error"


async def _send(
    session: Session,
    params: MutableMapping[str, Any],
) -> BrowserResponse:
    """Send one piece, going around the too-big fallback so we can't recurse."""
    response = _raise_for_error(
        await session._send_no_retry(_HELPER_METHOD, params),  # noqa: SLF001
    )
    # Check for JS error response since that won't throw a top-level error
    exception_details = response.get("result", {}).get("exceptionDetails")
    if exception_details:
        raise RuntimeError(
            f"Chunked send failed in the page: {_js_error_text(exception_details)}",
        )
    return response


async def send_chunked(
    session: Session,
    command: BrowserCommand,
    payload: str,
) -> tuple[BrowserResponse, BrowserCommand]:
    """
    Send an oversized `Runtime.callFunctionOn` in pieces.

    Args:
        session: The session the original command was sent on.
        command: The original command, too big to send in one go.
        payload: The already serialized command, from the error the pipe
            raised. We slice this rather than serializing all over again.

    Returns:
        The response to the final call, and the command that produced it
        (the caller needs it to look up timings).

    """
    params: MutableMapping[str, Any] = dict(command["params"])
    # The pieces have to run in the same execution context as the real call
    execution_context_params = {
        key: params[key] for key in ("executionContextId", "objectId") if key in params
    }
    # Two calls in one page must not share a store, or they'd eat each other.
    key = f"{session.session_id or 'browser'}:{next(_counter)}"

    # Use ceiling division to ensure whole number of chunks
    n_chunks = -(-len(payload) // CHUNK_SIZE)
    _logger.info(
        f"Message too big for one write, sending it as {n_chunks} pieces "
        f"under key {key}.",
    )

    try:
        await _send(
            session,
            {
                **execution_context_params,
                "functionDeclaration": _INIT_FN,
                "arguments": [{"value": key}],
            },
        )
        for start in range(0, len(payload), CHUNK_SIZE):
            await _send(
                session,
                {
                    **execution_context_params,
                    "functionDeclaration": _PUSH_FN,
                    "arguments": [
                        {"value": key},
                        {"value": payload[start : start + CHUNK_SIZE]},
                    ],
                },
            )

        params["functionDeclaration"] = _build_wrapper(
            command["params"]["functionDeclaration"],
        )
        params["arguments"] = [{"value": key}]
        # Everything else the caller asked for (awaitPromise, returnByValue,
        # silent, userGesture, the execution context) rides along untouched.
        final_command = session._build_command(  # noqa: SLF001
            _HELPER_METHOD,
            params,
        )
        response = await session._send_built(final_command)  # noqa: SLF001
    except Exception:
        await _cleanup(session, execution_context_params, key)
        raise
    return response, final_command


async def _cleanup(
    session: Session,
    execution_context_params: MutableMapping[str, Any],
    key: str,
) -> None:
    """Drop the store if we bailed out before the wrapper could."""
    try:
        await _send(
            session,
            {
                **execution_context_params,
                "functionDeclaration": _DELETE_FN,
                "arguments": [{"value": key}],
            },
        )
    except Exception:  # noqa: BLE001 we're already failing, don't make it worse
        _logger.debug(f"Couldn't clean up chunk store {key}.")
