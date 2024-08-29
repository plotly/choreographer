import json
from threading import Thread
from .pipe import PipeClosedError


def verify_json_id(json_list, message_id, session_id=None, target_id=None):
    for json_ in json_list:
        if message_id in json_ and message_id == json["id"]:
            if session_id in json_ and session_id == json["sessionId"]:
                return json_
            elif target_id in json_:
                if (
                    "results" in json_ and target_id == json_["results"]["target_id"]
                ) or (target_id == json_["target_id"]):
                    return json_
    return None


def verify_target_id(json_obj):
    if "result" in json_obj and "targetId" in json_obj["result"]:
        return json_obj["result"]["targetId"]
    else:
        if "targetId" in json_obj["params"]:
            return json_obj["params"]["targetId"]
        elif "targetInfo" in json_obj["params"]:
            return json_obj["params"]["targetInfo"]["targetId"]


def verify_session_id(json_obj):
    if "sessionId" in json_obj:
        return json_obj["sessionId"]
    elif "result" in json_obj and "sessionId" in json_obj["result"]:
        return json_obj["result"]["sessionId"]
    else:
        return json_obj["params"]["sessionId"]


def verify_json_list(json_list, verify_function, verify_boolean=False, debug=False):
    for json_ in json_list:
        verify_json_error(json_)
        verify_boolean = verify_function(json_)
        if verify_boolean:
            json_obj = json_
            if debug:
                print(f">>>>>This is the json_obj: {json_obj}")
            return json_obj


def verify_json_error(json):
    if "error" in json:
        raise ValueError(
            f"Error code: {json["error"]["code"]}. {json["error"]["message"]}"
        )


def run_output_thread(pipe_obj, blocking=True, debug=None):
    def run_print(pipe_obj, blocking, debug):
        while True:
            try:
                json_list = pipe_obj.read_jsons(blocking, debug)
                if json_list:
                    print("JSON list:", json_list)
            except PipeClosedError:
                print("Pipe closed".center(10, "--"))
                break
    thread_print = Thread(target=run_print, args=(pipe_obj, blocking, debug))
    thread_print.start()