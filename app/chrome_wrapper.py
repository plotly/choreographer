import os

# importing modules has side effects, so we do this before imports
# chromium outs on 4, reads on 3
os.dup2(0, 3) # make our stdin their stdin
os.dup2(1, 4) # make our stdout their stdout
os.set_inheritable(4, True)
os.set_inheritable(3, True)

import subprocess # noqa
import signal # noqa
import platform # noqa

path = os.environ['CHROMIUM_PATH']
process = subprocess.Popen(
            [path,
                "--headless",
                "--remote-debugging-pipe",
                "--disable-breakpad",
                "--allow-file-access-from-files"],
            close_fds=False,
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

if platform.system() == "Windows":
    os.system('pause')
else:
    signal.pause()

print("Wrapper closing")
