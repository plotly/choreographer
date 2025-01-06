import platform
import subprocess


def kill(process):
    if platform.system() == "Windows":
        subprocess.call(  # noqa: S603, false positive, input fine
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],  # noqa: S607 windows full path...
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    else:
        process.terminate()
        if process.poll() is None:
            process.kill()
