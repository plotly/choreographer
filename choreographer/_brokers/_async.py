from __future__ import annotations

from typing import TYPE_CHECKING

import logistro

from choreographer import protocol

# afrom choreographer.channels import ChannelClosedError

if TYPE_CHECKING:
    from choreographer.browser_async import Browser
    from choreographer.channels._interface_type import ChannelInterface


_logger = logistro.getLogger(__name__)


class Broker:
    """Broker is a middleware implementation for asynchronous implementations."""

    _browser: Browser
    """Browser is a reference to the Browser object this broker is brokering for."""
    _channel: ChannelInterface
    """
    Channel will be the ChannelInterface implementation (pipe or websocket)
    that the broker communicates on.
    """

    def __init__(self, browser: Browser, channel: ChannelInterface) -> None:
        """
        Construct a broker for a synchronous arragenment w/ both ends.

        Args:
            browser: The sync browser implementation.
            channel: The channel the browser uses to talk on.

        """
        self._browser = browser
        self._channel = channel

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
        pass
