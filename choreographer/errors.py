"""A compilation of the errors available in choreographer."""

from ._brokers._async import UnhandledMessageWarning
from .browsers import (
    BrowserClosedError,
    BrowserFailedError,
    ChromeNotFoundError,
)
from .channels import BlockWarning, ChannelClosedError
from .protocol import (
    DevtoolsProtocolError,
    ExperimentalFeatureWarning,
    MessageTypeError,
    MissingKeyError,
)
from .utils import TmpDirWarning

__all__ = [
    "BlockWarning",
    "BrowserClosedError",
    "BrowserFailedError",
    "ChannelClosedError",
    "ChromeNotFoundError",
    "DevtoolsProtocolError",
    "ExperimentalFeatureWarning",
    "MessageTypeError",
    "MissingKeyError",
    "TmpDirWarning",
    "UnhandledMessageWarning",
]
