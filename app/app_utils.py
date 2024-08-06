import platform
import os
import sys
import subprocess
import json

class PipeClosedError(IOError):
    pass

class Pipe():
    def __init__(self):
        self.read_from_chromium, self.write_from_chromium = list(os.pipe())
        self.read_to_chromium, self.write_to_chromium = list(os.pipe())

    def write(self, msg):
        os.write(self.write_to_chromium, str.encode(msg+'\0'))

    def read_jsons(self, blocking=True):
        jsons = []
        os.set_blocking(self.read_from_chromium, blocking)
        try:
            raw_buffer = os.read(self.read_from_chromium, 10000) # 10MB buffer, nbd, doesn't matter w/ this
            if not raw_buffer:
                raise PipeClosedError()
            while raw_buffer[-1] != 0:
                os.set_blocking(self.read_from_chromium, True)
                raw_buffer += os.read(self.read_from_chromium, 10000)
        except BlockingIOError:
            return jsons
        for raw_message in raw_buffer.decode('utf-8').split('\0'):
            if raw_message:
                jsons.append(json.loads(raw_message))
        return jsons

def start_browser(path=None):
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
    proc = subprocess.Popen(
            [sys.executable, os.path.join(os.path.dirname(os.path.realpath(__file__)), "chrome_wrapper.py")],
            close_fds=True,
            stdin=pipe.read_to_chromium,
            stdout=pipe.write_from_chromium,
            stderr=None,
            env=new_env,
            text=True,
            bufsize=1,
            )
    os.close(pipe.read_to_chromium)
    os.close(pipe.write_from_chromium)
    return (proc, pipe)
