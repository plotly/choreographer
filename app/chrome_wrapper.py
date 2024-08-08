import os

# importing modules has side effects, so we do this before imports
# chromium reads on 3, writes on 4
# linter complains.
os.dup2(0, 3) # make our stdin their input
os.dup2(1, 4) # make our stdout their output
os.set_inheritable(4, True)
os.set_inheritable(3, True)

import subprocess # noqa
import signal # noqa
import platform # noqa
system = platform.system()
if system == "Windows": import msvcrt # noqa

path=""
if system == "Linux":
    path = os.environ.get("BROWSER_PATH", "/usr/bin/google-chrome-stable")
elif system == "Windows":
    path = os.environ.get("BROWSER_PATH", r"c:\Program Files\Google\Chrome\Application\chrome.exe")
else:
    path = os.environ['CHROMIUM_PATH']

cli = [path,
            "--headless",
            "--remote-debugging-pipe",
            "--disable-breakpad",
            "--allow-file-access-from-files"]

if system == "Windows":
    to_chromium_handle = msvcrt.get_osfhandle(3)
    os.set_handle_inheritable(to_chromium_handle, True)
    from_chromium_handle = msvcrt.get_osfhandle(4)
    os.set_handle_inheritable(from_chromium_handle, True)
    cli += [f"--remote-debugging-io-pipes={str(to_chromium_handle)},{str(from_chromium_handle)}"]

process = subprocess.Popen(
        cli,
        close_fds=False,
        stdout=None,
        stderr=None,
        text=True,
        bufsize=1
        )


def kill_proc(*nope):
    global process
    process.terminate()
    process.wait(3) # 3 seconds to clean up nicely, it's a lot
    process.kill()

signal.signal(signal.SIGTERM, kill_proc)
signal.signal(signal.SIGINT, kill_proc)

process.wait() # signal pause maybe, not sure

print("Wrapper closing")
