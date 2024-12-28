import argparse
import asyncio
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
import warnings
import zipfile

# we use arch instead of platform when singular since platform is a package
platforms = ["linux64", "win32", "win64", "mac-x64", "mac-arm64"]

default_local_exe_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "browser_exe",
)

platform_detected = platform.system()
arch_size_detected = "64" if sys.maxsize > 2**32 else "32"
arch_detected = "arm" if platform.processor() == "arm" else "x"

if platform_detected == "Windows":
    chrome_platform_detected = "win" + arch_size_detected
elif platform_detected == "Linux":
    chrome_platform_detected = "linux" + arch_size_detected
elif platform_detected == "Darwin":
    chrome_platform_detected = "mac-" + arch_detected + arch_size_detected

default_exe_name = None
if platform_detected.startswith("Linux"):
    default_exe_name = os.path.join(
        default_local_exe_path,
        f"chrome-{chrome_platform_detected}",
        "chrome",
    )
elif platform_detected.startswith("Darwin"):
    default_exe_name = os.path.join(
        default_local_exe_path,
        f"chrome-{chrome_platform_detected}",
        "Google Chrome for Testing.app",
        "Contents",
        "MacOS",
        "Google Chrome for Testing",
    )
elif platform_detected.startswith("Win"):
    default_exe_name = os.path.join(
        default_local_exe_path,
        f"chrome-{chrome_platform_detected}",
        "chrome.exe",
    )


# https://stackoverflow.com/questions/39296101/python-zipfile-removes-execute-permissions-from-binaries
class ZipFilePermissions(zipfile.ZipFile):
    def _extract_member(self, member, targetpath, pwd):
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        path = super()._extract_member(member, targetpath, pwd)
        # High 16 bits are os specific (bottom is st_mode flag)
        attr = member.external_attr >> 16
        if attr != 0:
            os.chmod(path, attr)
        return path


def get_browser_cli():
    if "ubuntu" in platform.version().lower():
        warnings.warn(
            "You are using `get_browser()` on Ubuntu."
            " Ubuntu is **very strict** about where binaries come from."
            " You have to disable the sandbox with use_sandbox=False"
            " when you initialize the browser OR you can install from Ubuntu's"
            " package manager.",
            UserWarning,
        )
    parser = argparse.ArgumentParser(description="tool to help debug problems")
    parser.add_argument("--i", "-i", type=int, dest="i")
    parser.add_argument("--arch", dest="arch")
    parser.add_argument("--path", dest="path")  # TODO, unused
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
    )  # TODO, unused
    parser.set_defaults(i=-1)
    parser.set_defaults(path=default_local_exe_path)
    parser.set_defaults(arch=chrome_platform_detected)
    parser.set_defaults(verbose=False)
    parsed = parser.parse_args()
    i = parsed.i
    arch = parsed.arch
    path = parsed.path
    verbose = parsed.verbose
    if not arch or arch not in platforms:
        raise RuntimeError(
            f"You must specify a platform: linux64, win32, win64, mac-x64, mac-arm64, not {platform}",
        )
    print(get_browser_sync(arch=arch, i=i, path=path, verbose=verbose))


def get_browser_sync(
    arch=chrome_platform_detected,
    i=-1,
    path=default_local_exe_path,
    verbose=False,
):
    browser_list = json.loads(
        urllib.request.urlopen(
            "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json",
        ).read(),
    )
    version_obj = browser_list["versions"][i]
    if verbose:
        print(version_obj["version"])
        print(version_obj["revision"])
    chromium_sources = version_obj["downloads"]["chrome"]
    url = None
    for src in chromium_sources:
        if src["platform"] == arch:
            url = src["url"]
            break
    if not os.path.exists(path):
        os.makedirs(path)
    filename = os.path.join(path, "chrome.zip")
    with urllib.request.urlopen(url) as response, open(filename, "wb") as out_file:
        shutil.copyfileobj(response, out_file)
    with ZipFilePermissions(filename, "r") as zip_ref:
        zip_ref.extractall(path)

    if arch.startswith("linux"):
        exe_name = os.path.join(path, f"chrome-{arch}", "chrome")
    elif arch.startswith("mac"):
        exe_name = os.path.join(
            path,
            f"chrome-{arch}",
            "Google Chrome for Testing.app",
            "Contents",
            "MacOS",
            "Google Chrome for Testing",
        )
    elif arch.startswith("win"):
        exe_name = os.path.join(path, f"chrome-{arch}", "chrome.exe")

    return exe_name


# to_thread everything
async def get_browser(
    arch=chrome_platform_detected,
    i=-1,
    path=default_local_exe_path,
):
    return await asyncio.to_thread(get_browser_sync, arch=arch, i=i, path=path)


def diagnose():
    from choreographer import Browser, browser_which

    parser = argparse.ArgumentParser(description="tool to help debug problems")
    parser.add_argument("--no-run", dest="run", action="store_false")
    parser.add_argument("--show", dest="headless", action="store_false")
    parser.set_defaults(run=True)
    parser.set_defaults(headless=True)
    args = parser.parse_args()
    run = args.run
    headless = args.headless
    fail = []
    print("*".center(50, "*"))
    print("SYSTEM:".center(50, "*"))
    print(platform.system())
    print(platform.release())
    print(platform.version())
    print(platform.uname())
    print("BROWSER:".center(50, "*"))
    print(browser_which(debug=True))
    print("VERSION INFO:".center(50, "*"))
    try:
        print("PIP:".center(25, "*"))
        print(subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode())
    except BaseException as e:
        print(f"Error w/ pip: {e}")
    try:
        print("UV:".center(25, "*"))
        print(subprocess.check_output(["uv", "pip", "freeze"]).decode())
    except BaseException as e:
        print(f"Error w/ uv: {e}")
    try:
        print("GIT:".center(25, "*"))
        print(
            subprocess.check_output(
                ["git", "describe", "--all", "--tags", "--long", "--always"],
            ).decode(),
        )
    except BaseException as e:
        print(f"Error w/ git: {e}")
    finally:
        print(sys.version)
        print(sys.version_info)
        print("Done with version info.".center(50, "*"))
        pass
    if run:
        try:
            print("Sync Test Headless".center(50, "*"))
            browser = Browser(debug=True, debug_browser=True, headless=headless)
            time.sleep(3)
            browser.close()
        except BaseException as e:
            fail.append(("Sync test headless", e))
        finally:
            print("Done with sync test headless".center(50, "*"))

        async def test_headless():
            browser = await Browser(debug=True, debug_browser=True, headless=headless)
            await asyncio.sleep(3)
            await browser.close()

        try:
            print("Async Test Headless".center(50, "*"))
            asyncio.run(test_headless())
        except BaseException as e:
            fail.append(("Async test headless", e))
        finally:
            print("Done with async test headless".center(50, "*"))
    print("")
    sys.stdout.flush()
    sys.stderr.flush()
    if fail:
        import traceback

        for exception in fail:
            try:
                print(f"Error in: {exception[0]}")
                traceback.print_exception(exception[1])
            except BaseException:
                print("Couldn't print traceback for:")
                print(str(exception))
        raise BaseException("There was an exception, see above.")
    print("Thank you! Please share these results with us!")
