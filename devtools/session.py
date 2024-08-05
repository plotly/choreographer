import json


class Session:
    def __init__(self, session_id):
        if isinstance(session_id, str):
            self.session_id = session_id
        else:
            raise TypeError("You must use an string object for session_id")

        self.event_cbs = {}
        self.message_cbs = {}
        self.message_id = 0

    def send_command(self, command, params, cb=None):
        if cb and not callable(cb):
            raise TypeError("The arg that you use, is not able at cb")
        if not isinstance(command, str):
            raise TypeError("You must use an string for the command parameter")

        self.message_cbs[self.message_id] = cb

        json_command = {
            "method": command,
            "params": params,
            "Id": self.message_id,
            "message_cbs": self.message_cbs,
        }
        self.message_id = +1
        return json.dumps(json_command)
