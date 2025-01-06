"""choreographer.protocol provides classes and tools for Chrome Devtools Protocol."""

from ._session import Session
from ._target import Target


class DevtoolsProtocolError(Exception):
    """."""

    def __init__(self, response):
        """."""
        super().__init__(response)
        self.code = response["error"]["code"]
        self.message = response["error"]["message"]


class MessageTypeError(TypeError):
    """."""

    def __init__(self, key, value, expected_type):
        """."""
        value = type(value) if not isinstance(value, type) else value
        super().__init__(
            f"Message with key {key} must have type {expected_type}, not {value}.",
        )


class MissingKeyError(ValueError):
    """."""

    def __init__(self, key, obj):
        """."""
        super().__init__(
            f"Message missing required key/s {key}. Message received: {obj}",
        )


class ExperimentalFeatureWarning(UserWarning):
    """."""


__all__ = [
    "DevtoolsProtocolError",
    "ExperimentalFeatureWarning",
    "MessageTypeError",
    "MissingKeyError",
    "Session",
    "Target",
]
