import json


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


def verify_json_error(json):
    if "error" in json:
        raise ValueError(
            f"Error code: {json["error"]["code"]}. {json["error"]["message"]}"
        )
