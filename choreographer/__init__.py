"""choreographer is a browser controller for python."""

from choreographer import protocol

from ._browser import Browser, BrowserClosedError, browser_which, get_browser_path
from ._channels.pipe import BlockWarning, PipeClosedError
from ._cli_utils import get_browser, get_browser_sync
from ._system_utils._tempfile import TempDirectory, TempDirWarning
from ._tab import Tab

__all__ = [
    "BlockWarning",
    "Browser",
    "BrowserClosedError",
    "PipeClosedError",
    "Tab",
    "TempDirWarning",
    "TempDirectory",
    "browser_which",
    "get_browser",
    "get_browser_path",
    "get_browser_sync",
    "protocol",
]
