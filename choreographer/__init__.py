"""
choreographer is a browser controller for python.

choreographer is natively async, so while there are two main entrypoints:
classes `Browser` and `BrowserSync`, the sync version is very limited, functioning
as a building block.
"""

from choreographer import protocol

from ._browser import Browser, BrowserClosedError
from ._channels.pipe import BlockWarning, PipeClosedError
from ._cli_utils import get_browser, get_browser_sync
from ._sys_utils import TempDirectory, TempDirWarning, browser_which, get_browser_path
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
