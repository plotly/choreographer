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
        self, path=default_path, headless=True, debug=False, debug_browser=None, loop=None
    ):
        if path is None:
            raise ValueError("You must specify a path")
        self.headless = headless
        self.pipe = Pipe(debug=debug)
        self.loop = loop
        self.protocol = Protocol(self.pipe, loop=loop, debug=debug)
        super().__init__("0", self)  # TODO not sure about target id "0"
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
        new_env["CHROMIUM_PATH"] = str(path)
        new_env["USER_DATA_DIR"] = str(self.temp_dir.name)
        if headless:
            new_env["HEADLESS"] = "--headless"  # unset if false

        win_only = {}
        if platform.system() == "Windows":
            win_only = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}

        proc = subprocess.Popen(
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
            **win_only,
        )
        self.subprocess = proc
        self.tabs = OrderedDict()

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
            except PermissionError:
                warnings.warn(
                    "The temporary directory could not be deleted, but execution will continue."
                )
            except Exception:
                warnings.warn(
                    "The temporary directory could not be deleted, but execution will continue."
                )

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
            raise RuntimeError("There is no eventloop, or was not passed to browser. Cannot use async methods")
        if self.headless and (width or height):
            warnings.warn("Width and height only work for headless chrome mode, they will be ignored")
            width=None
            height=None
        params = dict(url=url)
        if width: params["width"] = width
        if height: params["height"] = height

        response = await self.browser.send_command("Target.createTarget",
                                                  params=params)
        if "error" in response:
            raise RuntimeError("Could not create tab") from Exception(response["error"])
        target_id = response["result"]["targetId"]
        new_tab = Tab(target_id, self)
        self.add_tab(new_tab)
        await new_tab.create_session()
        return new_tab

    async def close_session(self, target):
        if not self.browser.loop:
            raise RuntimeError(
                "There is no eventloop, or was not passed to browser. Cannot use async methods"
            )
        if isinstance(target, Tab):
            target_id = target.target_id
        response = await self.browser.send_command(
            command="Target.closeTarget",
            params={"targetId": target_id},
        )
        error = self.protocol.get_error(response)
        if error:
            raise RuntimeError("Could not close tab") from Exception(error)
        print(f"The tab {target_id} has been closed")
        self.remove_tab(target)
        return response
