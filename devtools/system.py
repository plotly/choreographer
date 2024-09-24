import shutil
import platform
import os

chrome = ["chrome", "Chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
chromium = ["chromium", "chromium-browser"]
# firefox = // this needs to be tested
# brave = // this needs to be tested
# edge = // this needs to be tested

default_path = None
system = platform.system()
if system == "Windows":
    default_path = r"c:\Program Files\Google\Chrome\Application\chrome.exe"
elif system == "Linux":
    default_path = "/usr/bin/google-chrome-stable"
else: # assume mac, or system == "Darwin"
    default_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def which_windows():
    import winreg
    import re

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
    return exe


def which_browser(executable_name=chrome):
    path = None
    if isinstance(executable_name, str):
        executable_name = [executable_name]
    for exe in executable_name:
        if platform.system() == "Windows":
            try:
                path = which_windows()
                break
            except:  # noqa # no bare except according to ruff but who knows what errors we'll get from this
                os.environ["NoDefaultCurrentDirectoryInExePath"] = "0"
        path = shutil.which(exe)
        if path:
            break
    if not path:
        path = default_path
    return path
