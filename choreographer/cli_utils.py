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
import zipfile

from choreographer import Browser
from choreographer import which_browser

platforms = ["linux64", "win32", "win64", "mac-x64", "mac-arm64"]
default_exe_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "browser_exe",
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
    parser = argparse.ArgumentParser(description="tool to help debug problems")
    parser.add_argument("--i", "-i", type=int, dest="i")
    parser.add_argument("--platform", dest="platform")
    parser.add_argument("--path", dest="path")  # TODO, unused
    parser.set_defaults(i=-1)
    parser.set_defaults(path=default_exe_path)
    parsed = parser.parse_args()
    i = parsed.i
    platform = parsed.platform
    path = parsed.path
    if not platform or platform not in platforms:
        raise RuntimeError(
            f"You must specify a platform: linux64, win32, win64, mac-x64, mac-arm64, not {platform}",
        )
    print(get_browser_sync(platform, i, path))


def get_browser_sync(platform, i=-1, path=default_exe_path):
    browser_list = json.loads(
        urllib.request.urlopen(
            "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json",
        ).read(),
    )
    chromium_sources = browser_list["versions"][i]["downloads"]["chrome"]
    url = None
    for src in chromium_sources:
        if src["platform"] == platform:
            url = src["url"]
            break
    if not os.path.exists(path):
        os.makedirs(path)
    filename = os.path.join(path, "chrome.zip")
    with urllib.request.urlopen(url) as response, open(filename, "wb") as out_file:
        shutil.copyfileobj(response, out_file)
    with ZipFilePermissions(filename, "r") as zip_ref:
        zip_ref.extractall(path)
    exe_name = os.path.join(path, f"chrome-{platform}", "chrome")
    return exe_name


async def get_browser(): ...


def diagnose():
    parser = argparse.ArgumentParser(description="tool to help debug problems")
    parser.add_argument("--no-run", dest="run", action="store_false")
    parser.set_defaults(run=True)
    run = parser.parse_args().run
    fail = []
    print("*".center(50, "*"))
    print("SYSTEM:".center(50, "*"))
    print(platform.system())
    print(platform.release())
    print(platform.version())
    print(platform.uname())
    print("BROWSER:".center(50, "*"))
    print(which_browser(debug=True))
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
            browser = Browser(debug=True, debug_browser=True, headless=True)
            time.sleep(3)
            browser.close()
        except BaseException as e:
            fail.append(("Sync test headless", e))
        finally:
            print("Done with sync test headless".center(50, "*"))

        async def test_headless():
            browser = await Browser(debug=True, debug_browser=True, headless=True)
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
