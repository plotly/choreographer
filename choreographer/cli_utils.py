import argparse
import asyncio
import platform
import subprocess
import sys
import time

from choreographer import Browser
from choreographer import which_browser


def get_browser(latest=True): ...


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
