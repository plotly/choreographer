"""chromium.py provides a class proving tools for running chromium browsers."""

import os
import platform
import sys
from pathlib import Path

if platform.system() == "Windows":
    import msvcrt

from choreographer._channels import Pipe
from choreographer._sys_utils import get_browser_path


class Chromium:
    def __init__(self, channel):
        self._channel = channel
        if not isinstance(channel, Pipe):
            raise NotImplementedError("Websocket style channels not implemented yet")

    # where do we get user data dir
    def get_cli(self, temp_dir, **kwargs):
        gpu_enabled = kwargs.pop("with_gpu", False)
        headless = kwargs.pop("headless", True)
        sandbox = kwargs.pop("with_sandbox", False)
        if kwargs:
            raise RuntimeError(
                "Chromium.get_cli() received " f"invalid args: {kwargs.keys()}",
            )
        path = get_browser_path()
        if not path:
            raise RuntimeError("Browser not found.")

        chromium_wrapper_path = Path(__file__).resolve().parent / "chromium_wrapper.py"
        if platform.system() != "Windows":
            cli = [
                sys.executable,
                chromium_wrapper_path,
                path,
            ]
        else:
            cli = [
                path,
            ]

        cli.extend(
            [
                "--disable-breakpad",
                "--allow-file-access-from-files",
                "--enable-logging=stderr",
                f"--user-data-dir={temp_dir}",
                "--no-first-run",
                "--enable-unsafe-swiftshader",
            ],
        )
        if not gpu_enabled:
            cli.append("--disable-gpu")
        if headless:
            cli.append("--headless")
        if not sandbox:
            cli.append("--no-sandbox")

        if isinstance(self._channel, Pipe):
            cli.append("--remote-debugging-pipe")
            if platform.system() == "Windows":
                _inheritable = True
                w_handle = msvcrt.get_osfhandle(self._channel.from_choreo_to_external)
                r_handle = msvcrt.get_osfhandle(self._channel.from_external_to_choreo)
                os.set_handle_inheritable(w_handle, _inheritable)
                os.set_handle_inheritable(r_handle, _inheritable)
                cli += [
                    f"--remote-debugging-io-pipes={r_handle!s},{w_handle!s}",
                ]


def get_env():
    return os.environ().copy()
