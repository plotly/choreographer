import subprocess

import logistro

from ._brokers import BrokerSync
from ._browsers import BrowserClosedError, BrowserFailedError, Chromium
from ._channels import ChannelClosedError, Pipe
from ._sys_utils import kill

logger = logistro.getLogger(__name__)


class SessionSync:
    def __init__(self, browser, session_id):
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a string")
        # Resources
        self.browser = browser

        # State
        self.session_id = session_id
        self.message_id = 0

    def send_command(self, command, params=None):
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

        return self.browser.broker.send_json(json_command)


class TargetSync:
    _session_type = SessionSync

    def __init__(self, target_id, browser):
        if not isinstance(target_id, str):
            raise TypeError("target_id must be string")
        # Resources
        self.browser = browser

        # States
        self.sessions = {}
        self.target_id = target_id

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
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        return self._get_first_session().send_command(command, params)


class TabSync(TargetSync):
    def __init__(self, target_id, browser):
        super().__init__(target_id, browser)


class BrowserSync(TargetSync):
    """`BrowserSync` is the sync implementation of `Browser`."""

    _tab_type = TabSync
    _session_type = SessionSync
    _target_type = TargetSync

    def __init__(self, path=None, *, browser_cls=Chromium, channel_cls=Pipe, **kwargs):
        self.tabs = {}
        # Compose Resources
        self.channel = channel_cls()
        self.broker = BrokerSync(self, self.channel)
        self.browser_impl = browser_cls(self.channel, path, **kwargs)

        # we do need something to indicate we're open TODO yeah an open lock

    def open(self):
        self.subprocess = subprocess.Popen(  # noqa: S603
            self.browser_impl.get_cli(),
            # stderr= TODO make a pipe with logistro
            env=self.browser_impl.get_env(),
            **self.browser_impl.get_popen_args(),
        )
        super(TargetSync, self).__init__("0", self)
        self._add_session(SessionSync(self, ""))
        # start a watchdock
        # open can only be run once?
        # or depends on lock

    def __enter__(self):
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
        try:
            self._close()
        except ProcessLookupError:
            pass
        self.channel.close()
        self.browser_impl.clean()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    # wrap our broker for convenience
    def start_output_thread(self, **kwargs):
        self.broker.run_output_thread(**kwargs)

    def _add_tab(self, tab):
        if not isinstance(tab, self.tab_type):
            raise TypeError("tab must be an object of (sub)class Tab")
        self.tabs[tab.target_id] = tab

    def _remove_tab(self, target_id):
        if isinstance(target_id, self.tab_type):
            target_id = target_id.target_id
        del self.tabs[target_id]

    def get_tab(self):
        if self.tabs.values():
            return next(iter(self.tabs.values()))
        return None
