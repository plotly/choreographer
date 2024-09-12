import os

# importing modules has side effects, so we do this before imports
# chromium reads on 3, writes on 4
# linter complains.
os.dup2(0, 3)  # make our stdin their input
os.dup2(1, 4)  # make our stdout their output
os.set_inheritable(4, True)
os.set_inheritable(3, True)

import subprocess  # noqa
import signal  # noqa
import platform  # noqa
import sys # noqa

system = platform.system()
if system == "Windows":
    import msvcrt  # noqa

default_path = None
if system == "Windows":
    default_path = r"c:\Program Files\Google\Chrome\Application\chrome.exe"
elif system == "Linux":
    default_path = "/usr/bin/google-chrome-stable"
else:
    pass

path = os.environ.get("BROWSER_PATH", default_path)

if path is None:
    raise ValueError("You must specify a path with environmental variable BROWSER_PATH")

print(f"Sent path: {path}", file=sys.stderr)

user_data_dir = os.environ["USER_DATA_DIR"]

cli = [
    path,
    "--remote-debugging-pipe",
    "--disable-breakpad",
    "--allow-file-access-from-files",
    "--enable-logging=stderr",
    f"--user-data-dir={user_data_dir}",
    "--no-first-run",
]

if "HEADLESS" in os.environ:
    cli.append("--headless")

if system == "Windows":
    to_chromium_handle = msvcrt.get_osfhandle(3)
    os.set_handle_inheritable(to_chromium_handle, True)
    from_chromium_handle = msvcrt.get_osfhandle(4)
    os.set_handle_inheritable(from_chromium_handle, True)
    cli += [
        f"--remote-debugging-io-pipes={str(to_chromium_handle)},{str(from_chromium_handle)}"
    ]

process = subprocess.Popen(
    cli, close_fds=False, stdout=None, stderr=None, text=True, bufsize=1
)


def kill_proc(*nope):
    global process
    process.terminate()
    process.wait(3)  # 3 seconds to clean up nicely, it's a lot
    process.kill()


signal.signal(signal.SIGTERM, kill_proc)
signal.signal(signal.SIGINT, kill_proc)

if system == "Windows":
    process.wait()
else:
    signal.pause()

# NOTE is bad but we don't detect closed pipe (stdout doesn't close from other end?)
# doesn't seem to impact in sync, maybe because we're doing manual cleanup in sequence
# should try to see if shutting down chrome browser can provoke pipeerror in threadmode and asyncmode
# i think getting rid of this would be really good, and seeing what's going on in both
# async and sync mode would help
# see NOTE in pipe.py (line 38?)
print("{bye}")
