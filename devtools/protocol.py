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

    def verify_json_id(self, json_list, message_id, session_id=None, target_id=None):
        for json_ in json_list:
            if message_id in json_ and message_id == json["id"]:
                if session_id in json_ and session_id == json["sessionId"]:
                    return json_
                elif target_id in json_:
                    if (
                        "results" in json_
                        and target_id == json_["results"]["target_id"]
                    ) or (target_id == json_["target_id"]):
                        return json_
        return None

    def verify_target_id(self, json_obj):
        if "result" in json_obj and "targetId" in json_obj["result"]:
            return json_obj["result"]["targetId"]
        else:
            if "targetId" in json_obj["params"]:
                return json_obj["params"]["targetId"]
            elif "targetInfo" in json_obj["params"]:
                return json_obj["params"]["targetInfo"]["targetId"]

    def verify_session_id(self, json_obj):
        if "sessionId" in json_obj:
            return json_obj["sessionId"]
        elif "result" in json_obj and "sessionId" in json_obj["result"]:
            return json_obj["result"]["sessionId"]
        else:
            return json_obj["params"]["sessionId"]

    def verify_json_list(
        self, json_list, verify_function, verify_boolean=False, debug=False
    ):
        for json_ in json_list:
            self.verify_json_error(json_)
            verify_boolean = verify_function(json_)
            if verify_boolean:
                json_obj = json_
                if debug:
                    print(f">>>>>This is the json_obj: {json_obj}")
                return json_obj

    def verify_json_error(self, json):
        if "error" in json:
            if "id" in json:
                raise ValueError(
                    f"The command with id {json["id"]} raise an error. Error code: {json["error"]["code"]}. {json["error"]["message"]}"
                )
            else:
                raise ValueError(
                    f"Error code: {json["error"]["code"]}. {json["error"]["message"]}"
                )
