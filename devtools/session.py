import json
import uuid


class Session:
    def __init__(self, parent, session_id=str(uuid.uuid4())):
        if isinstance(session_id, str):
            self.session_id = session_id
        else:
            raise TypeError("You must use an string object for session_id")

        self.event_cbs = {}
        self.message_cbs = {}
        self.message_id = 0
        self.parent_connection = parent

    def send_command(self, command, params=None, cb=None):
        if cb and not callable(cb):
            raise TypeError("The arg that you use, is not able at cb")
        if not isinstance(command, str):
            raise TypeError("You must use an string for the command parameter")

        if cb:
            self.message_cbs[self.message_id] = cb

        json_command = {
            "id": self.message_id,
            "method": command,
        }

        if self.session_id != "":
            json_command["session_id"] = self.session_id

        if params:
            json_command["params"] = params

            self.parent_connection.pipe.write_json(
                message_id=json_command["id"],
                method=json_command["method"],
                params=json_command["params"],
                session_id=self.session_id,
            )
        else:
            self.parent_connection.pipe.write_json(
                message_id=json_command["id"],
                method=json_command["method"],
                session_id=self.session_id,
            )

        self.message_id += 1

        return json.dumps(json_command)
