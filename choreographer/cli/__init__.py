"""cli provides some tools that are used on the commandline (and to download chrome)."""

from ._cli_utils_no_qa import diagnose
from .cli import (
    get_chrome,
    get_chrome_cli,
    get_chrome_download_path,
    get_chrome_sync,
)

__all__ = [
    "diagnose",
    "get_chrome",
    "get_chrome_cli",
    "get_chrome_download_path",
    "get_chrome_sync",
]
