from app.app_utils import Pipe
from collections import OrderedDict
import platform
import os
import sys
import subprocess
import signal

class Browser:
    def __init__(self):
        self.pipes = OrderedDict()
        self.subprocess = OrderedDict()

    def start_browser(self, path=None):
        pipe = Pipe()
        if not path:
            if platform.system() == "Windows":
                path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            elif platform.system() == "Linux":
                path = "/usr/bin/google-chrome-stable"
            else:
                raise ValueError("You must set path to a chrome-like browser")
        new_env = os.environ.copy()
        new_env['CHROMIUM_PATH']=path
        win_only = {}
        if platform.system() == "Windows":
            win_only = {"creationflags":subprocess.CREATE_NEW_PROCESS_GROUP}
        proc = subprocess.Popen(
                [sys.executable, os.path.join(os.path.dirname(os.path.realpath(__file__)), "chrome_wrapper.py")],
                close_fds=True,
                stdin=pipe.read_to_chromium,
                stdout=pipe.write_from_chromium,
                stderr=None,
                env=new_env,
                **win_only
                )
        self.pipes[id(pipe)] = pipe
        self.subprocess[id(proc)] = proc
        
        return (proc, pipe)

    def close_browser(self):
        proc, _ = self.start_browser()

        if platform.system() == "Windows":
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            proc.terminate()
        proc.wait(5)
        proc.kill()