import os
import sys
import json


class PipeClosedError(IOError):
    pass


class Pipe:
    def __init__(self):
        self.read_from_chromium, self.write_from_chromium = list(os.pipe())
        self.read_to_chromium, self.write_to_chromium = list(os.pipe())

    def write_json(
        self, message_id, method, params=None, session_id="", debug=False
    ):  # this should accept an objects not a string
        if params:
            message = {"id": message_id, "method": method, "params": params}
        else:
            message = {"id": message_id, "method": method}

        if session_id != "":
            message["sessionId"] = session_id
        
        if debug:
            print("You are using write_json()")
            print(f"This is the message: {message}")

        encoded_message = json.dumps(message).encode() + b"\0"

        os.write(self.write_to_chromium, encoded_message)

    def read_jsons(self, blocking=True, debug=False):
        if debug:
            print("Debug enabled", file=sys.stderr)
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
            return jsons
        if debug:
            print(raw_buffer, file=sys.stderr)  # noqa
        for raw_message in raw_buffer.decode("utf-8").split("\0"):
            if raw_message:
                jsons.append(json.loads(raw_message))
        return jsons
