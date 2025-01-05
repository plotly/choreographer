import os
import platform
import shutil
import sys

from choreographer._cli_utils import default_exe_name

chrome = [
    "chrome",
    "Chrome",
    "google-chrome",
    "google-chrome-stable",
    "Chrome.app",
    "Google Chrome",
    "Google Chrome.app",
    "chromium",
    "chromium-browser",
]
chromium = ["chromium", "chromium-browser"]
# firefox = // this needs to be tested
# brave = // this needs to be tested

default_path_chrome = None

if platform.system() == "Windows":
    default_path_chrome = [
        r"c:\Program Files\Google\Chrome\Application\chrome.exe",
        f"c:\\Users\\{os.environ.get('USER', 'default')}\\AppData\\"
        "Local\\Google\\Chrome\\Application\\chrome.exe",
    ]
elif platform.system() == "Linux":
    default_path_chrome = [
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chrome",
    ]
else:  # assume mac, or system == "Darwin"
    default_path_chrome = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]


def which_windows_chrome():
    try:
        import re
        import winreg

        command = winreg.QueryValueEx(
            winreg.OpenKey(
                winreg.HKEY_CLASSES_ROOT,
                "ChromeHTML\\shell\\open\\command",
                0,
                winreg.KEY_READ,
            ),
            "",
        )[0]
        exe = re.search('"(.*?)"', command).group(1)
    except BaseException:  # noqa: BLE001 don't care why, best effort search
        return None
    return exe


def _is_exe(path):
    try:
        return os.access(path, os.X_OK)
    except:  # noqa: E722 bare except ok, weird errors, best effort.
        return False


def browser_which(executable_name=chrome, *, debug=False, skip_local=False):  # noqa: PLR0912, C901
    if debug:
        print(f"Checking {default_exe_name}", file=sys.stderr)
    if not skip_local and default_exe_name.exists():
        if debug:
            print(f"Found {default_exe_name}", file=sys.stderr)
        return default_exe_name
    path = None
    if isinstance(executable_name, str):
        executable_name = [executable_name]
    if platform.system() == "Windows":
        os.environ["NoDefaultCurrentDirectoryInExePath"] = "0"  # noqa: SIM112 var name set by windows
    for exe in executable_name:
        if debug:
            print(f"looking for {exe}", file=sys.stderr)
        if platform.system() == "Windows" and exe == "chrome":
            path = which_windows_chrome()
            if path and _is_exe(path):
                return path
        path = shutil.which(exe)
        if debug:
            print(f"looking for {path}", file=sys.stderr)
        if path and _is_exe(path):
            return path
    default_path = []
    if executable_name == chrome:
        default_path = default_path_chrome
    for candidate in default_path:
        if debug:
            print(f"Looking at {candidate}", file=sys.stderr)
        if _is_exe(candidate):
            return candidate
    if debug:
        print("Found nothing...", file=sys.stderr)
    return None
