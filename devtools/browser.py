import platform
import os
import sys
import subprocess
import tempfile
import warnings
import json
import asyncio
import stat
import shutil
from threading import Thread
from collections import OrderedDict

from .pipe import Pipe
from .protocol import Protocol, DevtoolsProtocolError, TARGET_NOT_FOUND
from .target import Target
from .session import Session
from .tab import Tab
from .system import which_browser

from .pipe import PipeClosedError

class TempDirWarning(UserWarning):
    pass
class UnhandledMessageWarning(UserWarning):
    pass

default_path = which_browser() # probably handle this better
with_onexc = bool(sys.version_info[:3] >= (3, 12))

class Browser(Target):

    def _check_loop(self):
        if self.loop and isinstance(self.loop, asyncio.SelectorEventLoop):
            # I think using set_event_loop_policy is too invasive (is system wide)
            # and may not work in situations where a framework manually set SEL
            self.loop_hack = True

    def __init__(
        self,
        path=None,
        headless=True,
        loop=None,
        executor=None,
        debug=False,
        debug_browser=None,
    ):
        # Configuration
        self.headless = headless
        self.debug = debug
        self.loop_hack = False # subprocess needs weird stuff w/ SelectorEventLoop

        # Set up stderr
        if not debug_browser:  # false o None
            stderr = subprocess.DEVNULL
        elif debug_browser is True:
            stderr = None
        else:
            stderr = debug
        self._stderr = stderr

        # Set up temp dir
        if platform.system() != "Windows":
            self.temp_dir = tempfile.TemporaryDirectory()
        else:
            vinfo = sys.version_info[:3]
            if vinfo >= (3, 12):
                self.temp_dir = tempfile.TemporaryDirectory(
                    delete=False, ignore_cleanup_errors=True
                )
            elif vinfo >= (3, 10):
                self.temp_dir = tempfile.TemporaryDirectory(
                    ignore_cleanup_errors=True
                )
            else:
                self.temp_dir = tempfile.TemporaryDirectory()

        # Set up process env
        new_env = os.environ.copy()

        if not path: # use argument first
            path = os.environ.get("BROWSER_PATH", None)
        if not path:
            path = default_path
        if path:
            new_env["BROWSER_PATH"] = str(path)
        else:
            raise RuntimeError(
                "Could not find an acceptable browser. Please set environmental variable BROWSER_PATH or pass `path=/path/to/browser` into the Browser() constructor."
            )


        new_env["USER_DATA_DIR"] = str(self.temp_dir.name)

        if headless:
            new_env["HEADLESS"] = "--headless"  # unset if false

        self._env = new_env
        if self.debug:
            print("DEBUG REPORT:")
            print(f"BROWSER_PATH: {new_env['BROWSER_PATH']}")
            print(f"USER_DATA_DIR: {new_env['USER_DATA_DIR']}")

        # Defaults for loop
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except Exception:
                loop = False
        self.loop = loop
        self._check_loop()

        # State
        if self.loop:
            self.futures = {}
        self.executor = executor

        self.tabs = OrderedDict()

        # Compose Resources
        self.pipe = Pipe(debug=debug)
        self.protocol = Protocol(debug=debug)

        # Initializing
        super().__init__("0", self)  # NOTE: 0 can't really be used externally
        self.add_session(Session(self, ""))

        if not self.loop:
            self._open()

    async def _delete_session(self, response):
        session_id = response['params']['sessionId']
        self.remove_session(session_id)

    # somewhat out of order, __aenter__ is for use with `async with Browser()`
    # it is basically 99% of __await__, which is for use with `browser = await Browser()`
    # so we just use one inside the other
    def __aenter__(self):
        if self.loop is True:
            self.loop = asyncio.get_running_loop()
            self._check_loop()
        self.future_self = self.loop.create_future()
        self.loop.create_task(self._open_async())
        self.run_read_loop()
        return self.future_self

    # await is basically the second part of __init__() if the user uses
    # await Browser(), which if they are using a loop, they need to.
    def __await__(self):
        return self.__aenter__().__await__()


    def _open(self):
        stderr = self._stderr
        env = self._env
        if platform.system() != "Windows":
            self.subprocess = subprocess.Popen(
                [
                    sys.executable,
                    os.path.join(
                        os.path.dirname(os.path.realpath(__file__)), "chrome_wrapper.py"
                    ),
                ],
                close_fds=True,
                stdin=self.pipe.read_to_chromium,
                stdout=self.pipe.write_from_chromium,
                stderr=stderr,
                env=env,
            )
        else:
            from .chrome_wrapper import open_browser
            self.subprocess = open_browser(to_chromium=self.pipe.read_to_chromium,
                                                   from_chromium=self.pipe.write_from_chromium,
                                                   stderr=stderr,
                                                   env=env,
                                                   loop_hack=self.loop_hack)


    async def _open_async(self):
        stderr = self._stderr
        env = self._env
        if platform.system() != "Windows":
            self.subprocess = await asyncio.create_subprocess_exec(
                sys.executable,
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), "chrome_wrapper.py"
                ),
                stdin=self.pipe.read_to_chromium,
                stdout=self.pipe.write_from_chromium,
                stderr=stderr,
                close_fds=True,
                env=env,
            )
        else:
            from .chrome_wrapper import open_browser
            self.subprocess = await open_browser(to_chromium=self.pipe.read_to_chromium,
                                                   from_chromium=self.pipe.write_from_chromium,
                                                   stderr=stderr,
                                                   env=env,
                                                   loop=True,
                                                   loop_hack=self.loop_hack)
        await self.populate_targets()
        self.future_self.set_result(self)

    def _clean_temp(self):
        name = self.temp_dir.name
        clean = False
        try:
            self.temp_dir.cleanup()
            clean=True
        except BaseException as e:
            if platform.system() == "Windows" and not self.debug:
                pass
            else:
                warnings.warn(str(e), TempDirWarning)

        # windows+old vers doesn't like python's default cleanup

        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWUSR)
            func(path)

        try:
            if with_onexc:
                shutil.rmtree(self.temp_dir.name, onexc=remove_readonly)
                clean=True
            else:
                shutil.rmtree(self.temp_dir.name, onerror=remove_readonly)
                clean=True
            del self.temp_dir
        except FileNotFoundError:
            pass # it worked!
        except PermissionError:
            if not clean:
                warnings.warn(
                    "The temporary directory could not be deleted, due to permission error, execution will continue.", TempDirWarning
                )
        except BaseException as e:
            if not clean:
                warnings.warn(
                        f"The temporary directory could not be deleted, execution will continue. {type(e)}: {e}", TempDirWarning
                )
        if self.debug:
            print(f"Tempfile still exists?: {bool(os.path.exists(str(name)))}")

    async def _is_closed_async(self, wait=0):
        waiter = self.subprocess.wait()
        try:
            await asyncio.wait_for(waiter, wait)
            return True
        except: # noqa
            return False

    def _is_closed(self, wait=0):
        if not wait:
            if not self.subprocess.poll():
                return False
            else:
                return True
        else:
            try:
                self.subprocess.wait(wait)
                return True
            except: # noqa
                return False

    # _sync_close and _async_close are basically the same thing

    def _sync_close(self):
        if self._is_closed():
            if self.debug: print("Browser was already closed.", file=sys.stderr)
            return
        # check if no sessions or targets
        self.send_command("Browser.close")
        if self._is_closed():
            if self.debug: print("Browser.close method closed browser", file=sys.stderr)
            return
        self.pipe.close()
        if self._is_closed(wait = 1):
            if self.debug: print("pipe.close() (or slow Browser.close) method closed browser", file=sys.stderr)
            return

        # Start a kill
        if platform.system() == "Windows":
            if not self._is_closed():
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.subprocess.pid)],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                )
                if self._is_closed(wait = 4):
                    return
                else:
                    raise RuntimeError("Couldn't kill browser subprocess")
        else:
            self.subprocess.terminate()
            if self._is_closed():
                if self.debug: print("terminate() closed the browser", file=sys.stderr)
                return

            self.subprocess.kill()
            if self._is_closed():
                if self.debug: print("kill() closed the browser", file=sys.stderr)
        return


    async def _async_close(self):
        if await self._is_closed_async():
            if self.debug: print("Browser was already closed.", file=sys.stderr)
            return
        # TODO: Above doesn't work with closed tabs for some reason
        # TODO: check if tabs?
        # TODO: track tabs?
        await asyncio.wait([self.send_command("Browser.close")], timeout=1)
        if await self._is_closed_async():
            if self.debug: print("Browser.close method closed browser", file=sys.stderr)
            return
        self.pipe.close()
        if await self._is_closed_async(wait=1):
            if self.debug: print("pipe.close() method closed browser", file=sys.stderr)
            return

        # Start a kill
        if platform.system() == "Windows":
            if not await self._is_closed_async():
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.subprocess.pid)],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                )
                if await self._is_closed_async(wait = 4):
                    return
                else:
                    raise RuntimeError("Couldn't kill browser subprocess")
        else:
            self.subprocess.terminate()
            if await self._is_closed_async():
                if self.debug: print("terminate() closed the browser", file=sys.stderr)
                return

            self.subprocess.kill()
            if await self._is_closed_async():
                if self.debug: print("kill() closed the browser", file=sys.stderr)
        return


    def close(self):
        if self.loop:
            async def close_task():
                await self._async_close()
                self.pipe.close()
                self._clean_temp() # can we make async
            return asyncio.create_task(close_task())
        else:
            self._sync_close()
            self.pipe.close()
            self._clean_temp()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    async def __aexit__(self, type, value, traceback):
        await self.close()

    # Basic syncronous functions

    def _add_tab(self, tab):
        if not isinstance(tab, Tab):
            raise TypeError("tab must be an object of class Tab")
        self.tabs[tab.target_id] = tab

    def _remove_tab(self, target_id):
        if isinstance(target_id, Tab):
            target_id = target_id.target_id
        del self.tabs[target_id]

    def get_tab(self):
        if self.tabs.values():
            return list(self.tabs.values())[0]

    # Better functions that require asyncronous

    async def create_tab(self, url="", width=None, height=None):
        if not self.loop:
            raise RuntimeError(
                "There is no eventloop, or was not passed to browser. Cannot use async methods"
            )
        if self.headless and (width or height):
            warnings.warn(
                "Width and height only work for headless chrome mode, they will be ignored."
            )
            width = None
            height = None
        params = dict(url=url)
        if width:
            params["width"] = width
        if height:
            params["height"] = height

        response = await self.browser.send_command("Target.createTarget", params=params)
        if "error" in response:
            raise RuntimeError("Could not create tab") from Exception(response["error"])
        target_id = response["result"]["targetId"]
        new_tab = Tab(target_id, self)
        self._add_tab(new_tab)
        await new_tab.create_session()
        return new_tab

    async def close_tab(self, target_id):
        if not self.loop:
            raise RuntimeError(
                "There is no eventloop, or was not passed to browser. Cannot use async methods"
            )
        if isinstance(target_id, Target):
            target_id = target_id.target_id
        # NOTE: we don't need to manually remove sessions because
        # sessions are intrinisically handled by events
        response = await self.send_command(
            command="Target.closeTarget",
            params={"targetId": target_id},
        )
        self._remove_tab(target_id)
        if "error" in response:
            raise RuntimeError("Could not close tab") from Exception(response["error"])
        return response

    async def create_session(self):
        if not self.browser.loop:
            raise RuntimeError(
                "There is no eventloop, or was not passed to browser. Cannot use async methods"
            )
        warnings.warn(
            "Creating new sessions on Browser() only works with some versions of Chrome, it is experimental."
        )
        response = await self.browser.send_command("Target.attachToBrowserTarget")
        if "error" in response:
            raise RuntimeError("Could not create session") from Exception(
                response["error"]
            )
        session_id = response["result"]["sessionId"]
        new_session = Session(self, session_id)
        self.add_session(new_session)
        return new_session

    async def populate_targets(self):
        if not self.browser.loop:
            warnings.warn("This method requires use of an event loop (asyncio).")
        response = await self.browser.send_command("Target.getTargets")
        if "error" in response:
            raise RuntimeError("Could not get targets") from Exception(
                response["error"]
            )

        for json_response in response["result"]["targetInfos"]:
            if (
                json_response["type"] == "page"
                and json_response["targetId"] not in self.tabs
            ):
                target_id = json_response["targetId"]
                new_tab = Tab(target_id, self)
                try:
                    await new_tab.create_session()
                except DevtoolsProtocolError as e:
                    if e.code == TARGET_NOT_FOUND:
                        if self.debug:
                            print(
                                f"Target {target_id} not found (could be closed before)",
                                file=sys.stderr
                                )
                        continue
                    else:
                        raise e
                self._add_tab(new_tab)
                if self.debug:
                    print(f"The target {target_id} was added", file=sys.stderr)

    # Output Helper for Debugging

    def run_output_thread(self, debug=None):
        if self.loop:
            raise ValueError("You must use this method without loop in the Browser")
        if not debug:
            debug = self.debug

        def run_print(debug):
            if debug: print("Starting run_print loop", file=sys.stderr)
            while True:
                try:
                    responses = self.pipe.read_jsons(debug=debug)
                    for response in responses:
                        print(json.dumps(response, indent=4))
                except PipeClosedError:
                    if self.debug:
                        print("PipeClosedError caught", file=sys.stderr)
                    break

        Thread(target=run_print, args=(debug,)).start()

    def _get_target_for_session(self, session_id):
        for tab in self.tabs.values():
            if session_id in tab.sessions:
                return tab
        if session_id in self.sessions:
            return self
        return None

    def run_read_loop(self):
        async def read_loop():
            try:
                responses = await self.loop.run_in_executor(
                    self.executor, self.pipe.read_jsons, True, self.debug
                )
                for response in responses:
                    error = self.protocol.get_error(response)
                    key = self.protocol.calculate_key(response)
                    if not self.protocol.has_id(response) and error:
                        raise RuntimeError(error)
                    elif self.protocol.is_event(response):
                        event_session_id = response.get("sessionId", "")
                        if event_session_id == "":
                            session_id = ""
                        else:
                            session_id = response["params"]["sessionId"]
                        session = self.protocol.sessions[session_id]
                        target = self._get_target_for_session(session_id) # and if there is no target TODO
                        
                        subscriptions = session.subscriptions
                        subscriptions_futures = session.subscriptions_futures

                        for sub_key in list(subscriptions):
                            similar_strings = sub_key.endswith("*") and response[
                                "method"
                            ].startswith(sub_key[:-1])
                            equals_method = response["method"] == sub_key
                            if self.debug:
                                print(f"Checking subscription key: {sub_key} against event method {response['method']}", file=sys.stderr)
                            if similar_strings or equals_method:
                                self.loop.create_task(
                                    subscriptions[sub_key][0](response)
                                )
                                if not subscriptions[sub_key][1]: # if not repeating
                                    self.protocol.sessions[session_id].unsubscribe(sub_key)

                        if response["method"] == "Target.detachedFromTarget":
                            if target:
                                target.remove_session(session_id)
                            _ = self.protocol.sessions.pop(session_id, None)
                            if self.debug:
                                print(
                                    f"Use intern subscription key: 'Target.detachedFromTarget'. Session {session_id} was closed.",
                                    file=sys.stderr
                                    )

                        for sub_key, futures in list(subscriptions_futures.items()):
                            similar_strings = sub_key.endswith("*") and response["method"].startswith(sub_key[:-1])
                            equals_method = response["method"] == sub_key
                            if self.debug:
                                print(f"Checking subscription key: {sub_key} against event method {response['method']}", file=sys.stderr)
                            if similar_strings or equals_method:
                                for future in futures:
                                    if self.debug:
                                        print(f"Processing future {id(future)}", file=sys.stderr)
                                    future.set_result(response)
                                    if self.debug:
                                        print(f"Future resolved with response {future}", file=sys.stderr)
                                del session.subscriptions_futures[sub_key]


                    elif key:
                        future = None
                        if key in self.futures:
                            if self.debug:
                                print(
                                    f"run_read_loop() found future foor key {key}"
                                )
                            future = self.futures.pop(key)
                        else:
                            raise RuntimeError(f"Couldn't find a future for key: {key}")
                        if error:
                            future.set_result(response)
                        else:
                            future.set_result(response)
                    else:
                        warnings.warn(f"Unhandled message type:{str(response)}", UnhandledMessageWarning)
            except PipeClosedError:
                if self.debug:
                    print("PipeClosedError caught", file=sys.stderr)
                return
            self.loop.create_task(read_loop())

        self.loop.create_task(read_loop())

    def write_json(self, obj):
        self.protocol.verify_json(obj)
        key = self.protocol.calculate_key(obj)
        if self.loop:
            future = self.loop.create_future()
            self.futures[key] = future
            self.loop.run_in_executor(
                self.executor, self.pipe.write_json, obj
            )  # ignore result
            return future
        else:
            self.pipe.write_json(obj)
            return key

# this is the dtdoctor.exe function to help get debug reports
# it is not really part of this program
def diagnose():
    import subprocess, sys, time # noqa
    fail = []
    print("*".center(50, "*"))
    print("Collecting information about the system:".center(50, "*"))
    print(platform.system())
    print(platform.release())
    print(platform.version())
    print(platform.uname())
    print("Looking for browser:".center(50, "*"))
    print(which_browser(debug=True))
    try:
        print("Looking for version info:".center(50, "*"))
        print(subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']))
        print(subprocess.check_output(["git", "describe", "--all", "--tags", "--long", "--always",]))
        print(sys.version)
        print(sys.version_info)
    except BaseException as e:
        fail.append(("System Info", e))
    finally:
        print("Done with version info.".center(50, "*"))
        pass
    try:
        print("Sync test headless".center(50, "*"))
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
        print("Async Test headless".center(50, "*"))
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
