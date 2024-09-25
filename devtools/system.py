import shutil
import platform
import os

chrome = ["chrome", "Chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
chromium = ["chromium", "chromium-browser"]
# firefox = // this needs to be tested
# brave = // this needs to be tested
# edge = // this needs to be tested


def which_windows_chrome():
    try:
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
    except BaseException:
        return None

def _is_exe(path):
    return os.access(path, os.X_OK)

def which_browser(executable_name=chrome):
    path = None
    if isinstance(executable_name, str):
        executable_name = [executable_name]
    if platform.system() == "Windows":
        os.environ["NoDefaultCurrentDirectoryInExePath"] = "0"
    for exe in executable_name:
        if platform.system() == "Windows" and exe == "chrome":
            path = which_windows_chrome()
            if path and _is_exe(path):
                return path
        path = shutil.which(exe)
        if path and _is_exe(path):
            return path
    return None
