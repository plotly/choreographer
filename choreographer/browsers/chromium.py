"""Provides a class proving tools for running chromium browsers."""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import logistro

if platform.system() == "Windows":
    import msvcrt

from choreographer.channels import Pipe
from choreographer.utils import TmpDirectory, get_browser_path

from ._chrome_constants import chrome_names, typical_chrome_paths

if TYPE_CHECKING:
    import logging
    from collections.abc import Mapping, MutableMapping, Sequence
    from typing import Any

    from choreographer.channels._interface_type import ChannelInterface

_chromium_wrapper_path = (
    Path(__file__).resolve().parent / "_unix_pipe_chromium_wrapper.py"
)

_logger = logistro.getLogger(__name__)


def _is_exe(path: str | Path) -> bool:
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

    path: str | Path | None
    """The path to the chromium executable."""
    gpu_enabled: bool
    """True if we should use the gpu. False by default for compatibility."""
    headless: bool
    """True if we should not show the browser, true by default."""
    sandbox_enabled: bool
    """True to enable the sandbox. False by default."""
    skip_local: bool
    """True if we want to avoid looking for our local download when searching path."""
    tmp_dir: TmpDirectory
    """A reference to a temporary directory object the chromium needs to store data."""

    @classmethod
    def logger_parser(
        cls,
        record: logging.LogRecord,
        _old: MutableMapping[str, Any],
    ) -> bool:
        """
        Parse (via `logging.Filter.parse()`) data from browser stderr for logging.

        Args:
            record: the `logging.LogRecord` object to read/modify
            _old: data that was already stripped out.

        """
        record.msg = _logs_parser_regex.sub("", record.msg)
        # we just eliminate their stamp, we dont' extract it
        return True

    def __init__(
        self,
        channel: ChannelInterface,
        path: Path | str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Construct a chromium browser implementation.

        Args:
            channel: the `choreographer.Channel` we'll be using (WebSockets? Pipe?)
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
        _logger.info(f"Chromium init'ed with kwargs {kwargs}")
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
            "ubuntu" in platform.version().lower() and self.sandbox_enabled,
        )
        if self.skip_local:
            _logger.warning("Ubuntu + Sandbox won't work unless chrome from snap")

        if not self.path:
            self.path = get_browser_path(
                executable_names=chrome_names,
                skip_local=self.skip_local,
            )
        if not self.path and typical_chrome_paths:
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
        _logger.debug(f"Found path: {self.path}")
        self._channel = channel
        if not isinstance(channel, Pipe):
            raise NotImplementedError("Websocket style channels not implemented yet.")

        self.tmp_dir = TmpDirectory(
            path=self._tmp_dir_path,
            sneak="snap" in str(self.path),
        )
        _logger.info(f"Temporary directory at: {self.tmp_dir.path}")

    def get_popen_args(self) -> Mapping[str, Any]:
        """Return the args needed to runc chromium with `subprocess.Popen()`."""
        args = {}
        # need to check pipe
        if platform.system() == "Windows":
            args["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore [attr-defined]
            args["close_fds"] = False
        else:
            args["close_fds"] = True
            if isinstance(self._channel, Pipe):
                args["stdin"] = self._channel.from_choreo_to_external
                args["stdout"] = self._channel.from_external_to_choreo
        _logger.debug(f"Returning args: {args}")
        return args

    def get_cli(self) -> Sequence[str]:
        """Return the CLI command for chromium."""
        if platform.system() != "Windows":
            cli = [
                str(sys.executable),
                str(_chromium_wrapper_path),
                str(self.path),
            ]
        else:
            cli = [
                str(self.path),
            ]

        if not self.gpu_enabled:
            cli.append("--disable-gpu")
        if self.headless:
            cli.append("--headless")
        if not self.sandbox_enabled:
            cli.append("--no-sandbox")

        cli.extend(
            [
                "--disable-breakpad",
                "--allow-file-access-from-files",
                "--enable-logging=stderr",
                f"--user-data-dir={self.tmp_dir.path}",
                "--no-first-run",
                "--enable-unsafe-swiftshader",
                "--disable-dev-shm-usage",
                "--disable-background-media-suspend",
                "--disable-lazy-loading",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-component-update",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-hang-monitor",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
                "--disable-ipc-flooding-protection",
                "--disable-sync",
                "--metrics-recording-only",
                "--password-store=basic",
                "--use-mock-keychain",
                "--disable-domain-reliability",
                "--disable-print-preview",
                "--disable-speech-api",
                "--no-default-browser-check",
                "--no-pings",
                "--no-process-per-site",
                "--process-per-tab",
                "--disable-features=Translate,BackForwardCache,AcceptCHFrame,MediaRouter,OptimizationHints,AudioServiceOutOfProcess,IsolateOrigins,CalculateNativeWinOcclusion,site-per-process,IntensiveWakeUpThrottling,AllowAggressiveThrottlingWithWebSocket,OptOutZeroTimeoutTimersFromThrottling",
                "--disable-web-security",
            ],
        )
        if isinstance(self._channel, Pipe):
            cli.append("--remote-debugging-pipe")
            if platform.system() == "Windows":
                # its gonna read on 3
                # its gonna write on 4
                r_handle = msvcrt.get_osfhandle(self._channel.from_choreo_to_external)  # type: ignore [attr-defined]
                w_handle = msvcrt.get_osfhandle(self._channel.from_external_to_choreo)  # type: ignore [attr-defined]
                _inheritable = True
                os.set_handle_inheritable(r_handle, _inheritable)  # type: ignore [attr-defined]
                os.set_handle_inheritable(w_handle, _inheritable)  # type: ignore [attr-defined]
                cli += [
                    f"--remote-debugging-io-pipes={r_handle!s},{w_handle!s}",
                ]
        _logger.debug(f"Returning cli: {cli}")
        return cli

    def get_env(self) -> MutableMapping[str, str]:
        """Return the env needed for chromium."""
        _logger.debug("Returning env: same env, no modification.")
        return os.environ.copy()

    def clean(self) -> None:
        """Clean up any leftovers form browser, like tmp files."""
        self.tmp_dir.clean()

    def __del__(self) -> None:
        """Delete the temporary file and run `clean()`."""
        self.clean()
