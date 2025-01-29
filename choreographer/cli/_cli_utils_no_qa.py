import argparse
import asyncio
import platform
import subprocess
import sys
import time

# diagnose function is too weird and ruff guts it
# ruff has line-level and file-level QA suppression
# so lets give diagnose a separate file

# ruff: noqa: PLR0915, C901, S603, BLE001, S607, PERF203, TRY002, T201

# in order, exceptions are:
# - function complexity (statements?)
# - function complexity (algo measure)
# - validate subprocess input arguments
# - blind exception
# - partial executable path (bash not /bin/bash)
# - performance overhead of try-except in loop
# - make own exceptions
# - no print


def diagnose() -> None:
    import logistro

    logistro.getLogger().setLevel("DEBUG")

    from choreographer import Browser, BrowserSync
    from choreographer.browsers._chrome_constants import chrome_names
    from choreographer.utils._which import browser_which

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
    print(browser_which(chrome_names))
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
    if run:
        try:
            print("Sync Test Headless".center(50, "*"))
            browser = BrowserSync(headless=headless)
            browser.open()
            time.sleep(3)
            browser.close()
        except BaseException as e:
            fail.append(("Sync test headless", e))
        finally:
            print("Done with sync test headless".center(50, "*"))

        async def test_headless() -> None:
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
    print()
    sys.stdout.flush()
    sys.stderr.flush()
    if fail:
        import traceback

        for exception in fail:
            try:
                print(f"Error in: {exception[0]}")
                traceback.print_exception(
                    type(exception[1]),
                    exception[1],
                    exception[1].__traceback__,
                )
            except BaseException:
                print("Couldn't print traceback for:")
                print(str(exception))
        raise BaseException("There was an exception, see above.")
    print("Thank you! Please share these results with us!")
