"""
Tests for sending commands that are too big for one write.

The real limit is 100MB, which is too slow to test against, so nearly every
test here shrinks it with monkeypatch. The whole point of the feature is
that a chunked call and a normal call are indistinguishable, so most of
these run the same call both ways and compare.
"""

import asyncio
import json

import logistro
import pytest
import pytest_asyncio

from choreographer.channels import MessageTooLargeError, pipe
from choreographer.protocol import _chunking

pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)

_N_VALUES = 2000
_MIN_CHUNKED_MESSAGES = 3  # init + at least one push + the real call
_MIN_REAL_CHUNKED_MESSAGES = 5  # at the real 10MiB chunk size, expect about 14

_ECHO_FN = (
    "function(spec, tag){"
    "return JSON.stringify({"
    "type: typeof spec,"
    "n: spec.values.length,"
    "first: spec.values[0],"
    "last: spec.values[spec.values.length - 1],"
    "text: spec.text,"
    "tag: tag"
    "});"
    "}"
)


def _spec(n=_N_VALUES, text="plain"):
    return {"values": list(range(n)), "text": text}


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def js(browser):
    """Give back a tab session with a JavaScript context to run functions in."""
    tab = await browser.create_tab("")
    session = await tab.create_session()
    context = session.subscribe_once("Runtime.executionContextCreated")
    await session.send_command("Page.enable")
    await session.send_command("Runtime.enable")
    js_id = (await context)["params"]["context"]["id"]
    yield session, js_id
    await tab.close_session(session.session_id)
    await browser.close_tab(tab.target_id)


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def js_unique(browser):
    """Like `js`, but hands back the context's uniqueId instead of its id."""
    tab = await browser.create_tab("")
    session = await tab.create_session()
    context = session.subscribe_once("Runtime.executionContextCreated")
    await session.send_command("Page.enable")
    await session.send_command("Runtime.enable")
    unique_id = (await context)["params"]["context"]["uniqueId"]
    yield session, unique_id
    await tab.close_session(session.session_id)
    await browser.close_tab(tab.target_id)


async def _call(session, js_id, fn=_ECHO_FN, args=None, **extra):
    params = {
        "functionDeclaration": fn,
        "arguments": [{"value": a} for a in (args if args is not None else [])],
        "executionContextId": js_id,
        "returnByValue": False,
        "awaitPromise": True,
    }
    params.update(extra)
    return await session.send_command("Runtime.callFunctionOn", params=params)


def _value(response):
    return response["result"]["result"]["value"]


async def _store_keys(session, js_id):
    response = await _call(
        session,
        js_id,
        fn=(
            "function(){"
            "return JSON.stringify("
            "window.__choreo_chunks ? Object.keys(window.__choreo_chunks) : []"
            ");"
            "}"
        ),
    )
    return json.loads(_value(response))


def _shrink(monkeypatch, max_size=4096, chunk_size=512):
    monkeypatch.setattr(pipe, "MAX_MESSAGE_SIZE", max_size)
    monkeypatch.setattr(_chunking, "CHUNK_SIZE", chunk_size)


async def test_chunked_matches_unchunked(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    args = [_spec(), "hello"]

    plain = _value(await _call(session, js_id, args=args))

    _shrink(monkeypatch)
    chunked = _value(await _call(session, js_id, args=args))

    assert json.loads(chunked) == json.loads(plain)
    assert json.loads(chunked)["type"] == "object"
    assert json.loads(chunked)["n"] == _N_VALUES


async def test_chunking_actually_happened(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    before = session.message_id
    await _call(session, js_id, args=[_spec(), "hello"])
    assert session.message_id - before > _MIN_CHUNKED_MESSAGES


async def test_store_is_cleaned_up(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    await _call(session, js_id, args=[_spec(), "hello"])

    monkeypatch.undo()
    assert await _store_keys(session, js_id) == []


async def test_error_in_function_still_reports_and_cleans_up(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    response = await _call(
        session,
        js_id,
        fn="function(spec){ throw new Error('boom ' + spec.values.length); }",
        args=[_spec()],
    )
    assert "exceptionDetails" in response["result"]
    assert "boom 2000" in json.dumps(response["result"]["exceptionDetails"])

    monkeypatch.undo()
    assert await _store_keys(session, js_id) == []


async def test_promise_is_awaited(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    response = await _call(
        session,
        js_id,
        fn=(
            "function(spec){return Promise.resolve('resolved ' + spec.values.length);}"
        ),
        args=[_spec()],
    )
    assert _value(response) == "resolved 2000"


async def test_return_by_value(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    response = await _call(
        session,
        js_id,
        fn="function(spec){ return {n: spec.values.length}; }",
        args=[_spec()],
        returnByValue=True,
    )
    assert _value(response) == {"n": 2000}


async def test_with_perf_survives_chunking(js, monkeypatch):
    """
    `with_perf` has to keep working when the send gets broken up.

    Timings are looked up by message key, and the original command's write
    never happened, so its key has no entry in `write_perfs`. `send_chunked`
    hands back the command that actually went out so the lookup lands on that
    one instead. Drop that and this raises `KeyError`.

    Note the timings then describe only the final message, not the pushes.
    """
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    response, perf = await session.send_command(
        "Runtime.callFunctionOn",
        params={
            "functionDeclaration": _ECHO_FN,
            "arguments": [{"value": _spec()}, {"value": "hello"}],
            "executionContextId": js_id,
            "awaitPromise": True,
        },
        with_perf=True,
    )

    assert json.loads(_value(response))["n"] == _N_VALUES
    write_start, write_end, read_end = perf
    assert write_start <= write_end <= read_end


async def test_non_ascii_survives_the_split(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    text = "héllo — 😀 中文 " * 200
    args = [_spec(text=text), "tag"]

    plain = json.loads(_value(await _call(session, js_id, args=args)))

    _shrink(monkeypatch)
    chunked = json.loads(_value(await _call(session, js_id, args=args)))

    assert chunked["text"] == text
    assert chunked == plain


async def test_several_large_arguments(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    response = await _call(
        session,
        js_id,
        fn=(
            "function(a, b, c){"
            "return JSON.stringify([a.values.length, b.values.length, c]);"
            "}"
        ),
        args=[_spec(1000), _spec(1500), "tail"],
    )
    assert json.loads(_value(response)) == [1000, 1500, "tail"]


async def test_concurrent_chunked_calls_do_not_collide(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    responses = await asyncio.gather(
        _call(session, js_id, args=[_spec(1000), "first"]),
        _call(session, js_id, args=[_spec(2000), "second"]),
    )
    first, second = (json.loads(_value(r)) for r in responses)

    assert (first["n"], first["tag"]) == (1000, "first")
    assert (second["n"], second["tag"]) == (2000, "second")

    monkeypatch.undo()
    assert await _store_keys(session, js_id) == []


async def test_unchunkable_command_raises(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    with pytest.raises(MessageTooLargeError):
        await session.send_command(
            "Page.navigate",
            params={"url": "data:text/html," + ("x" * 8192)},
        )

    # The channel was never written to, so the session still works.
    monkeypatch.undo()
    assert _value(await _call(session, js_id, args=[_spec(10), "after"]))


async def test_lost_store_mid_send_raises(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)
    # Intentionally break init function to trigger this error
    monkeypatch.setattr(_chunking, "_INIT_FN", "function(k){ }")

    with pytest.raises(RuntimeError, match="Chunked send failed in the page"):
        await _call(session, js_id, args=[_spec(), "hello"])


async def test_unique_context_id_is_followed(js_unique, monkeypatch):
    _logger.info("testing...")
    session, unique_id = js_unique
    _shrink(monkeypatch)

    response = await session.send_command(
        "Runtime.callFunctionOn",
        params={
            "functionDeclaration": _ECHO_FN,
            "arguments": [{"value": _spec()}, {"value": "hello"}],
            "uniqueContextId": unique_id,
            "awaitPromise": True,
        },
    )

    got = json.loads(_value(response))
    assert got["n"] == _N_VALUES
    assert got["tag"] == "hello"


async def test_throw_on_side_effect_is_refused(js, monkeypatch):
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    with pytest.raises(MessageTooLargeError):
        await _call(session, js_id, args=[_spec(), "hello"], throwOnSideEffect=True)

    # The important half: we declined before writing anything to the page.
    monkeypatch.undo()
    assert await _store_keys(session, js_id) == []


async def test_object_id_arguments_are_not_chunked(js, monkeypatch):
    """Browser-side handles can't be rebuilt from text, so don't try."""
    _logger.info("testing...")
    session, js_id = js
    handle = await _call(
        session,
        js_id,
        fn="function(){ return {a: 1}; }",
    )
    object_id = handle["result"]["result"]["objectId"]

    _shrink(monkeypatch)
    with pytest.raises(MessageTooLargeError):
        await session.send_command(
            "Runtime.callFunctionOn",
            params={
                "functionDeclaration": "function(o, pad){ return o.a; }",
                "arguments": [{"objectId": object_id}, {"value": "x" * 8192}],
                "executionContextId": js_id,
            },
        )


async def test_oversized_function_does_not_recurse(js, monkeypatch):
    """
    A huge functionDeclaration can't be helped by chunking.

    The wrapper we'd build is bigger than the message we're replacing, so it
    has to give up rather than fall back into itself forever.
    """
    _logger.info("testing...")
    session, js_id = js
    _shrink(monkeypatch)

    with pytest.raises(MessageTooLargeError):
        await _call(
            session,
            js_id,
            fn="function(x){ var s = '" + ("y" * 8192) + "'; return s.length; }",
            args=[1],
        )


@pytest.mark.slow
async def test_real_oversized_payload(js):
    """
    The only test that uses Chrome's actual limit, so it is the slow one.

    The padding is stamped with its own offset every 1000 characters, so a
    dropped piece or two pieces arriving out of order changes the answer.
    A payload of all one character would hide both.
    """
    _logger.info("testing...")
    session, js_id = js

    stride = 1000
    n_pieces = 115_000  # About 110MiB (over the limit)
    pad = "".join(f"{i:08d}" + "y" * (stride - 8) for i in range(n_pieces))
    marks = [0, 5_000, 50_000, n_pieces - 1]
    spec = {"pad": pad, "tail": "héllo 😀"}

    before = session.message_id
    response = await _call(
        session,
        js_id,
        fn=(
            "function(spec, offsets, stride){"
            "return JSON.stringify({"
            "len: spec.pad.length,"
            "tail: spec.tail,"
            "marks: offsets.map(function(k){"
            "return spec.pad.substr(k * stride, 8);"
            "})"
            "});"
            "}"
        ),
        args=[spec, marks, stride],
    )
    got = json.loads(_value(response))
    sent = session.message_id - before

    # Without this the test would still pass if the payload ever slipped under
    # the real limit, quietly measuring nothing.
    assert sent > _MIN_REAL_CHUNKED_MESSAGES, (
        f"only {sent} messages sent: the payload did not get chunked"
    )
    assert got["len"] == n_pieces * stride
    assert got["tail"] == "héllo 😀"
    assert got["marks"] == [f"{k:08d}" for k in marks]
    assert await _store_keys(session, js_id) == []


async def test_error_text_does_not_include_payload():
    _logger.info("testing...")
    error = MessageTooLargeError(200, 100, payload="SECRET" * 100)
    assert "SECRET" not in str(error)
    assert "SECRET" not in repr(error)
    assert error.payload is not None
