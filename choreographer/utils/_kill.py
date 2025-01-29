from __future__ import annotations

import platform
import subprocess


def kill(process: subprocess.Popen[bytes]) -> None:
    if platform.system() == "Windows":
        subprocess.call(  # noqa: S603, false positive, input fine
            ["taskkill", "/IM", "/F", "/T", "/PID", str(process.pid)],  # noqa: S607 windows full path...
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    else:
        process.terminate()
        if process.poll() is None:
            process.kill()
