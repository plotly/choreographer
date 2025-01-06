import subprocess

import logistro

from ._brokers import BrokerSync
from ._browser_base import BrowserBase
from ._browsers import BrowserClosedError, BrowserFailedError, Chromium
from ._channels import ChannelClosedError, Pipe
from ._sys_utils import kill
from .protocol._target import Session, Target

logger = logistro.getLogger(__name__)

# TODO: protocol a commin'


class BrowserSync(BrowserBase, Target):
    """`BrowserSync` is the sync implementation of `Browser`."""

    def __init__(self, path=None, *, browser_cls=Chromium, channel_cls=Pipe, **kwargs):
        self.tabs = {}
        # Compose Resources
        self.channel = channel_cls()
        self.broker = BrokerSync(self, self.channel)
        self.browser_impl = browser_cls(self.channel, path, **kwargs)

        # Explicit supers are better IMO
        super(BrowserBase, self).__init__()
        # we don't init ourselves as a target until we open?

    def open(self):
        self.subprocess = subprocess.Popen(  # noqa: S603
            self.browser_impl.get_cli(),
            # stderr= TODO make a pipe with logistro
            env=self.browser_impl.get_env(),
            **self.browser_impl.get_popen_args(),
        )
        super(Target, self).__init__("0", self)
        self._add_session(Session(self, ""))
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
