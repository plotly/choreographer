"""chromium.py provides a class proving tools for running chromium browsers."""

import os
import platform
import re
import subprocess
import sys
from pathlib import Path

import logistro

if platform.system() == "Windows":
    import msvcrt

from choreographer._channels import Pipe
from choreographer._sys_utils import TmpDirectory, get_browser_path

from ._chrome_constants import chrome_names, typical_chrome_paths

chromium_wrapper_path = (
    Path(__file__).resolve().parent / "_unix_pipe_chromium_wrapper.py"
)

logger = logistro.getLogger(__name__)


def _is_exe(path):
    try:
        return os.access(path, os.X_OK)
    except:  # noqa: E722 bare except ok, weird errors, best effort.
        return False


_logs_parser_regex = re.compile(r"\d*:\d*:\d*\/\d*\.\d*:")


class Chromium:
    """
    Chromium represents an implementation of the chromium browser.

    It also includes chromium-like browsers (chrome, edge, and brave).
    """

    @classmethod
    def logger_parser(cls, record, _old):
        """
        Parse (per logistro) and extract data from browser stderr for logging.

        Args:
            record: the `logging.LogRecord` object to read/modify
            _old: data that was already stripped out.

        """
        record.msg = _logs_parser_regex.sub("", record.msg)
        # we just eliminate their stamp, we dont' extract it
        return True

    def __init__(self, channel, path=None, **kwargs):
        """
        Construct a chromium browser implementation.

        Args:
            channel: the choreographer.Channel we'll be using (WebSockets? Pipe?)
            path: path to the browser
            kwargs:
                gpu_enabled (default False): Turn on GPU? Doesn't work in all envs.
                headless (default True): Actually launch a browser?
                sandbox_enabled (default False): Enable sandbox-
                    a persnickety thing depending on environment, OS, user, etc
                tmp_dir (default None): Manually set the temporary directory

        Raises:
            RuntimeError: Too many kwargs, or browser not found.
            NotImplementedError: Pipe is the only channel type it'll accept right now.

        """
        self.path = path
        self.gpu_enabled = kwargs.pop("enable_gpu", False)
        self.headless = kwargs.pop("headless", True)
        self.sandbox_enabled = kwargs.pop("enable_sandbox", False)
        self._tmp_dir_path = kwargs.pop("tmp_dir", None)
        if kwargs:
            raise RuntimeError(
                "Chromium.get_cli() received " f"invalid args: {kwargs.keys()}",
            )
        self.skip_local = bool(
            "ubuntu" in platform.version().lower() and self.enable_sandbox,
        )
        if self.skip_local:
            logger.warning("Ubuntu + Sandbox won't work unless chrome from snap")

        if not self.path:
            self.path = get_browser_path(
                executable_names=chrome_names,
                skip_local=self.skip_local,
            )
        if not self.path:
            # do typical chrome paths
            for candidate in typical_chrome_paths:
                if _is_exe(candidate):
                    self.path = candidate
                    break
        if not self.path:
            raise RuntimeError(
                "Browser not found. You can use get_chrome(), "
                "please see documentation.",
            )
        logger.debug(f"Found path: {self.path}")
        self._channel = channel
        if not isinstance(channel, Pipe):
            raise NotImplementedError("Websocket style channels not implemented yet.")

        self.tmp_dir = TmpDirectory(
            path=self._tmp_dir_path,
            sneak="snap" in str(self.path),
        )
        logger.info(f"Temporary directory at: {self.tmp_dir.name}")

    def get_popen_args(self):
        """Return the args needed to runc chromium with subprocess.Popen()."""
        args = {}
        # need to check pipe
        if platform.system() == "Windows":
            args["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            args["close_fds"] = False
        else:
            args["close_fds"] = True
            if isinstance(self._channel, Pipe):
                args["stdin"] = self._channel.from_choreo_to_external
                args["stdout"] = self._channel.from_external_to_choreo
        logger.debug(f"Returning args: {args}")
        return args

    def get_cli(self):
        """Return the CLI command for chromium."""
        if platform.system() != "Windows":
            cli = [
                sys.executable,
                chromium_wrapper_path,
                self.path,
            ]
        else:
            cli = [
                self.path,
            ]

        cli.extend(
            [
                "--disable-breakpad",
                "--allow-file-access-from-files",
                "--enable-logging=stderr",
                f"--user-data-dir={self.tmp_dir.path}",
                "--no-first-run",
                "--enable-unsafe-swiftshader",
            ],
        )
        if not self.gpu_enabled:
            cli.append("--disable-gpu")
        if self.headless:
            cli.append("--headless")
        if not self.sandbox_enabled:
            cli.append("--no-sandbox")

        if isinstance(self._channel, Pipe):
            cli.append("--remote-debugging-pipe")
            if platform.system() == "Windows":
                w_handle = msvcrt.get_osfhandle(self._channel.from_choreo_to_external)
                r_handle = msvcrt.get_osfhandle(self._channel.from_external_to_choreo)
                _inheritable = True
                os.set_handle_inheritable(w_handle, _inheritable)
                os.set_handle_inheritable(r_handle, _inheritable)
                cli += [
                    f"--remote-debugging-io-pipes={r_handle!s},{w_handle!s}",
                ]
        logger.debug(f"Returning cli: {cli}")
        return cli

    def get_env(self):
        """Return the env needed for chromium."""
        logger.debug("Returning env: same env, no modification.")
        return os.environ.copy()

    def clean(self):
        """Clean up any leftovers form browser, like tmp files."""
        self.tmp_dir.clean()

    def __del__(self):
        self.clean()
