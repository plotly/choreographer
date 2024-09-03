import json
import sys

from .pipe import PipeClosedError
from threading import Thread


class Protocol:
    def __init__(self, browser_pipe):
        self.pipe = browser_pipe

    def write_json(self, obj):
        n_keys = 0
        if "id" in obj and "method" in obj:
            n_keys += 2
        else:
            raise RuntimeError("Each message object must contain an id and method key")

        if "params" in obj:
            n_keys += 1
        if "sessionId" in obj:
            n_keys += 1

        if len(obj.keys()) != n_keys:
            raise RuntimeError(
                "Message objects must have id and method keys, and may have params and sessionId keys"
            )

        self.pipe.write_json(obj)

    def verify_response(self, response, session_id, message_id):
        if "session_id" not in response and session_id == "":
            pass
        elif "session_id" in response and response["session_id"] == session_id:
            pass
        else:
            return False

        if "id" in response and str(response["id"]) == str(message_id):
            pass
        else:
            return False
        return True

    def has_id(self, response):
        return "id" in response

    def get_targetId(self, response):
        if "result" in response and "targetId" in response["result"]:
            return response["result"]["targetId"]
        else:
            if "targetId" in response["params"]:
                return response["params"]["targetId"]
            elif "targetInfo" in response["params"]:
                return response["params"]["targetInfo"]["targetId"]

    def get_sessionId(self, response):
        if "sessionId" in response:
            return response["sessionId"]
        elif "result" in response and "sessionId" in response["result"]:
            return response["result"]["sessionId"]
        else:
            return response["params"]["sessionId"]

    def get_error(self, response):
        if "error" in response:
            return response["error"]
        else:
            return None

    def run_output_thread(self, debug=False):
        def run_print(debug):
            while True:
                try:
                    responses = self.pipe.read_jsons(debug=debug)
                    for response in responses:
                        print(json.dumps(response, indent=4))
                except PipeClosedError:
                    print("Pipe closed", file=sys.stderr)
                    break

        Thread(target=run_print, args=(debug,)).start()

