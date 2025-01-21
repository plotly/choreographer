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
        self.futures = {}

    def send_json(self, obj: protocol.BrowserCommand) -> protocol.MessageKey | None:
        """
        Send an object down the channel.

        Args:
            obj: An object to be serialized to json and written to the channel.

        """
        protocol.verify_params(obj)
        key = protocol.calculate_message_key(obj)
        self._channel.write_json(obj)
        return key

    async def clean(self) -> None:
        for key, future in self.futures.items():
            if not future.done():
                future.cancel()
            del self.futures[key]

    def run_read_loop(self) -> None:  # noqa: C901 complexity
        def check_error(result: asyncio.Future[Any]) -> None:
            e = result.exception()
            if e:
                self._background_tasks.add(asyncio.create_task(self._browser.close()))
                if not isinstance(e, asyncio.CancelledError):
                    _logger.error(f"Error in run_read_loop: {e!s}")
                    raise e

        async def read_loop() -> None:
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
                    # aelif self.protocol.is_event(response):
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
            self._background_tasks.add(read_task)

        read_task = asyncio.create_task(read_loop())
        read_task.add_done_callback(check_error)
        self._background_tasks.add(read_task)

    async def write_json(
        self,
        obj: protocol.BrowserCommand,
    ) -> asyncio.Future[Any]:
        protocol.verify_params(obj)
        key = protocol.calculate_message_key(obj)
        if not key:
            raise RuntimeError(
                "Message strangely formatted and "
                "choreographer couldn't figure it out why.",
            )
        future = asyncio.get_running_loop().create_future()
        self.futures[key] = future
        try:
            await asyncio.to_thread(self._channel.write_json, obj)
        except:
            future.cancel()
            del self.futures[key]
            raise
        return future
