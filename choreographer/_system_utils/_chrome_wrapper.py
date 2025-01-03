import os

# importing modules has side effects, so we do this before imports

# not everyone uses the wrapper as a process
if __name__ == "__main__":
    # chromium reads on 3, writes on 4
    os.dup2(0, 3)  # make our stdin their input
    os.dup2(1, 4)  # make our stdout their output

import asyncio
import platform
import signal
import subprocess
import sys
from functools import partial

_inheritable = True

system = platform.system()
if system == "Windows":
    import msvcrt
else:
    os.set_inheritable(4, _inheritable)
    os.set_inheritable(3, _inheritable)


def open_browser(  # noqa: PLR0913 too many args in func
    to_chromium,
    from_chromium,
    stderr=sys.stderr,
    env=None,
    loop=None,
    *,
    loop_hack=False,
):
    path = env.get("BROWSER_PATH")
    if not path:
        raise RuntimeError("No browser path was passed to run")

    user_data_dir = env["USER_DATA_DIR"]

    cli = [
        path,
        "--remote-debugging-pipe",
        "--disable-breakpad",
        "--allow-file-access-from-files",
        "--enable-logging=stderr",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--enable-unsafe-swiftshader",
    ]
    if not env.get("GPU_ENABLED", False):
        cli.append("--disable-gpu")
    if not env.get("SANDBOX_ENABLED", False):
        cli.append("--no-sandbox")

    if "HEADLESS" in env:
        cli.append("--headless")

    system_dependent = {}
    if system == "Windows":
        to_chromium_handle = msvcrt.get_osfhandle(to_chromium)
        os.set_handle_inheritable(to_chromium_handle, _inheritable)
        from_chromium_handle = msvcrt.get_osfhandle(from_chromium)
        os.set_handle_inheritable(from_chromium_handle, _inheritable)
        cli += [
            f"--remote-debugging-io-pipes={to_chromium_handle!s},{from_chromium_handle!s}",
        ]
        system_dependent["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        system_dependent["close_fds"] = False
    else:
        system_dependent["pass_fds"] = (to_chromium, from_chromium)

    if not loop:
        return subprocess.Popen(  # noqa: S603 input fine.
            cli,
            stderr=stderr,
            **system_dependent,
        )
    elif loop_hack:

        def run():
            return subprocess.Popen(  # noqa: S603 input fine.
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
            **system_dependent,
        )


def kill_proc(process, _sig_num, _frame):
    process.terminate()
    process.wait(5)  # 5 seconds to clean up nicely, it's a lot
    process.kill()


if __name__ == "__main__":
    process = open_browser(to_chromium=3, from_chromium=4, env=os.environ)
    kp = partial(kill_proc, process)
    signal.signal(signal.SIGTERM, kp)
    signal.signal(signal.SIGINT, kp)

    process.wait()

    # not great but it seems that
    # pipe isn't always closed when chrome closes
    # so we pretend to be chrome and send a bye instead
    # also, above depends on async/sync, platform, etc
    print("{bye}")
