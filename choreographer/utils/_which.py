import os
import platform
import shutil

from choreographer.cli import get_chrome_download_path


def _is_exe(path):
    try:
        return os.access(path, os.X_OK)
    except:  # noqa: E722 bare except ok, weird errors, best effort.
        return False


def _which_from_windows_reg():
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


def browser_which(executable_names, *, skip_local=False):
    """
    Look for and return first name found in PATH.

    Args:
        executable_names: the list of names to look for
        skip_local: (default False) don't look for a choreo download of anything.

    """
    path = None

    if isinstance(executable_names, str):
        executable_names = [executable_names]

    local_chrome = get_chrome_download_path()
    if (
        local_chrome.exists()
        and not skip_local
        and local_chrome.name in executable_names
    ):
        return local_chrome

    if platform.system() == "Windows":
        os.environ["NoDefaultCurrentDirectoryInExePath"] = "0"  # noqa: SIM112 var name set by windows

    for exe in executable_names:
        if platform.system() == "Windows" and exe == "chrome":
            path = _which_from_windows_reg()
        if path and _is_exe(path):
            return path
        path = shutil.which(exe)
        if path and _is_exe(path):
            return path
    # which didn't work

    # hail mary
    return None


def get_browser_path(*args, **kwargs):  # noqa: D417: don't pass args explicitly
    """
    Call `browser_which()` but check for user override first.

    It looks for the browser in path.

    Accepts the same arguments as `browser_which':

    Args:
        executable_names: the list of names to look for
        skip_local: (default False) don't look for a choreo download of anything.

    """
    return os.environ.get("BROWSER_PATH", browser_which(*args, **kwargs))
