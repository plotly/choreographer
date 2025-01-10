"""A compilation of the errors available in choreographer."""

from ._tmpfile import TmpDirWarning
from .browsers import (
    BrowserClosedError,
    BrowserFailedError,
)
from .channels import BlockWarning, ChannelClosedError
from .protocol import (
    DevtoolsProtocolError,
    ExperimentalFeatureWarning,
    MessageTypeError,
    MissingKeyError,
)

__all__ = [
    "BlockWarning",
    "BrowserClosedError",
    "BrowserFailedError",
    "ChannelClosedError",
    "DevtoolsProtocolError",
    "ExperimentalFeatureWarning",
    "MessageTypeError",
    "MissingKeyError",
    "TmpDirWarning",
]
