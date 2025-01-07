"""Provides the sync api: `BrowserSync`, `TabSync`, `TargetSync` and `SessionSync`."""

import os
import subprocess
from threading import Lock

import logistro

from ._brokers import BrokerSync
from ._browsers import BrowserClosedError, BrowserFailedError, Chromium
from ._channels import ChannelClosedError, Pipe
from ._sys_utils import kill

logger = logistro.getLogger(__name__)


class SessionSync:
    """A session is a single conversation with a single target."""

    def __init__(self, browser, session_id):
        """
        Construct a session from the browser as an object.

        A session is like an open conversation with a target.
        All commands are sent on sessions.

        Args:
            browser:  a reference to the main browser
            session_id:  the id given by the browser

        """
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a string")
        # Resources
        self.browser = browser

        # State
        self.session_id = session_id
        logger.debug(f"New session: {session_id}")
        self.message_id = 0

    def send_command(self, command, params=None):
        """
        Send a devtools command on the session.

        https://chromedevtools.github.io/devtools-protocol/

        Args:
            command: devtools command to send
            params: the parameters to send

        """
        current_id = self.message_id
        self.message_id += 1
        json_command = {
            "id": current_id,
            "method": command,
        }

        if self.session_id:
            json_command["sessionId"] = self.session_id
        if params:
            json_command["params"] = params
        logger.debug(
            f"Sending {command} with {params} on session {self.session_id}",
        )
        return self.browser.broker.send_json(json_command)


class TargetSync:
    """A target like a browser, tab, or others. It sends commands. It has sessions."""

    _session_type = SessionSync
    """Like generic typing<>. This is the session type associated with TargetSync."""

    def __init__(self, target_id, browser):
        """Create a target after one ahs been created by the browser."""
        if not isinstance(target_id, str):
            raise TypeError("target_id must be string")
        # Resources
        self.browser = browser

        # States
        self.sessions = {}
        self.target_id = target_id
        logger.info(f"Created new target {target_id}.")

    def _add_session(self, session):
        if not isinstance(session, self._session_type):
            raise TypeError("session must be a session type class")
        self.sessions[session.session_id] = session
        self.browser.all_sessions[session.session_id] = session

    def _remove_session(self, session_id):
        if isinstance(session_id, self._session_type):
            session_id = session_id.session_id
        _ = self.sessions.pop(session_id, None)
        _ = self.browser.all_sessions.pop(session_id, None)

    def _get_first_session(self):
        if not self.sessions.values():
            raise RuntimeError(
                "Cannot use this method without at least one valid session",
            )
        return next(iter(self.sessions.values()))

    def send_command(self, command, params=None):
        """
        Send a command to the first session in a target.

        https://chromedevtools.github.io/devtools-protocol/

        Args:
            command: devtools command to send
            params: the parameters to send

        """
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        session = self._get_first_session()
        logger.debug(
            f"Sending {command} with {params} on session {session.session_id}",
        )
        return session.send_command(command, params)


class TabSync(TargetSync):
    """A wrapper for TargetSync, so user can use TabSync, not TargetSync."""


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
        logger.debug("Attempting to open new browser.")
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
        logger.info("Broker cleaned up.")
        if not self._release_lock():
            return
        try:
            logger.info("Trying to close browser.")
            self._close()
            logger.info("browser._close() called successfully.")
        except ProcessLookupError:
            pass
        os.close(self.logger_pipe)
        logger.info("Logging pipe closed.")
        self.channel.close()
        logger.info("Browser channel closed.")
        self.browser_impl.clean()
        logger.info("Browser implementation cleaned up.")

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
