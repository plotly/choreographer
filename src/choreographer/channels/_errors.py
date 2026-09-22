from __future__ import annotations


class BlockWarning(UserWarning):
    """A warning for when block modification operations used on incompatible OS."""


class ChannelClosedError(IOError):
    """An error to throw when the channel has closed from either end or error."""


class JSONError(RuntimeError):
    """Another JSONError."""


class MessageTooLargeError(RuntimeError):
    """
    An error for when a message won't fit in the browser's receive buffer.

    The browser closes the connection outright if we write a message bigger
    than its buffer, so we refuse to write it and raise this instead.
    """

    size: int
    """The size, in bytes, of the message we refused to write."""
    max_size: int
    """The largest message the browser will accept."""
    payload: str | None
    """
    The serialized message.

    It is kept so that callers who know how to break the message up can
    reuse it instead of serializing all over again. It is deliberately left
    out of the error text: it can be hundreds of megabytes.
    """

    def __init__(self, size: int, max_size: int, payload: str | None = None) -> None:
        """
        Construct a MessageTooLargeError.

        Args:
            size: the size of the message in bytes.
            max_size: the largest message the browser will accept.
            payload: the serialized message, if the caller should have it.

        """
        super().__init__(
            f"Message is {size} bytes, which is over the browser's "
            f"{max_size} byte limit. It was not sent.",
        )
        self.size = size
        self.max_size = max_size
        self.payload = payload
