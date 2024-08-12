from .pipe import Pipe
import platform
import os
import sys
import subprocess
import signal


class Browser:
    def __init__(self, debug=None, path=None):
        self.pipe = Pipe()

        if not debug:  # false o None
            stderr = subprocess.DEVNULL
        elif debug is True:
            stderr = None
        else:
            stderr = debug

        if not path:
            if platform.system() == "Windows":
                path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            elif platform.system() == "Linux":
                path = "/usr/bin/google-chrome-stable"
            else:
                raise ValueError("You must set path to a chrome-like browser")

        new_env = os.environ.copy()
        new_env["CHROMIUM_PATH"] = path
        win_only = {}
        if platform.system() == "Windows":
            win_only = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}

        proc = subprocess.Popen(
            [
                sys.executable,
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), "chrome_wrapper.py"
                ),
            ],
            close_fds=True,
            stdin=self.pipe.read_to_chromium,
            stdout=self.pipe.write_from_chromium,
            stderr=stderr,
            env=new_env,
            **win_only,
        )
        self.subprocess = proc

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return self.close_browser()

    def close_browser(self):
        if platform.system() == "Windows":
            self.subprocess.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            self.subprocess.terminate()
        self.subprocess.wait(5)
        self.subprocess.kill()
