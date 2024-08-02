import platform
import os
import sys
import subprocess

class Pipe():
    def __init__(self):
        self.read_from_chromium, self.write_from_chromium = list(os.pipe())
        self.read_to_chromium, self.write_to_chromium = list(os.pipe())
    def read(self, debug=False):
        raw_message = os.read(self.read_from_chromium, 10000)
        if debug:
            print(raw_message, file=sys.stderr)
        return bytes.decode(raw_message).replace('\0','')
    def write(self, msg):
        os.write(self.write_to_chromium, str.encode(msg+'\0'))

def raw_to_json():
#        decoder = json.JSONDecoder()
#        raw_message = pipe.read()
#        pos = 0
#        messages = []
#        while not pos == len(str(raw_message)):
#            msg, json_len = decoder.raw_decode(result[pos:])
#            pos += json_len
#            messages.append(msg)
#        return message

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
