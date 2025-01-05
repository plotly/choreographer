"""chromium.py provides a class proving tools for running chromium browsers."""

import os
import platform
import sys
from pathlib import Path

# TODO(Andrew): move this to its own subpackage comm # noqa: FIX002, TD003
from choreographer._pipe import Pipe, WebSocket

if platform.system() == "Windows":
    import msvcrt


class Chromium:
    def __init__(self, pipe):
        self._comm = pipe
        # extra information from pipe

    # where do we get user data dir
    def get_cli(self, temp_dir, **kwargs):
        gpu_enabled = kwargs.pop("with_gpu", False)
        headless = kwargs.pop("headless", True)
        sandbox = kwargs.pop("with_sandbox", False)
        if kwargs:
            raise RuntimeError(
                "Chromium.get_cli() received " f"invalid args: {kwargs.keys()}",
            )
        path = None  # TODO(Andrew): not legit # noqa: FIX002,TD003
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

        if isinstance(self._comm, Pipe):
            cli.append("--remote-debugging-pipe")
            if platform.system() == "Windows":
                _inheritable = True
                write_handle = msvcrt.get_osfhandle(self._comm.from_choreo_to_external)
                read_handle = msvcrt.get_osfhandle(self._comm.from_external_to_choreo)
                os.set_handle_inheritable(write_handle, _inheritable)
                os.set_handle_inheritable(read_handle, _inheritable)
                cli += [
                    f"--remote-debugging-io-pipes={read_handle!s},{write_handle!s}",
                ]
        elif isinstance(self._comm, WebSocket):
            raise NotImplementedError("Websocket style comms are not implemented yet")


def get_env():
    return os.environ().copy()
