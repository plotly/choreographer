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

    def send_command(self, command, params=None, cb=None, session_id=None, debug=False):
        if cb and not callable(cb):
            raise TypeError("The arg that you use, is not able at cb")
        if not isinstance(command, str):
            raise TypeError("You must use an string for the command parameter")

        if cb:
            self.message_cbs[self.message_id] = cb

        json_command = {
            "message_id": self.message_id,
            "method": command,
        }

        if session_id:
            json_command["session_id"] = session_id
        elif self.session_id != "":
            json_command["session_id"] = self.session_id

        if params:
            json_command["params"] = params
        
        if debug:
            json_command["debug"] = debug
            print(f"The json created for send_command() is: {json_command}")

        self.parent_connection.pipe.write_json(**json_command)

        self.message_id += 1
