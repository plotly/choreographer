import os

# importing modules has side effects, so we do this before imports
# linter complains.
env = None


# chromium reads on 3, writes on 4
# really this means windows only, but a more readable platform.system()
if __name__ == "__main__":
    os.dup2(0, 3)  # make our stdin their input
    os.dup2(1, 4)  # make our stdout their output


import subprocess  # noqa
import signal  # noqa
import platform  # noqa
import asyncio #noqa
import sys #noqa

system = platform.system()
if system == "Windows":
    import msvcrt  # noqa
else:
    os.set_inheritable(4, True)
    os.set_inheritable(3, True)

def open_browser(to_chromium, from_chromium, stderr=sys.stderr, env=None, loop=None, loop_hack=False):
    path = env.get("BROWSER_PATH")
    if not path:
        raise RuntimeError("No browser path was passed to run")
    # TODO: check that browser exists (windows, mac) w/ --version (TODO: how to do on wndows?)

    user_data_dir = env["USER_DATA_DIR"]

    cli = [
        path,
        "--remote-debugging-pipe",
        "--disable-breakpad",
        "--allow-file-access-from-files",
        "--enable-logging=stderr",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--enable-unsafe-swiftshader"
    ]
    if not env.get("GPU_ENABLED", False):
        cli.append("--disable-gpu")
    if not env.get("SANDBOX_ENABLED", False):
        cli.append("--no-sandbox")

    if "HEADLESS" in env:
        cli.append("--headless=old") # temporary fix

    system_dependent = {}
    if system == "Windows":
        to_chromium_handle = msvcrt.get_osfhandle(to_chromium)
        os.set_handle_inheritable(to_chromium_handle, True)
        from_chromium_handle = msvcrt.get_osfhandle(from_chromium)
        os.set_handle_inheritable(from_chromium_handle, True)
        cli += [
            f"--remote-debugging-io-pipes={str(to_chromium_handle)},{str(from_chromium_handle)}"
        ]
        system_dependent["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        system_dependent["close_fds"] = False
    else:
        system_dependent["pass_fds"]=(to_chromium, from_chromium)

    if not loop:
        return subprocess.Popen(
            cli,
            stderr=stderr,
            **system_dependent,
        )
    elif loop_hack:
        def run():
            return subprocess.Popen(
                cli,
                stderr=stderr,
                **system_dependent,
            )
        return asyncio.to_thread(run)
    else:
        return asyncio.create_subprocess_exec(
                cli[0],
                *cli[1:],
                stderr=stderr,
                **system_dependent)


# THIS MAY BE PART OF KILL
def kill_proc(*nope):
    global process
    process.terminate()
    process.wait(3)  # 3 seconds to clean up nicely, it's a lot
    process.kill()

if __name__ == "__main__":
    process = open_browser(to_chromium=3, from_chromium=4, env=os.environ)
    signal.signal(signal.SIGTERM, kill_proc)
    signal.signal(signal.SIGINT, kill_proc)

    process.wait()
    # NOTE is bad but we don't detect closed pipe (stdout doesn't close from other end?)
    # doesn't seem to impact in sync, maybe because we're doing manual cleanup in sequence
    # should try to see if shutting down chrome browser can provoke pipeerror in threadmode and asyncmode
    # i think getting rid of this would be really good, and seeing what's going on in both
    # async and sync mode would help
    # see NOTE in pipe.py (line 38?)
    print("{bye}")
