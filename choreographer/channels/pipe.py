"""Provides a channel based on operating system file pipes."""

from __future__ import annotations

import os
import platform
import sys
import warnings
from threading import Lock
from typing import TYPE_CHECKING

import logistro

from . import _wire as wire
from ._errors import BlockWarning, ChannelClosedError, JSONError

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any

    from choreographer.protocol import BrowserResponse

_with_block = bool(sys.version_info[:3] >= (3, 12) or platform.system() != "Windows")

_logger = logistro.getLogger(__name__)


# if we're a pipe we expect these public attributes
class Pipe:
    """Defines an operating system pipe."""

    from_external_to_choreo: int
    """Consumers need this, it is the channel the browser uses to talk to choreo."""
    from_choreo_to_external: int
    """Consumers needs this, it is the channel choreo writes to the browser on."""
    shutdown_lock: Lock
    """Once this is locked, the pipe is closed and can't be reopened."""

    def __init__(self) -> None:
        """Construct a pipe using os functions."""
        # This is where pipe listens (from browser)
        # So pass the write to browser
        self._read_from_browser, self._write_from_browser = list(os.pipe())

        # This is where pipe writes (to browser)
        # So pass the read to browser
        self._read_to_browser, self._write_to_browser = list(os.pipe())

        # Popen will write stdout of wrapper to this (dupping 4)
        # Browser will write directly to this if not using wrapper
        self.from_external_to_choreo = self._write_from_browser
        # Popen will read this into stdin of wrapper (dupping 3)
        # Browser will read directly from this if not using wrapper
        # which dupes stdin to expected fd (4?)
        self.from_choreo_to_external = self._read_to_browser
        # These won't be used on windows directly, they'll be t-formed to
        # windows-style handles. But let another layer handle that.

        # this is just a convenience to prevent multiple shutdowns
        self.shutdown_lock = Lock()  # should be private

    def write_json(self, obj: Mapping[str, Any]) -> None:
        """
        Send one json down the pipe.

        Args:
            obj: any python object that serializes to json.

        """
        if self.shutdown_lock.locked():
            raise ChannelClosedError
        encoded_message = wire.serialize(obj) + b"\0"
        _logger.debug2(f"Writing: {encoded_message}")
        try:
            os.write(self._write_to_browser, encoded_message)
        except OSError as e:
            self.close()
            raise ChannelClosedError from e

    def read_jsons(  # noqa: PLR0912, C901 branches, complexity
        self,
        *,
        blocking: bool = True,
    ) -> Sequence[BrowserResponse]:
        """
        Read from the pipe and return one or more jsons in a list.

        Args:
            blocking: The read option can be set to block or not.

        Returns:
            A list of jsons.

        """
        if self.shutdown_lock.locked():
            raise ChannelClosedError
        if not _with_block and not blocking:
            warnings.warn(  # noqa: B028
                "Windows python version < 3.12 does not support non-blocking",
                BlockWarning,
            )
        jsons: list[BrowserResponse] = []
        try:
            if _with_block:
                os.set_blocking(self._read_from_browser, blocking)
        except OSError as e:
            self.close()
            raise ChannelClosedError from e
        try:
            raw_buffer = None  # if we fail in read, we already defined
            raw_buffer = os.read(
                self._read_from_browser,
                10000,
            )  # 10MB buffer, nbd, doesn't matter w/ this
            _logger.debug2(f"Read: {raw_buffer}")
            if not raw_buffer or raw_buffer == b"{bye}\n":
                # we seem to need {bye} even if chrome closes NOTE
                raise ChannelClosedError
            while raw_buffer[-1] != 0:
                # still not great, return what you have
                if _with_block:
                    os.set_blocking(self._read_from_browser, True)
                raw_buffer += os.read(self._read_from_browser, 10000)
                _logger.debug2(f"Read: {raw_buffer}")
        except BlockingIOError:
            return jsons
        except OSError as e:
            self.close()
            if not raw_buffer or raw_buffer == b"{bye}\n":
                raise ChannelClosedError from e
            # this could be hard to test as it is a real OS corner case
        decoded_buffer = raw_buffer.decode("utf-8")
        for raw_message in decoded_buffer.split("\0"):
            if raw_message:
                try:
                    jsons.append(wire.deserialize(raw_message))
                except JSONError:
                    _logger.exception("JSONError decoding message.")
        return jsons

    def _unblock_fd(self, fd: int) -> None:
        try:
            if _with_block:
                os.set_blocking(fd, False)
        except BaseException:  # noqa: BLE001, S110 OS errors are not consistent, catch blind + pass
            pass

    def _close_fd(self, fd: int) -> None:
        try:
            os.close(fd)
        except BaseException:  # noqa: BLE001, S110 OS errors are not consistent, catch blind + pass
            pass

    def _fake_bye(self) -> None:
        self._unblock_fd(self._write_from_browser)
        try:
            os.write(self._write_from_browser, b"{bye}\n")
        except BaseException:  # noqa: BLE001, S110 OS errors are not consistent, catch blind + pass
            pass

    def close(self) -> None:
        """Close the pipe."""
        if self.shutdown_lock.acquire(blocking=False):
            if platform.system() == "Windows":
                self._fake_bye()
            self._unblock_fd(self._write_from_browser)
            self._unblock_fd(self._read_from_browser)
            self._unblock_fd(self._write_to_browser)
            self._unblock_fd(self._read_to_browser)
            self._close_fd(self._write_to_browser)  # no more writes
            self._close_fd(self._write_from_browser)  # we're done with writes
            self._close_fd(self._read_from_browser)  # no more attempts at read
            self._close_fd(self._read_to_browser)
