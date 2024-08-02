import platform
import os
import subprocess

def start_browser(path=None):
    if not path:
        if platform.system() == "Windows":
            path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        elif platform.system() == "Linux":
            path = "/usr/bin/google-chrome-stable"
        else:
            raise ValueError("You must set path to a chrome-like browser")

    #t chromium is going to output on 4
    # we will read on result_stream to get chromium's output
    from_chromium = list(os.pipe())
    to_chromium = list(os.pipe())

    print(f"from_chromium read: {from_chromium[0]} write: {from_chromium[1]}")
    print(f"to_chromium read: {to_chromium[0]} write: {to_chromium[1]}")


    if (from_chromium[1] != 4):
        print("from_chromium write is not 4")
        if (from_chromium[0] == 4):
            print("from_chromium[0] is!")
            temp = from_chromium[0]
            from_chromium[0] = os.dup(from_chromium[0])
            os.close(temp)
            print(f"from_chromium[0] is now {from_chromium}!")
        if (to_chromium[0] == 4):
            print("to_chromium[0] is!")
            temp = to_chromium[0]
            to_chromium[0] = os.dup(to_chromium[0])
            os.close(temp)
            print(f"to_chromium[0] is now {to_chromium}!")
        if (to_chromium[1] == 4):
            print("to_chromium[1] is!")
            temp = to_chromium[1]
            to_chromium[1] = os.dup(to_chromium[1])
            os.close(temp)
            print(f"to_chromium[1] is now {to_chromium}!")

        os.dup2(from_chromium[1], 4)
        os.close(from_chromium[1])
        from_chromium[1] = 4
        print("Finished the swap")

    if (to_chromium[0] != 3):
        print("to_chromium read is not 3")
        if (to_chromium[1] == 3):
            print("to_chromium[1] is!")
            temp = to_chromium[1]
            to_chromium[1] = os.dup(to_chromium[1])
            os.close(temp)
            print(f"to_chromium[1] is now {to_chromium}!")
        if (from_chromium[0] == 3):
            print("from_chromium[0] is!")
            temp = from_chromium[0]
            from_chromium[0] = os.dup(from_chromium[0])
            os.close(temp)
            print(f"from_chromium[0] is now {from_chromium}!")
        if (from_chromium[1] == 3):
            print("from_chromium[1] is!")
            temp = from_chromium[1]
            from_chromium[1] = os.dup(from_chromium[1])
            os.close(temp)
            print(f"from_chromium[1] is now {from_chromium}!")

        os.dup2(to_chromium[0], 3)
        os.close(to_chromium[0])
        to_chromium[0] = 3
        print("Finished the swap")

    print(f"from_chromium read: {from_chromium[0]} write: {from_chromium[1]}")
    print(f"to_chromium read: {to_chromium[0]} write: {to_chromium[1]}")
    os.set_inheritable(to_chromium[0], True)
    os.set_inheritable(to_chromium[1], True)
    os.set_inheritable(from_chromium[0], True)
    os.set_inheritable(from_chromium[1], True)

    stderr_pipe = list(os.pipe())
    os.set_inheritable(stderr_pipe[0], True)
    os.set_inheritable(stderr_pipe[1], True)
    proc = subprocess.Popen(
            [path,
                "--headless",
                "--remote-debugging-pipe",
                "--disable-breakpad",
                "--allow-file-access-from-files"],
            close_fds=False,
            stdout=stderr_pipe[1],
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
            )
    # chromium is going to output on 4
    # we will read on result_stream to get chromium's output
    from_chromium = list(os.pipe())
    to_chromium = list(os.pipe())

    print(f"from_chromium read: {from_chromium[0]} write: {from_chromium[1]}")
    print(f"to_chromium read: {to_chromium[0]} write: {to_chromium[1]}")


    if (from_chromium[1] != 4):
        print("from_chromium write is not 4")
        if (from_chromium[0] == 4):
            print("from_chromium[0] is!")
            temp = from_chromium[0]
            from_chromium[0] = os.dup(from_chromium[0])
            os.close(temp)
            print(f"from_chromium[0] is now {from_chromium}!")
        if (to_chromium[0] == 4):
            print("to_chromium[0] is!")
            temp = to_chromium[0]
            to_chromium[0] = os.dup(to_chromium[0])
            os.close(temp)
            print(f"to_chromium[0] is now {to_chromium}!")
        if (to_chromium[1] == 4):
            print("to_chromium[1] is!")
            temp = to_chromium[1]
            to_chromium[1] = os.dup(to_chromium[1])
            os.close(temp)
            print(f"to_chromium[1] is now {to_chromium}!")

        os.dup2(from_chromium[1], 4)
        os.close(from_chromium[1])
        from_chromium[1] = 4
        print("Finished the swap")

    if (to_chromium[0] != 3):
        print("to_chromium read is not 3")
        if (to_chromium[1] == 3):
            print("to_chromium[1] is!")
            temp = to_chromium[1]
            to_chromium[1] = os.dup(to_chromium[1])
            os.close(temp)
            print(f"to_chromium[1] is now {to_chromium}!")
        if (from_chromium[0] == 3):
            print("from_chromium[0] is!")
            temp = from_chromium[0]
            from_chromium[0] = os.dup(from_chromium[0])
            os.close(temp)
            print(f"from_chromium[0] is now {from_chromium}!")
        if (from_chromium[1] == 3):
            print("from_chromium[1] is!")
            temp = from_chromium[1]
            from_chromium[1] = os.dup(from_chromium[1])
            os.close(temp)
            print(f"from_chromium[1] is now {from_chromium}!")

        os.dup2(to_chromium[0], 3)
        os.close(to_chromium[0])
        to_chromium[0] = 3
        print("Finished the swap")

    print(f"from_chromium read: {from_chromium[0]} write: {from_chromium[1]}")
    print(f"to_chromium read: {to_chromium[0]} write: {to_chromium[1]}")
    os.set_inheritable(to_chromium[0], True)
    os.set_inheritable(to_chromium[1], True)
    os.set_inheritable(from_chromium[0], True)
    os.set_inheritable(from_chromium[1], True)

    stderr_pipe = list(os.pipe())
    os.set_inheritable(stderr_pipe[0], True)
    os.set_inheritable(stderr_pipe[1], True)
    proc = subprocess.Popen(
            [path,
                "--headless",
                "--remote-debugging-pipe",
                "--disable-breakpad",
                "--allow-file-access-from-files"],
            close_fds=False,
            stdout=stderr_pipe[1],
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
            )
    return proc

