"""
choreographer is a browser controller for python.

choreographer is natively async, so while there are two main entrypoints:
classes `Browser` and `BrowserSync`, the sync version is very limited, functioning
as a building block.
"""

from choreographer import protocol

from ._browser_sync import BrowserClosedError, BrowserSync, TabSync
from ._channels import BlockWarning, ChannelClosedError
from ._cli_utils import get_browser, get_browser_sync
from ._sys_utils import TempDirectory, TempDirWarning, browser_which, get_browser_path

__all__ = [
    "BlockWarning",
    "BrowserClosedError",
    "BrowserSync",
    "ChannelClosedError",
    "TabSync",
    "TempDirWarning",
    "TempDirectory",
    "browser_which",
    "get_browser",
    "get_browser_path",
    "get_browser_sync",
    "protocol",
]
