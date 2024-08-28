import os
import sys
import json

class PipeClosedError(IOError):
    pass

class Pipe:
    def __init__(self, debug=False):
        self.read_from_chromium, self.write_from_chromium = list(os.pipe())
        self.read_to_chromium, self.write_to_chromium = list(os.pipe())
        self.debug = debug

    # TODO: accept already formed object
    def write_json(self, msg_id, method, params=None, session_id="", debug=None):
        if not debug: debug = self.debug
        if debug:
            print("write_json:", file=sys.stderr)
        message = {}
        if session_id:
            message["sessionId"] = session_id
        message["id"] = msg_id
        message["method"] = method
        if params:
            message["params"] = params

        encoded_message = json.dumps(message).encode() + b"\0"

        if debug:
            print(f">>>>>>>>>write: {encoded_message}", file=sys.stderr)
        os.write(self.write_to_chromium, encoded_message)

    def read_jsons(self, blocking=True, debug=None):
        if not debug:
            debug = self.debug
        if debug:
            print(
                f">>>>>>>>>read_jsons ({'blocking' if blocking else 'not blocking'}):",
                file=sys.stderr,
            )
        jsons = []
        os.set_blocking(self.read_from_chromium, blocking)
        try:
            raw_buffer = os.read(
                self.read_from_chromium, 10000
            )  # 10MB buffer, nbd, doesn't matter w/ this
            if not raw_buffer:
                raise PipeClosedError()
            while raw_buffer[-1] != 0:
                os.set_blocking(self.read_from_chromium, True)
                raw_buffer += os.read(self.read_from_chromium, 10000)
        except BlockingIOError:
            if debug:
                print(">>>>>>>>>BlockingIOError caught.", file=sys.stderr)
            return jsons
        if debug:
            print(f">>>>>>>>>read: {raw_buffer}", file=sys.stderr)
        for raw_message in raw_buffer.decode("utf-8").split("\0"):
            if raw_message:
                jsons.append(json.loads(raw_message))
        return jsons
