import os
import json


def verify_json_id(json_list, message_id, session_id=None):
    for json_ in json_list:
        if message_id in json_ and message_id == json["id"]:
            if session_id in json_ and session_id == json["sessionId"]:
                return json_


def verify_json_error(json):
    if "error" in json:
        raise ValueError(
            f"Error code: {json["error"]["code"]}. {json["error"]["message"]}"
        )
