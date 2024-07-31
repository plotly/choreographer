import json


class Session:
    def __init__(self):
        pass

    def send_command(self, command, params):
        if not isinstance(command, str):
            raise TypeError("You must use an string for the command parameter")
        json_command = {"method": command, "params": params}
        return json.dumps(json_command)
