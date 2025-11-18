from __future__ import annotations

import os
import platform
import subprocess

import logistro

if (_system := platform.system()) != "Windows":
    import signal

_logger = logistro.getLogger(__name__)


def kill(process: subprocess.Popen[bytes] | subprocess.Popen[str]) -> None:
    if _system == "Windows":
        subprocess.call(  # noqa: S603, false positive, input fine
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],  # noqa: S607 windows full path...
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            timeout=6,
        )
        return

    try:
        os.killpg(
            process.pid,
            signal.SIGTERM,  # type: ignore[reportPossiblyUnboundVariable]
        )
    except ProcessLookupError:
        process.terminate()
    _logger.debug("Called terminate (a light kill).")
    try:
        process.wait(timeout=6)
    except subprocess.TimeoutExpired:
        _logger.debug("Calling kill (a heavy kill).")
        try:
            os.killpg(
                process.pid,
                signal.SIGKILL,  # type: ignore[reportPossiblyUnboundVariable]
            )
        except ProcessLookupError:
            process.kill()
