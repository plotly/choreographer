"""A compilation of the errors available in choreographer."""

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
from .utils import TmpDirWarning

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
