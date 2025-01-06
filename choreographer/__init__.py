"""
choreographer is a browser controller for python.

choreographer is natively async, so while there are two main entrypoints:
classes `Browser` and `BrowserSync`, the sync version is very limited, functioning
as a building block.
"""

from ._browser_sync import (  # noqa: F401 unused import
    BrowserSync,
    SessionSync,
    TabSync,
    TargetSync,
)
from ._browsers import (  # noqa: F401 unused import
    BrowserClosedError,
    BrowserFailedError,
    Chromium,
)
from ._channels import BlockWarning, ChannelClosedError  # noqa: F401 unused import
from ._cli_utils import get_browser, get_browser_sync  # noqa: F401 unused import
from ._sys_utils import (  # noqa: F401 unused import
    TmpDirectory,
    TmpDirWarning,
    browser_which,
    get_browser_path,
)

_sync_api = [
    "BrowserSync",
    "SessionSync",
    "TabSync",
    "TargetSync",
]

_browser_impls = [
    "Chromium",
]

_errors = [
    "BrowserClosedError",
    "BrowserFailedError",
    "ChannelClosedError",
    "BlockWarning",
    "TmpDirWarning",
]

_utils = [
    "get_browser",
    "get_browser_sync",
    "TmpDirectory",
    "browser_which",
    "get_browser_path",
]

__all__ = [  # noqa: PLE0604 non-string in all
    *_sync_api,
    *_browser_impls,
    *_errors,
    *_utils,
]
