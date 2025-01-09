"""
choreographer is a browser controller for python.

choreographer is natively async, so while there are two main entrypoints:
classes `Browser` and `BrowserSync`, the sync version is very limited, functioning
as a building block.

See the main README for a quickstart.
"""

from ._browsers import (
    BrowserClosedError,
    BrowserFailedError,
    Chromium,
)
from ._channels import BlockWarning, ChannelClosedError
from ._cli_utils import get_chrome, get_chrome_sync
from ._sys_utils import (
    TmpDirectory,
    TmpDirWarning,
    browser_which,
    get_browser_path,
)
from .browser_sync import (
    BrowserSync,
    SessionSync,
    TabSync,
    TargetSync,
)

__all__ = [
    "BlockWarning",
    "BrowserClosedError",
    "BrowserFailedError",
    "BrowserSync",
    "ChannelClosedError",
    "Chromium",
    "SessionSync",
    "TabSync",
    "TargetSync",
    "TmpDirWarning",
    "TmpDirectory",
    "browser_which",
    "get_browser_path",
    "get_chrome",
    "get_chrome_sync",
]
