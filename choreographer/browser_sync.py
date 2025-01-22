"""Provides the sync api: `BrowserSync`, `TabSync`."""

from __future__ import annotations

import subprocess
from threading import Lock
from typing import TYPE_CHECKING

import logistro

from ._brokers import BrokerSync
from .browsers import BrowserClosedError, BrowserFailedError, Chromium
from .channels import ChannelClosedError, Pipe
from .protocol.devtools_sync import SessionSync, TargetSync
from .utils._kill import kill

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from pathlib import Path
    from types import TracebackType
    from typing import Any, Self

    from .browsers._interface_type import BrowserImplInterface
    from .channels._interface_type import ChannelInterface

_logger = logistro.getLogger(__name__)


class TabSync(TargetSync):
    """A wrapper for `TargetSync`, so user can use `TabSync`, not `TargetSync`."""


class BrowserSync(TargetSync):
    """`BrowserSync` is the sync implementation of `Browser`."""

    _tab_type = TabSync
    _session_type = SessionSync
    _target_type = TargetSync
    _broker_type = BrokerSync
    # A list of the types that are essential to use
    # with this class

    tabs: MutableMapping[str, TabSync]
    """A mapping by target_id of all the targets which are open tabs."""
    targets: MutableMapping[str, TargetSync]
    """A mapping by target_id of ALL the targets."""
    # Don't init instance attributes with mutables

    def _make_lock(self) -> None:
        self._open_lock = Lock()

    def _is_open(self) -> bool:
        return not self._open_lock.acquire(blocking=False)

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
        # if hasattr(browser_cls, "logger_parser"):
        #    parser = browser_cls.logger_parser # noqa: ERA001
        # else: # noqa: ERA001
        #    parser = None # noqa: ERA001
        # self._logger_pipe, _ = logistro.getPipeLogger(
        #    "browser_proc",
        #    parser=parser, # noqa: ERA001
        # ) # BUG TODO REGRESSION
        self._logger_pipe = subprocess.DEVNULL

    def open(self) -> None:
        """Open the browser."""
        if self._is_open():
            raise RuntimeError("Can't re-open the browser")
        self.subprocess = subprocess.Popen(  # noqa: S603
            self._browser_impl.get_cli(),
            stderr=self._logger_pipe,
            env=self._browser_impl.get_env(),
            **self._browser_impl.get_popen_args(),
        )
        super().__init__("0", self._broker)
        self._add_session(self._session_type("", self._broker))

    def __enter__(self) -> Self:
        """Open browser as context to launch on entry and close on exit."""
        self.open()
        return self

    def _is_closed(self, wait: int | None = 0) -> bool:
        if wait == 0:
            return self.subprocess.poll() is None
        else:
            try:
                self.subprocess.wait(wait)
            except subprocess.TimeoutExpired:
                return False
        return True

    def _close(self) -> None:
        if self._is_closed():
            return

        try:
            self.send_command("Browser.close")
        except (BrowserClosedError, BrowserFailedError):
            return
        except ChannelClosedError:
            pass

        self._channel.close()
        if self._is_closed():
            return

        # try kiling
        kill(self.subprocess)
        if self._is_closed(wait=4):
            return
        else:
            raise RuntimeError("Couldn't close or kill browser subprocess")

    def close(self) -> None:
        """Close the browser."""
        self._broker.clean()
        _logger.info("Broker cleaned up.")
        if not self._release_lock():
            return
        try:
            _logger.info("Trying to close browser.")
            self._close()
            _logger.info("browser._close() called successfully.")
        except ProcessLookupError:
            pass
        # os.close(self._logger_pipe) # noqa: ERA001 bug regression
        _logger.info("Logging pipe closed.")
        self._channel.close()
        _logger.info("Browser channel closed.")
        self._browser_impl.clean()
        _logger.info("Browser implementation cleaned up.")

    def __exit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:  # None instead of False is fine, eases type checking
        """Close the browser."""
        self.close()

    def _add_tab(self, tab: TabSync) -> None:
        if not isinstance(tab, self._tab_type):
            raise TypeError(f"tab must be an object of {self._tab_type}")
        self.tabs[tab.target_id] = tab

    def _remove_tab(self, target_id: str) -> None:
        if isinstance(target_id, self._tab_type):
            target_id = target_id.target_id
        del self.tabs[target_id]

    def get_tab(self) -> TabSync | None:
        """Get the first tab if there is one. Useful for default tabs."""
        if self.tabs.values():
            return next(iter(self.tabs.values()))
        return None

    # wrap our broker for convenience
    def start_output_thread(self, **kwargs: Any) -> None:
        """
        Start a separate thread that dumps all messages received to stdout.

        Args:
            kwargs: passed directly to print().

        """
        self._broker.run_output_thread(**kwargs)
