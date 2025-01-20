"""Provides the async api: `Browser`, `Tab`."""

from __future__ import annotations

import asyncio
import os
import subprocess
from asyncio import Lock
from typing import TYPE_CHECKING

import logistro

from ._brokers import Broker
from .browsers import BrowserClosedError, BrowserFailedError, Chromium
from .channels import ChannelClosedError, Pipe
from .protocol.devtools_async import Session, Target
from .utils._kill import kill

if TYPE_CHECKING:
    from collections.abc import Generator, MutableMapping
    from pathlib import Path
    from types import TracebackType
    from typing import Any, Self

    from .browsers._interface_type import BrowserImplInterface
    from .channels._interface_type import ChannelInterface

_logger = logistro.getLogger(__name__)


class Tab(Target):
    """A wrapper for `Target`, so user can use `Tab`, not `Target`."""


class Browser(Target):
    """`Browser` is the async implementation of `Browser`."""

    _tab_type = Tab
    _session_type = Session
    _target_type = Target
    _broker_type = Broker
    # A list of the types that are essential to use
    # with this class

    tabs: MutableMapping[str, Tab]
    """A mapping by target_id of all the targets which are open tabs."""
    targets: MutableMapping[str, Target]
    """A mapping by target_id of ALL the targets."""
    # Don't init instance attributes with mutables

    def _make_lock(self) -> None:
        self._open_lock = Lock()

    async def _is_open(self) -> bool:
        # Did we acquire the lock? If so, return true, we locked open.
        # If we are open, we did not lock open.
        # fuck, go through this again
        if self._open_lock.locked():
            return True
        await self._open_lock.acquire()
        return False

    def _release_lock(self) -> bool:
        try:
            if self._open_lock.locked():
                self._open_lock.release()
                return True
            else:
                return False
        except RuntimeError:
            return False

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        browser_cls: type[BrowserImplInterface] = Chromium,
        channel_cls: type[ChannelInterface] = Pipe,
        **kwargs: Any,
    ) -> None:
        """
        Construct a new browser instance.

        Args:
            path: The path to the browser executable.
            browser_cls: The type of browser (default: `Chromium`).
            channel_cls: The type of channel to browser (default: `Pipe`).
            kwargs: The arguments that the browser_cls takes. For example,
                headless=True/False, enable_gpu=True/False, etc.

        """
        _logger.debug("Attempting to open new browser.")
        self._make_lock()
        self.tabs = {}
        self.targets = {}

        # Compose Resources
        self._channel = channel_cls()
        self._broker = self._broker_type(self, self._channel)
        self._browser_impl = browser_cls(self._channel, path, **kwargs)
        if hasattr(browser_cls, "logger_parser"):
            parser = browser_cls.logger_parser
        else:
            parser = None
        self._logger_pipe, _ = logistro.getPipeLogger(
            "browser_proc",
            parser=parser,
        )
        # we do need something to indicate we're open TODO yeah an open lock

    async def open(self) -> None:
        """Open the browser."""
        if not self._is_open():
            raise RuntimeError("Can't re-open the browser")

        cli = self._browser_impl.get_cli()
        stderr = self._logger_pipe
        env = self._browser_impl.get_env()
        args = self._browser_impl.get_popen_args()

        # asyncio's equiv doesn't work in all situations
        def run() -> subprocess.Popen[bytes]:
            return subprocess.Popen(  # noqa: S603
                cli,
                stderr=stderr,
                env=env,
                **args,
            )

        # TODO How do we catch errors
        self.subprocess = await asyncio.to_thread(run)

        super().__init__("0", self._broker)
        self._add_session(self._session_type("", self._broker))

    async def __aenter__(self) -> Self:
        """Open browser as context to launch on entry and close on exit."""
        await self.open()
        return self

    # for use with `await Browser()`

    def __await__(self) -> Generator[Any, Any, None]:
        """If you await the `Browser()`, it will implicitly call `open()`."""
        return self.open().__await__()

    async def _is_closed(self, wait: int | None = 0) -> bool:
        if wait == 0:
            return self.subprocess.poll() is None
        else:
            try:
                # TODO: how do we catch errors?
                await asyncio.to_thread(self.subprocess.wait, wait)
            except subprocess.TimeoutExpired:
                return False
        return True

    async def _close(self) -> None:
        if await self._is_closed():
            return

        try:
            await self.send_command("Browser.close")
        except (BrowserClosedError, BrowserFailedError):
            return
        except ChannelClosedError:
            pass

        # TODO how do we handle errors
        await asyncio.to_thread(self._channel.close)

        if await self._is_closed():
            return

        # TODO how do we handle errors
        await asyncio.to_thread(kill, self.subprocess)
        if await self._is_closed(wait=4):
            return
        else:
            raise RuntimeError("Couldn't close or kill browser subprocess")

    async def close(self) -> None:
        """Close the browser."""
        await self._broker.clean()
        _logger.info("Broker cleaned up.")
        if not self._release_lock():
            return
        try:
            _logger.info("Trying to close browser.")
            await self._close()
            _logger.info("browser._close() called successfully.")
        except ProcessLookupError:
            pass
        os.close(self._logger_pipe)
        _logger.info("Logging pipe closed.")
        await asyncio.to_thread(self._channel.close)
        _logger.info("Browser channel closed.")
        await asyncio.to_thread(self._browser_impl.clean)
        _logger.info("Browser implementation cleaned up.")

    async def __aexit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:  # None instead of False is fine, eases type checking
        """Close the browser."""
        await self.close()

    def _add_tab(self, tab: Tab) -> None:
        if not isinstance(tab, self._tab_type):
            raise TypeError(f"tab must be an object of {self._tab_type}")
        self.tabs[tab.target_id] = tab

    def _remove_tab(self, target_id: str) -> None:
        if isinstance(target_id, self._tab_type):
            target_id = target_id.target_id
        del self.tabs[target_id]

    def get_tab(self) -> Tab | None:
        """Get the first tab if there is one. Useful for default tabs."""
        if self.tabs.values():
            return next(iter(self.tabs.values()))
        return None
