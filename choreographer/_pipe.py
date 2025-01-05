import os
import platform
import sys
import warnings
from threading import Lock

import simplejson

with_block = bool(sys.version_info[:3] >= (3, 12) or platform.system() != "Windows")


class PipeClosedError(IOError):
    pass


class BlockWarning(UserWarning):
    pass


class MultiEncoder(simplejson.JSONEncoder):
    """Special json encoder for numpy types."""

    def default(self, obj):
        if hasattr(obj, "dtype") and obj.dtype.kind == "i" and obj.shape == ():
            return int(obj)
        elif hasattr(obj, "dtype") and obj.dtype.kind == "f" and obj.shape == ():
            return float(obj)
        elif hasattr(obj, "dtype") and obj.shape != ():
            return obj.tolist()
        elif hasattr(obj, "isoformat"):
            return obj.isoformat()
        return simplejson.JSONEncoder.default(self, obj)


# whoever is setting up the process is going to look for:
# we're going to look for self.stdout_redirection
# we're going to look for self.stdin_redirection
class Pipe:
    def __init__(self, *, debug=False, json_encoder=MultiEncoder):
        # this is where pipe listens (from browser)
        # so pass the write to browser
        self.read_from_browser, self.write_from_browser = list(os.pipe())

        # this is where pipe writes (to browser)
        # so pass the read to browser
        self.read_to_browser, self.write_to_browser = list(os.pipe())

        # Popen will write stdout of wrapper to write_from_browser
        # which is duping expected fd (3?) to stdout
        self.stdout_redirection = self.write_from_browser
        # Popen will read read_to_browser into stdin of wrapper
        # which dupes stdin to expected fd (4?)
        self.stdin_redirection = self.read_to_browser
        # these won't be used on windows directly
        # but we let the process manager handle platform idiosyncrasies

        self.debug = debug
        self.json_encoder = json_encoder

        # this is just a convenience to prevent multiple shutdowns
        self.shutdown_lock = Lock()

    def serialize(self, obj):
        message = simplejson.dumps(
            obj,
            ensure_ascii=False,
            ignore_nan=True,
            cls=self.json_encoder,
        )
        return message.encode("utf-8") + b"\0"

    def deserialize(self, message):
        return simplejson.loads(message)

    def write_json(self, obj, debug=None):
        if self.shutdown_lock.locked():
            raise PipeClosedError
        if not debug:
            debug = self.debug
        if debug:
            print(f"write_json: {obj}", file=sys.stderr)
        encoded_message = self.serialize(obj)
        if debug:
            print(f"write_json: {encoded_message}", file=sys.stderr)
        try:
            os.write(self.write_to_browser, encoded_message)
        except OSError as e:
            self.close()
            raise PipeClosedError from e
        if debug:
            print("wrote_json.", file=sys.stderr)

    def read_jsons(self, *, blocking=True, debug=None):  # noqa: PLR0912, C901 branches, complexity
        if self.shutdown_lock.locked():
            raise PipeClosedError
        if not with_block and not blocking:
            warnings.warn(  # noqa: B028
                "Windows python version < 3.12 does not support non-blocking",
                BlockWarning,
            )
        if not debug:
            debug = self.debug
        if debug:
            print(
                f"read_jsons ({'blocking' if blocking else 'not blocking'}):",
                file=sys.stderr,
            )
        jsons = []
        try:
            if with_block:
                os.set_blocking(self.read_from_browser, blocking)
        except OSError as e:
            self.close()
            raise PipeClosedError from e
        try:
            raw_buffer = None  # if we fail in read, we already defined
            raw_buffer = os.read(
                self.read_from_browser,
                10000,
            )  # 10MB buffer, nbd, doesn't matter w/ this
            if not raw_buffer or raw_buffer == b"{bye}\n":
                # we seem to need {bye} even if chrome closes NOTE
                if debug:
                    print("read_jsons pipe was closed, raising", file=sys.stderr)
                raise PipeClosedError
            while raw_buffer[-1] != 0:
                # still not great, return what you have
                if with_block:
                    os.set_blocking(self.read_from_browser, True)
                raw_buffer += os.read(self.read_from_browser, 10000)
        except BlockingIOError:
            if debug:
                print("read_jsons: BlockingIOError caught.", file=sys.stderr)
            return jsons
        except OSError as e:
            self.close()
            if debug:
                print(f"caught OSError in read() {e!s}", file=sys.stderr)
            if not raw_buffer or raw_buffer == b"{bye}\n":
                raise PipeClosedError from e
            # this could be hard to test as it is a real OS corner case
        decoded_buffer = raw_buffer.decode("utf-8")
        if debug:
            print(decoded_buffer, file=sys.stderr)
        for raw_message in decoded_buffer.split("\0"):
            if raw_message:
                try:
                    jsons.append(self.deserialize(raw_message))
                except simplejson.decoder.JSONDecodeError as e:
                    if debug:
                        print(
                            f"Problem with {raw_message} in json: {e}",
                            file=sys.stderr,
                        )
                if debug:
                    # This debug is kinda late but the jsons package
                    # helps with decoding, since JSON optionally
                    # allows escaping unicode characters, which chrome does (oof)
                    print(f"read_jsons: {jsons[-1]}", file=sys.stderr)
        return jsons

    def _unblock_fd(self, fd):
        try:
            if with_block:
                os.set_blocking(fd, False)
        except BaseException as e:  # noqa: BLE001 OS errors are not consistent, catch blind
            # also, best effort.
            if self.debug:
                print(f"Expected error unblocking {fd!s}: {e!s}", file=sys.stderr)

    def _close_fd(self, fd):
        try:
            os.close(fd)
        except BaseException as e:  # noqa: BLE001 OS errors are not consistent, catch blind
            # also, best effort.
            if self.debug:
                print(f"Expected error closing {fd!s}: {e!s}", file=sys.stderr)

    def _fake_bye(self):
        self._unblock_fd(self.write_from_browser)
        try:
            os.write(self.write_from_browser, b"{bye}\n")
        except BaseException as e:  # noqa: BLE001 OS errors are not consistent, catch blind
            # also, best effort.
            if self.debug:
                print(
                    f"Caught expected error in self-wrte bye: {e!s}",
                    file=sys.stderr,
                )

    def close(self):
        if self.shutdown_lock.acquire(blocking=False):
            if platform.system() == "Windows":
                self._fake_bye()
            self._unblock_fd(self.write_from_browser)
            self._unblock_fd(self.read_from_browser)
            self._unblock_fd(self.write_to_browser)
            self._unblock_fd(self.read_to_browser)
            self._close_fd(self.write_to_browser)  # no more writes
            self._close_fd(self.write_from_browser)  # we're done with writes
            self._close_fd(self.read_from_browser)  # no more attempts at read
            self._close_fd(self.read_to_browser)
