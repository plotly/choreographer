from .pipe import Pipe
from .protocol import Protocol
import platform
import os
import sys
import subprocess
import tempfile

from .system import which_browser

default_path = which_browser()


class Browser:
    def __init__(self, debug=None, path=default_path, headless=True):
        self.pipe = Pipe()
        if path is None:
            raise ValueError("You must specify a path")

        if platform.system() != "Windows":
            self.temp_dir = tempfile.TemporaryDirectory()
        else:
            self.temp_dir = tempfile.TemporaryDirectory(
                delete=False, ignore_cleanup_errors=True
            )

        if not debug:  # false o None
            stderr = subprocess.DEVNULL
        elif debug is True:
            stderr = None
        else:
            stderr = debug

        new_env = os.environ.copy()
        new_env["CHROMIUM_PATH"] = str(path)
        new_env["USER_DATA_DIR"] = str(self.temp_dir.name)
        if headless:
            new_env["HEADLESS"] = "--headless"

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
        self.protocol = Protocol(self.pipe)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close_browser()

    def create_tab(self, debug=False):
        self.protocol.create_tab(debug)

    def list_tabs(self):
        self.protocol.list_tabs()

    def close_tab(self, tab_id):
        self.protocol.close_tab(tab_id)

    def close_browser(self):
        if platform.system() == "Windows":
            # maybe we don't need chrome_wrapper for windows because of how handles are needed
            # if we're not chaining process, this might not be necessary
            # otherwise, win behaves strangely in the face of signals, so call a command to kill the process instead
            # NB: chrome accepts being killed like this because it knows windows is a nightmare
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", str(self.subprocess.pid)]
            )  # this output should be handled better by where there is debug
            self.subprocess.wait(2)
        self.subprocess.terminate()
        self.subprocess.wait(2)
        self.subprocess.kill()
        self.temp_dir.cleanup()
        # windows doesn't like python's default cleanup
        if platform.system() == "Windows":
            import stat
            import shutil

            def remove_readonly(func, path, excinfo):
                os.chmod(path, stat.S_IWUSR)
                func(path)

            shutil.rmtree(self.temp_dir.name, onexc=remove_readonly)
            del self.temp_dir

    def send_command(self, command, params=None, cb=None, session_id=None, debug=debug):
        return self.protocol.send_command(self, command, params, cb, session_id, debug)
