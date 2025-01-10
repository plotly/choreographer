"""
choreographer is a browser controller for python.

choreographer is natively async, so while there are two main entrypoints:
classes `Browser` and `BrowserSync`, the sync version is very limited, functioning
as a building block.

See the main README for a quickstart.
"""

from . import browsers, channel, cli, errors, protocol, utils
from .browser_sync import (
    BrowserSync,
    TabSync,
)
from .cli import get_chrome, get_chrome_sync
from .utils import (
    get_browser_path,
)

__all__ = [
    "BrowserSync",
    "TabSync",
    "browsers",
    "channel",
    "cli",
    "errors",
    "get_browser_path",
    "get_chrome",
    "get_chrome_sync",
    "protocol",
    "utils",
]
