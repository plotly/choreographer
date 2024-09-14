import platform
import os
import sys
import subprocess
import tempfile
import warnings

from collections import OrderedDict

from .pipe import Pipe
from .protocol import Protocol
from .target import Target
from .session import Session
from .tab import Tab
from .system import which_browser

default_path = which_browser()


class Browser(Target):
    def __init__(
        self,
        path=None,
        headless=True,
        debug=False,
        debug_browser=None,
        loop=None,
    ):
        # Configuration
        self.headless = headless

        # Resources
        self.pipe = Pipe(debug=debug)
        self.loop = loop
        self.protocol = Protocol(self.pipe, loop=loop, debug=debug)

        # State
        self.tabs = OrderedDict()

        # Initializing
        super().__init__("0", self)  # NOTE: 0 can't really be used externally
        self.add_session(Session(self, ""))

        if platform.system() != "Windows":
            self.temp_dir = tempfile.TemporaryDirectory()
        else:
            self.temp_dir = tempfile.TemporaryDirectory(
                delete=False, ignore_cleanup_errors=True
            )

        if not debug_browser:  # false o None
            stderr = subprocess.DEVNULL
        elif debug_browser is True:
            stderr = None
        else:
            stderr = debug

        new_env = os.environ.copy()
        if not path:
            path = os.environ.get("BROWSER_PATH", None)
        if not path:
            path = default_path
        if path:
            new_env["BROWSER_PATH"] = path

        new_env["USER_DATA_DIR"] = str(self.temp_dir.name)
        if headless:
            new_env["HEADLESS"] = "--headless"  # unset if false

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
                env=new_env,
            )
        else:
            from .chrome_wrapper import open_browser
            self.subprocess = open_browser(to_chromium=self.pipe.read_to_chromium,
                                                   from_chromium=self.pipe.write_from_chromium,
                                                   stderr=stderr,
                                                   env=new_env)
        if not self.headless and self.loop:
            self.populate_targets()


    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        if platform.system() == "Windows":
            # maybe we don't need chrome_wrapper for windows because of how handles are needed
            # if we're not chaining process, this might not be necessary
            # otherwise, win behaves strangely in the face of signals, so call a command to kill the process instead
            # NB: chrome accepts being killed like this because it knows windows is a nightmare
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", str(self.subprocess.pid)]
            )  # this output should be handled better by where there is debug
            self.subprocess.wait(2)
        self.subprocess.terminate()
        self.subprocess.wait(2)
        self.subprocess.kill()
        try:
            self.temp_dir.cleanup()
        except Exception as e:  # TODO- handle specific errors
            print(str(e))

        # windows doesn't like python's default cleanup
        if platform.system() == "Windows":
            import stat
            import shutil

            def remove_readonly(func, path, excinfo):
                os.chmod(path, stat.S_IWUSR)
                func(path)

            try:
                shutil.rmtree(self.temp_dir.name, onexc=remove_readonly)
                del self.temp_dir
            except FileNotFoundError:
                pass
            except PermissionError:
                warnings.warn(
                    "The temporary directory could not be deleted, due to permission error, execution will continue."
                )
            except Exception as e:
                warnings.warn(
                        f"The temporary directory could not be deleted, execution will continue. {type(e)}: {e}"
                )

        self.pipe.close()

    def add_tab(self, tab):
        if not isinstance(tab, Tab):
            raise TypeError("tab must be an object of class Tab")
        self.tabs[tab.target_id] = tab

    def remove_tab(self, target_id):
        if isinstance(target_id, Tab):
            target_id = target_id.target_id
        del self.tabs[target_id]

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
        self.add_tab(new_tab)
        await new_tab.create_session()
        return new_tab

    async def close_tab(self, target_id):
        if not self.loop:
            raise RuntimeError(
                "There is no eventloop, or was not passed to browser. Cannot use async methods"
            )
        if isinstance(target_id, Target):
            target_id = target_id.target_id
        response = await self.send_command(
            command="Target.closeTarget",
            params={"targetId": target_id},
        )
        self.remove_tab(target_id)
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
        if not self.headless:
            raise ValueError("You must use this function with headless=False")
        elif not self.browser.loop:
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
                self.add_tab(new_tab)
                if self.debug:
                    print(f"The target {target_id} was added", file=sys.stderr)

    def get_tab(self):
        if self.tabs.values():
            return list(self.tabs.values())[0]
