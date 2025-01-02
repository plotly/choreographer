"""choreographer is a browser controller for python."""

from ._browser import Browser, browser_which, get_browser_path
from ._cli_utils import get_browser, get_browser_sync
from ._devtools_protocol_layer._session import Session
from ._devtools_protocol_layer._target import Target
from ._system_utils._tempfile import TempDirectory, TempDirWarning
from ._tab import Tab

__all__ = [
    "Browser",
    "Session",
    "Tab",
    "Target",
    "TempDirWarning",  # just for testing?
    "TempDirectory",  # just for testing?
    "browser_which",
    "get_browser",
    "get_browser_path",
    "get_browser_sync",
]
