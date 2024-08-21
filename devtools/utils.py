import os
import json


def verify_json_id(pipe, json_list):
    to_chromium = os.read(pipe.read_to_chromium, 10000)
    json_chromium = json.load(to_chromium.decode("utf-8").split("\0"))
    for json_ in json_list:
        if json_chromium["id"] == json_["id"]:
            return json_
    raise ValueError("Your ID and the received ID are different")
