from __future__ import annotations

import asyncio
import warnings
from typing import TYPE_CHECKING

import logistro

from choreographer import channels, protocol

# afrom choreographer.channels import ChannelClosedError

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from typing import Any

    from choreographer.browser_async import Browser
    from choreographer.channels._interface_type import ChannelInterface
    from choreographer.protocol.devtools_async import Session, Target


_logger = logistro.getLogger(__name__)


class UnhandledMessageWarning(UserWarning):
    pass


class Broker:
    """Broker is a middleware implementation for asynchronous implementations."""

    _browser: Browser
    """Browser is a reference to the Browser object this broker is brokering for."""
    _channel: ChannelInterface
    """
    Channel will be the ChannelInterface implementation (pipe or websocket)
    that the broker communicates on.
    """
    futures: MutableMapping[protocol.MessageKey, asyncio.Future[Any]]
    """A mapping of all the futures for all sent commands."""

    _subscriptions_futures: MutableMapping[
        str,
        MutableMapping[
            str,
            list[asyncio.Future[Any]],
        ],
    ]
    """A mapping of session id: subscription: list[futures]"""

    def __init__(self, browser: Browser, channel: ChannelInterface) -> None:
        """
        Construct a broker for a synchronous arragenment w/ both ends.

        Args:
            browser: The sync browser implementation.
            channel: The channel the browser uses to talk on.

        """
        self._browser = browser
        self._channel = channel
        self._background_tasks: set[asyncio.Task[Any]] = set()
        # if its a task you dont want canceled at close (like the close task)
        self._background_tasks_cancellable: set[asyncio.Task[Any]] = set()
        # if its a user task, can cancel
        self._current_read_task: asyncio.Task[Any] | None = None
        self.futures = {}
        self._subscriptions_futures = {}

    def new_subscription_future(
        self,
        session_id: str,
        subscription: str,
    ) -> asyncio.Future[Any]:
        if session_id not in self._subscriptions_futures:
            self._subscriptions_futures[session_id] = {}
        if subscription not in self._subscriptions_futures[session_id]:
            self._subscriptions_futures[session_id][subscription] = []
        future = asyncio.get_running_loop().create_future()
        self._subscriptions_futures[session_id][subscription].append(future)
        return future

    async def clean(self) -> None:
        for future in self.futures.values():
            if not future.done():
                future.cancel()
        if self._current_read_task and not self._current_read_task.done():
            self._current_read_task.cancel()
        for session in self._subscriptions_futures.values():
            for query in session.values():
                for future in query:
                    if not future.done():
                        future.cancel()
        for task in self._background_tasks_cancellable:
            if not task.done():
                task.cancel()

    def run_read_loop(self) -> None:  # noqa: C901, PLR0915 complexity
        def check_error(result: asyncio.Future[Any]) -> None:
            try:
                e = result.exception()
                if e:
                    self._background_tasks.add(
                        asyncio.create_task(self._browser.close()),
                    )
                    if not isinstance(e, asyncio.CancelledError):
                        _logger.error(f"Error in run_read_loop: {e!s}")
                        raise e
            except asyncio.CancelledError:
                self._background_tasks.add(asyncio.create_task(self._browser.close()))

        async def read_loop() -> None:  # noqa: PLR0912, C901
            try:
                responses = await asyncio.to_thread(
                    self._channel.read_jsons,
                    blocking=True,
                )
                for response in responses:
                    error = protocol.get_error_from_result(response)
                    key = protocol.calculate_message_key(response)
                    if not key and error:
                        raise protocol.DevtoolsProtocolError(response)
                    self._check_for_closed_session(response)
                    # surrounding lines overlap in idea
                    if protocol.is_event(response):
                        event_session_id = response.get(
                            "sessionId",
                            "",
                        )
                        x = self._get_target_session_by_session_id(
                            event_session_id,
                        )
                        if not x:
                            continue
                        _, event_session = x
                        if not event_session:
                            _logger.error("Found an event that returned no session.")
                            continue

                        session_futures = self._subscriptions_futures.get(
                            event_session_id,
                        )
                        if session_futures:
                            for query in session_futures:
                                match = (
                                    query.endswith("*")
                                    and response["method"].startswith(query[:-1])
                                ) or (response["method"] == query)
                                if match:
                                    for future in session_futures[query]:
                                        if not future.done():
                                            future.set_result(response)
                                    session_futures[query] = []

                        for query in list(event_session.subscriptions):
                            match = (
                                query.endswith("*")
                                and response["method"].startswith(query[:-1])
                            ) or (response["method"] == query)
                            _logger.debug(
                                f"Checking subscription key: {query} "
                                "against event method {response['method']}",
                            )
                            if match:
                                t: asyncio.Task[Any] = asyncio.create_task(
                                    event_session.subscriptions[query][0](response),
                                )
                                self._background_tasks_cancellable.add(t)
                                if not event_session.subscriptions[query][1]:
                                    event_session.unsubscribe(query)

                    elif key:
                        if key in self.futures:
                            _logger.debug(f"run_read_loop() found future for key {key}")
                            future = self.futures.pop(key)
                        elif "error" in response:
                            raise protocol.DevtoolsProtocolError(response)
                        else:
                            raise RuntimeError(f"Couldn't find a future for key: {key}")
                        future.set_result(response)
                    else:
                        warnings.warn(  # noqa: B028
                            f"Unhandled message type:{response!s}",
                            UnhandledMessageWarning,
                        )
            except channels.ChannelClosedError:
                _logger.debug("PipeClosedError caught")
                self._background_tasks.add(asyncio.create_task(self._browser.close()))
                return
            read_task = asyncio.create_task(read_loop())
            read_task.add_done_callback(check_error)
            self._current_read_task = read_task

        read_task = asyncio.create_task(read_loop())
        read_task.add_done_callback(check_error)
        self._current_read_task = read_task

    async def write_json(
        self,
        obj: protocol.BrowserCommand,
    ) -> protocol.BrowserResponse:
        _logger.debug2(f"In broker.write_json for {obj}")
        protocol.verify_params(obj)
        key = protocol.calculate_message_key(obj)
        if not key:
            raise RuntimeError(
                "Message strangely formatted and "
                "choreographer couldn't figure it out why.",
            )
        loop = asyncio.get_running_loop()
        future: asyncio.Future[protocol.BrowserResponse] = loop.create_future()
        self.futures[key] = future
        try:
            await asyncio.to_thread(self._channel.write_json, obj)
        except BaseException as e:  # noqa: BLE001
            future.set_exception(e)
            del self.futures[key]
        return await future

    def _get_target_session_by_session_id(
        self,
        session_id: str,
    ) -> tuple[Target, Session] | None:
        if session_id == "":
            return (self._browser, self._browser.sessions[session_id])
        for tab in self._browser.tabs.values():
            if session_id in tab.sessions:
                return (tab, tab.sessions[session_id])
        if session_id in self._browser.sessions:
            return (self._browser, self._browser.sessions[session_id])
        return None

    def _check_for_closed_session(self, response: protocol.BrowserResponse) -> bool:
        if "method" in response and response["method"] == "Target.detachedFromTarget":
            session_closed = response["params"].get(
                "sessionId",
                "",
            )
            if session_closed == "":
                return True

            x = self._get_target_session_by_session_id(session_closed)
            if x:
                target_closed, _ = x
            else:
                return False

            if target_closed:
                target_closed._remove_session(session_closed)  # noqa: SLF001
                _logger.debug(
                    "Using intern subscription key: "
                    "'Target.detachedFromTarget'. "
                    f"Session {session_closed} was closed.",
                )
                return True
            return False
        else:
            return False
