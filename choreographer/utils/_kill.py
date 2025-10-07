from __future__ import annotations

import platform
import subprocess

import logistro

_logger = logistro.getLogger(__name__)


def kill(process: subprocess.Popen[bytes] | subprocess.Popen[str]) -> None:
    if platform.system() == "Windows":
        subprocess.call(  # noqa: S603, false positive, input fine
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],  # noqa: S607 windows full path...
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    else:
        process.terminate()
        _logger.debug("Called terminate (a light kill).")
        if process.poll() is None:
            _logger.debug("Calling kill (a heavy kill).")
            process.kill()
