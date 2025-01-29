from __future__ import annotations

import platform
import subprocess

import logistro

_logger = logistro.getLogger(__name__)


def kill(process: subprocess.Popen[bytes]) -> None:
    if platform.system() == "Windows":
        subprocess.call(  # noqa: S603, false positive, input fine
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],  # noqa: S607 windows full path...
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    else:
        process.terminate()
        _logger.info("Called terminate")
        if process.poll() is None:
            _logger.info("Calling kill")
            process.kill()
