import shutil
import platform
import os

chrome = ["chrome", "Chrome", "google-chrome", "google-chrome-stable", "chromium"]
chromium = ["chromium"]
# firefox = // this needs to be tested
# brave = // this needs to be tested
# edge = // this needs to be tested


def which_windows(): 
    import winreg
    import re
    command = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "ChromeHTML\\shell\\open\\command", 0, winreg.KEY_READ), "")[0]
    exe=re.search("\"(.*?)\"", command).group(1)
    return exe

def which_browser(executable_name = chrome):
    path = None
    if isinstance(executable_name, str):
        executable_name = [executable_name]
    for exe in executable_name:
        if platform.system() == "Windows":
            win_path = None
            try:
                path = which_windows()
                print(path)
                break
            except:
                os.environ['NoDefaultCurrentDirectoryInExePath']="0"
        path = shutil.which(exe)
        if path: break
    if not path:
        raise RuntimeError("Could not find chrome. Please path execution path as environmental variable BROWSER_PATH")
    return path
