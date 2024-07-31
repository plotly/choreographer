import json


class Session:
    def __init__(self, sessionId):
        if isinstance(sessionId, str):
            self._sessionId = sessionId
        else:
            raise TypeError("You must use an string object for sessionId")

        self._messageId = 0

    def send_command(self, command, params):
        if not isinstance(command, str):
            raise TypeError("You must use an string for the command parameter")
        json_command = {"method": command, "params": params}
        return json.dumps(json_command)
