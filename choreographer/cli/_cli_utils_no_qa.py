import argparse
import asyncio
import platform
import subprocess
import sys
import time

import logistro

# diagnose function is too weird and ruff guts it
# ruff has line-level and file-level QA suppression
# so lets give diagnose a separate file

# ruff: noqa: PLR0915, C901, S603, BLE001, S607, PERF203, TRY002, T201, PLR0912, SLF001
# ruff: noqa: PLC0415
# ruff: noqa: F401, ERA001 # temporary, sync
# ruff: noqa: PLC0415 - import at time of file

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
    logistro.getLogger().setLevel(6)
    logistro.getLogger().error("Test")
    from choreographer import Browser, BrowserSync
    from choreographer.browsers.chromium import _find_a_chromium_based_browser
    from choreographer.utils._which import browser_which

    parser = argparse.ArgumentParser(
        description="tool to help debug problems",
        parents=[logistro.parser],
    )
    parser.add_argument("--no-run", dest="run", action="store_false")
    parser.add_argument("--show", dest="headless", action="store_false")
    parser.set_defaults(run=True)
    parser.set_defaults(headless=True)
    args, _ = parser.parse_known_args()
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
    try:
        print("Found local: {browser_which(verify_local=True)}")
    except RuntimeError:
        print("Didn't find local.")
    browser_path = _find_a_chromium_based_browser(skip_local=True)
    print(browser_path)
    print("BROWSER_INIT_CHECK (DEPS)".center(50, "*"))
    if not browser_path:
        print("No browser, found can't check for deps.")
    else:
        b = Browser()
        b._browser_impl.pre_open()
        cli = b._browser_impl.get_cli()
        env = b._browser_impl.get_env()
        b._browser_impl.clean()
        del b
        print("cli:")
        for arg in cli:
            print(arg)
        print("env:")
        for k, v in env.items():
            print(f"{k}:{v}")
    print("VERSION INFO:".center(50, "*"))
    try:
        print("PIP:".center(25, "*"))
        print(subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode())
    except Exception as e:
        print(f"Error w/ pip: {e}")
    try:
        print("UV:".center(25, "*"))
        print(subprocess.check_output(["uv", "pip", "freeze"]).decode())
    except Exception as e:
        print(f"Error w/ uv: {e}")
    try:
        print("GIT:".center(25, "*"))
        print(
            subprocess.check_output(
                ["git", "describe", "--tags", "--long", "--always"],
            ).decode(),
        )
    except Exception as e:
        print(f"Error w/ git: {e}")
    finally:
        print(sys.version)
        print(sys.version_info)
        print("Done with version info.".center(50, "*"))
    if run:
        try:
            print("Skipping sync test...")
            # print("Sync Test Headless".center(50, "*"))
            # browser = BrowserSync(headless=headless)
            # browser.open()
            # time.sleep(3)
            # browser.close()
        except Exception as e:
            fail.append(("Sync test headless", e))
        finally:
            print("Done with sync test headless".center(50, "*"))

        async def test_headless() -> None:
            browser = await Browser(headless=headless)
            await asyncio.sleep(3)
            await browser.close()

        try:
            print("Async Test Headless".center(50, "*"))
            asyncio.run(test_headless())
        except Exception as e:
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
            except Exception:
                print("Couldn't print traceback for:")
                print(str(exception))
        raise Exception("There was an exception, see above.")
    print("Thank you! Please share these results with us!")
