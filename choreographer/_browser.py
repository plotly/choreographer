import asyncio
import io
import json
import os
import platform
import subprocess
import sys
import warnings
from collections import OrderedDict
from threading import Thread

from _devtools_protocol_layer._protocol import DevtoolsProtocolError
from _devtools_protocol_layer._protocol import ExperimentalFeatureWarning
from _devtools_protocol_layer._protocol import Protocol
from _devtools_protocol_layer._protocol import TARGET_NOT_FOUND
from _devtools_protocol_layer._session import Session
from _devtools_protocol_layer._target import Target
from _system_utils._system import browser_which
from _system_utils._tempfile import TempDirectory
from _system_utils._tempfile import TempDirWarning

from ._pipe import Pipe
from ._pipe import PipeClosedError
from ._tab import Tab


class UnhandledMessageWarning(UserWarning):
    pass


class BrowserFailedError(RuntimeError):
    pass


class BrowserClosedError(RuntimeError):
    pass


def get_browser_path(**kwargs):
    return os.environ.get("BROWSER_PATH", browser_which(**kwargs))


class Browser(Target):
    # Some frameworks configure windows use SelectorEventLoop, which lacks
    # certain features, so we need to know.
    def _check_loop(self):
        # Lock
        if not self.lock:
            self.lock = asyncio.Lock()
        if (
            platform.system() == "Windows"
            and self.loop
            and isinstance(self.loop, asyncio.SelectorEventLoop)
        ):
            if self.debug:
                print("We are in a selector event loop, use loop_hack", file=sys.stderr)
            self._loop_hack = True

    def __init__(
        self,
        path=None,
        headless=True,
        debug=False,
        debug_browser=False,
        **kwargs,
    ):
        ### Set some defaults
        self._env = os.environ.copy()  # environment for subprocesses
        self._loop_hack = False  # see _check_loop
        self.lock = None  # TODO where else is this set
        self.tabs = OrderedDict()
        self.sandboxed = False  # this is if our processes can't use /tmp

        # Browser Configuration
        self.enable_sandbox = kwargs.pop("enable_sandbox", False)
        if self.enable_sandbox:
            self._env["SANDBOX_ENABLED"] = "true"
        if not path:
            skip_local = bool(
                "ubuntu" in platform.version().lower() and self.enable_sandbox,
            )
            path = get_browser_path(skip_local=skip_local)
        if not path:
            raise BrowserFailedError(
                "Could not find an acceptable browser. Please call `choreo.get_browser()`, set environmental variable BROWSER_PATH or pass `path=/path/to/browser` into the Browser() constructor. The latter two work with Edge.",
            )
        if "snap" in str(path):
            self.sandboxed = True  # not chromium sandbox, snap sandbox
        self._env["BROWSER_PATH"] = str(path)
        self.headless = headless
        if headless:
            self._env["HEADLESS"] = "--headless"
        self.debug = debug
        self.enable_gpu = kwargs.pop("enable_gpu", False)
        if self.enable_gpu:
            self._env["GPU_ENABLED"] = "true"

        # Expert Configuration
        tmp_path = kwargs.pop("tmp_path", None)
        self.tmp_dir = TempDirectory(tmp_path, sneak=self.sandboxed)

        try:
            self.loop = kwargs.pop("loop", asyncio.get_running_loop())
        except Exception:
            self.loop = False
        if self.loop:
            self.futures = {}
            self._check_loop()
        self.executor = kwargs.pop("executor", None)

        if len(kwargs):
            raise ValueError(f"Unknown keyword arguments: {kwargs}")

        # Set up stderr
        if debug_browser is False:  # false o None
            stderr = subprocess.DEVNULL
        elif debug_browser is True:
            stderr = sys.stderr
        else:
            stderr = debug_browser

        if (
            stderr
            and stderr not in (subprocess.PIPE, subprocess.STDOUT, subprocess.DEVNULL)
            and not isinstance(stderr, int)
        ):
            try:
                stderr.fileno()
            except io.UnsupportedOperation:
                warnings.warn(
                    "A value has been passed to debug_browser which is not compatible with python's Popen. This may be because one was passed to Browser or because sys.stderr has been overridden by a framework. Browser logs will not be handled by python in this case.",
                )
                stderr = None

        self._stderr = stderr

        if debug:
            print(f"STDERR: {stderr}", file=sys.stderr)

        self._env["USER_DATA_DIR"] = str(self.tmp_dir.path)

        # Compose Resources
        self.pipe = Pipe(debug=debug)
        self.protocol = Protocol(debug=debug)

        # Initializing
        super().__init__("0", self)  # NOTE: 0 can't really be used externally
        self._add_session(Session(self, ""))

        if self.debug:
            print("DEBUG REPORT:", file=sys.stderr)
            print(f"BROWSER_PATH: {self._env['BROWSER_PATH']}", file=sys.stderr)
            print(f"USER_DATA_DIR: {self._env['USER_DATA_DIR']}", file=sys.stderr)
        if not self.loop:
            self._open()

    # for use with `async with Browser()`
    def __aenter__(self):
        self.future_self = self.loop.create_future()
        self.loop.create_task(self._open_async())
        self.run_read_loop()
        return self.future_self

    def __enter__(self):
        return self

    # for use with `await Browser()`
    # TODO: why have to call __await__ when __aenter__ returns a future
    def __await__(self):
        return self.__aenter__().__await__()

    def _open(self):
        if platform.system() != "Windows":
            self.subprocess = subprocess.Popen(
                [
                    sys.executable,
                    os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        "chrome_wrapper.py",
                    ),
                ],
                close_fds=True,
                stdin=self.pipe.read_to_chromium,
                stdout=self.pipe.write_from_chromium,
                stderr=self._stderr,
                env=self._env,
            )
        else:
            from .chrome_wrapper import open_browser

            self.subprocess = open_browser(
                to_chromium=self.pipe.read_to_chromium,
                from_chromium=self.pipe.write_from_chromium,
                stderr=self._stderr,
                env=self._env,
                loop_hack=self._loop_hack,
            )

    async def _open_async(self):
        try:
            if platform.system() != "Windows":
                self.subprocess = await asyncio.create_subprocess_exec(
                    sys.executable,
                    os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        "chrome_wrapper.py",
                    ),
                    stdin=self.pipe.read_to_chromium,
                    stdout=self.pipe.write_from_chromium,
                    stderr=self._stderr,
                    close_fds=True,
                    env=self._env,
                )
            else:
                from .chrome_wrapper import open_browser

                self.subprocess = await open_browser(
                    to_chromium=self.pipe.read_to_chromium,
                    from_chromium=self.pipe.write_from_chromium,
                    stderr=self._stderr,
                    env=self._env,
                    loop=True,
                    loop_hack=self._loop_hack,
                )
            self.loop.create_task(self._watchdog())
            await self.populate_targets()
            self.future_self.set_result(self)
        except (BrowserClosedError, BrowserFailedError, asyncio.CancelledError) as e:
            raise BrowserFailedError(
                "The browser seemed to close immediately after starting. Perhaps adding debug_browser=True will help.",
            ) from e

    async def _is_closed_async(self, wait=0):
        if self.debug:
            print(f"is_closed called with wait: {wait}", file=sys.stderr)
        if self._loop_hack:
            # Use synchronous tools in thread
            return await asyncio.to_thread(self._is_closed, wait)
        waiter = self.subprocess.wait()
        try:
            if wait == 0:  # this never works cause processing
                wait = 0.15
            await asyncio.wait_for(waiter, wait)
            return True
        except Exception:
            return False

    def _is_closed(self, wait=0):
        if wait == 0:
            if self.subprocess.poll() is None:
                return False
            else:
                return True
        else:
            try:
                self.subprocess.wait(wait)
                return True
            except:  # noqa
                return False

    # _sync_close and _async_close are basically the same thing

    def _sync_close(self):
        if self._is_closed():
            if self.debug:
                print("Browser was already closed.", file=sys.stderr)
            return
        # check if no sessions or targets
        self.send_command("Browser.close")
        if self._is_closed():
            if self.debug:
                print("Browser.close method closed browser", file=sys.stderr)
            return
        self.pipe.close()
        if self._is_closed(wait=1):
            if self.debug:
                print(
                    "pipe.close() (or slow Browser.close) method closed browser",
                    file=sys.stderr,
                )
            return

        # Start a kill
        if platform.system() == "Windows":
            if not self._is_closed():
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.subprocess.pid)],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                )
                if self._is_closed(wait=4):
                    return
                else:
                    raise RuntimeError("Couldn't kill browser subprocess")
        else:
            self.subprocess.terminate()
            if self._is_closed():
                if self.debug:
                    print("terminate() closed the browser", file=sys.stderr)
                return

            self.subprocess.kill()
            if self._is_closed(wait=4):
                if self.debug:
                    print("kill() closed the browser", file=sys.stderr)
        return

    async def _async_close(self):
        if await self._is_closed_async():
            if self.debug:
                print("Browser was already closed.", file=sys.stderr)
            return
        await asyncio.wait([self.send_command("Browser.close")], timeout=1)
        if await self._is_closed_async():
            if self.debug:
                print("Browser.close method closed browser", file=sys.stderr)
            return
        self.pipe.close()
        if await self._is_closed_async(wait=1):
            if self.debug:
                print("pipe.close() method closed browser", file=sys.stderr)
            return

        # Start a kill
        if platform.system() == "Windows":
            if not await self._is_closed_async():
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.subprocess.pid)],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                )
                if await self._is_closed_async(wait=4):
                    return
                else:
                    raise RuntimeError("Couldn't kill browser subprocess")
        else:
            self.subprocess.terminate()
            if await self._is_closed_async():
                if self.debug:
                    print("terminate() closed the browser", file=sys.stderr)
                return

            self.subprocess.kill()
            if await self._is_closed_async(wait=4):
                if self.debug:
                    print("kill() closed the browser", file=sys.stderr)
        return

    def close(self):
        if self.loop:

            async def close_task():
                if self.lock.locked():
                    return
                await self.lock.acquire()
                if not self.future_self.done():
                    self.future_self.set_exception(
                        BrowserFailedError(
                            "Close() was called before the browser finished opening- maybe it crashed?",
                        ),
                    )
                for future in self.futures.values():
                    if future.done():
                        continue
                    future.set_exception(
                        BrowserClosedError(
                            "Command not completed because browser closed.",
                        ),
                    )
                for session in self.sessions.values():
                    for futures in session.subscriptions_futures.values():
                        for future in futures:
                            if future.done():
                                continue
                            future.set_exception(
                                BrowserClosedError(
                                    "Event not complete because browser closed.",
                                ),
                            )
                for tab in self.tabs.values():
                    for session in tab.sessions.values():
                        for futures in session.subscriptions_futures.values():
                            for future in futures:
                                if future.done():
                                    continue
                                future.set_exception(
                                    BrowserClosedError(
                                        "Event not completed because browser closed.",
                                    ),
                                )
                try:
                    await self._async_close()
                except ProcessLookupError:
                    pass
                self.pipe.close()
                self.tmp_dir.clean()

            return asyncio.create_task(close_task())
        else:
            try:
                self._sync_close()
            except ProcessLookupError:
                pass
            self.pipe.close()
            self.tmp_dir.clean()

    async def _watchdog(self):
        self._watchdog_healthy = True
        if self.debug:
            print("Starting watchdog", file=sys.stderr)
        await self.subprocess.wait()
        if self.lock.locked():
            return
        self._watchdog_healthy = False
        if self.debug:
            print("Browser is being closed because chrom* closed", file=sys.stderr)
        await self.close()
        await asyncio.sleep(1)
        with warnings.catch_warnings():
            # ignore warnings here because
            # watchdog killing is last resort
            # and can leaves stuff in weird state
            warnings.filterwarnings("ignore", category=TempDirWarning)
            self.tmp_dir.clean()
            if self.tmp_dir.exists:
                self.tmp_dir.delete_manually()

    def __exit__(self, type, value, traceback):
        self.close()

    async def __aexit__(self, type, value, traceback):
        await self.close()

    # Basic synchronous functions
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

    # Better functions that require asynchronous
    async def create_tab(self, url="", width=None, height=None):
        if self.lock.locked():
            raise BrowserClosedError("create_tab() called on a closed browser.")
        if self.headless and (width or height):
            warnings.warn(
                "Width and height only work for headless chrome mode, they will be ignored.",
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
            raise RuntimeError("Could not create tab") from DevtoolsProtocolError(
                response,
            )
        target_id = response["result"]["targetId"]
        new_tab = Tab(target_id, self)
        self._add_tab(new_tab)
        await new_tab.create_session()
        return new_tab

    async def close_tab(self, target_id):
        if self.lock.locked():
            raise BrowserClosedError("close_tab() called on a closed browser")
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
            raise RuntimeError("Could not close tab") from DevtoolsProtocolError(
                response,
            )
        return response

    async def create_session(self):
        if self.lock.locked():
            raise BrowserClosedError("create_session() called on a closed browser")
        warnings.warn(
            "Creating new sessions on Browser() only works with some versions of Chrome, it is experimental.",
            ExperimentalFeatureWarning,
        )
        response = await self.browser.send_command("Target.attachToBrowserTarget")
        if "error" in response:
            raise RuntimeError("Could not create session") from DevtoolsProtocolError(
                response,
            )
        session_id = response["result"]["sessionId"]
        new_session = Session(self, session_id)
        self._add_session(new_session)
        return new_session

    async def populate_targets(self):
        if self.lock.locked():
            raise BrowserClosedError("populate_targets() called on a closed browser")
        response = await self.browser.send_command("Target.getTargets")
        if "error" in response:
            raise RuntimeError("Could not get targets") from Exception(
                response["error"],
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
                                file=sys.stderr,
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
            if debug:
                print("Starting run_print loop", file=sys.stderr)
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
        def check_error(result):
            e = result.exception()
            if e:
                self.close()
                if self.debug:
                    print(f"Error in run_read_loop: {e!s}", file=sys.stderr)
                if not isinstance(e, asyncio.CancelledError):
                    raise e

        async def read_loop():
            try:
                responses = await self.loop.run_in_executor(
                    self.executor,
                    self.pipe.read_jsons,
                    True,  # blocking argument to read_jsons
                    self.debug,  # debug argument to read_jsons
                )
                for response in responses:
                    error = self.protocol.get_error(response)
                    key = self.protocol.calculate_key(response)
                    if not self.protocol.has_id(response) and error:
                        raise DevtoolsProtocolError(response)
                    elif self.protocol.is_event(response):
                        event_session_id = response.get(
                            "sessionId",
                            "",
                        )
                        event_session = self.protocol.sessions[event_session_id]

                        subscriptions_futures = event_session.subscriptions_futures

                        ### THIS IS FOR SUBSCRIBE(repeating=True|False)
                        for query in list(event_session.subscriptions):
                            match = (
                                query.endswith("*")
                                and response["method"].startswith(query[:-1])
                            ) or (response["method"] == query)
                            if self.debug:
                                print(
                                    f"Checking subscription key: {query} against event method {response['method']}",
                                    file=sys.stderr,
                                )
                            if match:
                                self.loop.create_task(
                                    event_session.subscriptions[query][0](response),
                                )
                                if not event_session.subscriptions[query][1]:
                                    self.protocol.sessions[
                                        event_session_id
                                    ].unsubscribe(query)

                        ### THIS IS FOR SUBSCRIBE_ONCE (that's not clear from variable names)
                        for query, futures in list(subscriptions_futures.items()):
                            match = (
                                query.endswith("*")
                                and response["method"].startswith(query[:-1])
                            ) or (response["method"] == query)
                            if self.debug:
                                print(
                                    f"Checking subscription key: {query} against event method {response['method']}",
                                    file=sys.stderr,
                                )
                            if match:
                                for future in futures:
                                    if self.debug:
                                        print(
                                            f"Processing future {id(future)}",
                                            file=sys.stderr,
                                        )
                                    future.set_result(response)
                                    if self.debug:
                                        print(
                                            f"Future resolved with response {future}",
                                            file=sys.stderr,
                                        )
                                del event_session.subscriptions_futures[query]

                        ### Check for closed sessions
                        if response["method"] == "Target.detachedFromTarget":
                            session_closed = response["params"].get(
                                "sessionId",
                                "",
                            )
                            if session_closed == "":
                                continue  # browser closing anyway
                            target_closed = self._get_target_for_session(session_closed)
                            if target_closed:
                                target_closed._remove_session(session_closed)
                            _ = self.protocol.sessions.pop(session_closed, None)
                            if self.debug:
                                print(
                                    f"Use intern subscription key: 'Target.detachedFromTarget'. Session {session_closed} was closed.",
                                    file=sys.stderr,
                                )

                    elif key:
                        future = None
                        if key in self.futures:
                            if self.debug:
                                print(
                                    f"run_read_loop() found future for key {key}",
                                    file=sys.stderr,
                                )
                            future = self.futures.pop(key)
                        elif "error" in response:
                            raise DevtoolsProtocolError(response)
                        else:
                            raise RuntimeError(f"Couldn't find a future for key: {key}")
                        if error:
                            future.set_result(response)
                        else:
                            future.set_result(response)
                    else:
                        warnings.warn(
                            f"Unhandled message type:{response!s}",
                            UnhandledMessageWarning,
                        )
            except PipeClosedError:
                if self.debug:
                    print("PipeClosedError caught", file=sys.stderr)
                return
            f = self.loop.create_task(read_loop())
            f.add_done_callback(check_error)

        f = self.loop.create_task(read_loop())
        f.add_done_callback(check_error)

    def write_json(self, obj):
        self.protocol.verify_json(obj)
        key = self.protocol.calculate_key(obj)
        if self.loop:
            future = self.loop.create_future()
            self.futures[key] = future
            res = self.loop.run_in_executor(
                self.executor,
                self.pipe.write_json,
                obj,
            )  # ignore result

            def check_future(fut):
                if fut.exception():
                    if self.debug:
                        print(f"Write json future error: {fut!s}", file=sys.stderr)
                    if not future.done():
                        print("Setting future based on pipe error", file=sys.stderr)
                        future.set_exception(fut.exception())
                        print("Exception set", file=sys.stderr)
                    self.close()

            res.add_done_callback(check_future)
            return future
        else:
            self.pipe.write_json(obj)
            return key
