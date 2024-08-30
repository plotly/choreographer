import json

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

    def run_output_thread(self, debug=False):
        print("Start run_output_thread() to improve debugging".center(6, "-"))

        def run_print(debug):
            while True:
                try:
                    json_list = self.pipe.read_jsons(debug=debug)
                    if json_list:
                        for json_ in json_list:
                            print(json.dumps(json_, indent=4))
                except PipeClosedError:
                    print("Pipe closed".center(10, "-"))
                    break

        thread_print = Thread(target=run_print, args=(debug,))
        thread_print.start()

    # we need to do something for errors
