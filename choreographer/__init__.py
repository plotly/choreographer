"""
choreographer is a browser controller for python.

choreographer is natively async, so while there are two main entrypoints:
classes `Browser` and `BrowserSync`, the sync version is very limited, functioning
as a building block.

See the main README for a quickstart.
"""

from ._browsers import (  # noqa: F401 unused import
    BrowserClosedError,
    BrowserFailedError,
    Chromium,
)
from ._channels import BlockWarning, ChannelClosedError  # noqa: F401 unused import
from ._cli_utils import get_chrome, get_chrome_sync  # noqa: F401 unused import
from ._sys_utils import (  # noqa: F401 unused import
    TmpDirectory,
    TmpDirWarning,
    browser_which,
    get_browser_path,
)
from .browser_sync import (  # noqa: F401 unused import
    BrowserSync,
    SessionSync,
    TabSync,
    TargetSync,
)

__all__ = [
    "BrowserSync",
    "SessionSync",
    "TabSync",
    "TargetSync",
    "Chromium",
    "BrowserClosedError",
    "BrowserFailedError",
    "ChannelClosedError",
    "BlockWarning",
    "TmpDirWarning",
    "get_chrome",
    "get_chrome_sync",
    "TmpDirectory",
    "browser_which",
    "get_browser_path",
]
