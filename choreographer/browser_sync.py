"""Provides the sync api: `BrowserSync`, `TabSync`."""

import os
import subprocess
from threading import Lock

import logistro

from ._brokers import BrokerSync
from .browsers import BrowserClosedError, BrowserFailedError, Chromium
from .channels import ChannelClosedError, Pipe
from .protocol.sync import SessionSync, TargetSync
from .utils._kill import kill

_logger = logistro.getLogger(__name__)


class TabSync(TargetSync):
    """A wrapper for `TargetSync`, so user can use `TabSync`, not `TargetSync`."""


class BrowserSync(TargetSync):
    """`BrowserSync` is the sync implementation of `Browser`."""

    _tab_type = TabSync
    _session_type = SessionSync
    _target_type = TargetSync

    def _make_lock(self):
        self._open_lock = Lock()

    def _lock_open(self):
        # if open, acquire will return False, we want it to return True
        return self._open_lock.acquire(blocking=False)

    def _release_lock(self):
        try:
            if self._open_lock.locked():
                self._open_lock.release()
                return True
            else:
                return False
        except RuntimeError:
            return False

    def __init__(self, path=None, *, browser_cls=Chromium, channel_cls=Pipe, **kwargs):
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
        self.all_sessions = {}
        # Compose Resources
        self.channel = channel_cls()
        self.broker = BrokerSync(self, self.channel)
        self.browser_impl = browser_cls(self.channel, path, **kwargs)
        if hasattr(browser_cls, "logger_parser"):
            parser = browser_cls.logger_parser
        else:
            parser = None
        self.logger_pipe, _ = logistro.getPipeLogger(
            "browser_proc",
            parser=parser,
        )
        # we do need something to indicate we're open TODO yeah an open lock

    def open(self):
        """Open the browser."""
        if not self._lock_open():
            raise RuntimeError("Can't re-open the browser")
        self.subprocess = subprocess.Popen(  # noqa: S603
            self.browser_impl.get_cli(),
            stderr=self.logger_pipe,
            env=self.browser_impl.get_env(),
            **self.browser_impl.get_popen_args(),
        )
        super().__init__("0", self)
        self._add_session(self._session_type(self, ""))

    def __enter__(self):
        """Open browser as context to launch on entry and close on exit."""
        self.open()
        return self

    def _is_closed(self, wait=0):
        if wait == 0:
            return self.subprocess.poll() is None
        else:
            try:
                self.subprocess.wait(wait)
            except subprocess.TimeoutExpired:
                return False
        return True

    def _close(self):
        if self._is_closed():
            return

        try:
            self.send_command("Browser.close")
        except (BrowserClosedError, BrowserFailedError):
            return
        except ChannelClosedError:
            pass

        self.channel.close()
        if self._is_closed():
            return

        # try kiling
        kill(self.subprocess)
        if self._is_closed(wait=4):
            return
        else:
            raise RuntimeError("Couldn't close or kill browser subprocess")

    def close(self):
        """Close the browser."""
        self.broker.clean()
        _logger.info("Broker cleaned up.")
        if not self._release_lock():
            return
        try:
            _logger.info("Trying to close browser.")
            self._close()
            _logger.info("browser._close() called successfully.")
        except ProcessLookupError:
            pass
        os.close(self.logger_pipe)
        _logger.info("Logging pipe closed.")
        self.channel.close()
        _logger.info("Browser channel closed.")
        self.browser_impl.clean()
        _logger.info("Browser implementation cleaned up.")

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Close the browser."""
        self.close()

    def _add_tab(self, tab):
        if not isinstance(tab, self.tab_type):
            raise TypeError("tab must be an object of (sub)class Tab")
        self.tabs[tab.target_id] = tab

    def _remove_tab(self, target_id):
        if isinstance(target_id, self.tab_type):
            target_id = target_id.target_id
        del self.tabs[target_id]

    def get_tab(self):
        """Get the first tab if there is one. Useful for default tabs."""
        if self.tabs.values():
            return next(iter(self.tabs.values()))
        return None

    # wrap our broker for convenience
    def start_output_thread(self, **kwargs):
        """Start a separate thread that dumps all messages received to stdout."""
        self.broker.run_output_thread(**kwargs)
