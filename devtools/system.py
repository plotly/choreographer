import shutil
import platform
import os

chrome = ["chrome", "Chrome", "google-chrome", "google-chrome-stable", "chromium"]
chromium = ["chromium"]
# firefox = // this needs to be tested
# brave = // this needs to be tested
# edge = // this needs to be tested

def which_browser(executable_name = chrome):
    path = None
    if isinstance(executable_name, str):
        executable_name = [executable_name]
    for exe in executable_name:
        if platform.system() == "Windows":
            os.environ['NoDefaultCurrentDirectoryInExePath']=0
        path = shutil.which(exe)
        if path: break
    # if not path, error
    return path
