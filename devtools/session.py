from .target import Target


class Session:
    def __init__(self, parent_target, session_id):
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a string")
        if not isinstance(parent_target, Target):
            raise TypeError("parent must be a target object")

        self.session_id = session_id
        self.message_id = 0
        self.parent_target = parent_target

    def send_command(self, command, params=None):
        current_id = self.message_id
        self.message_id += 1
        json_command = {
            "id": current_id,
            "method": command,
        }

        if self.session_id:
            json_command["sessionId"] = self.session_id
        if params:
            json_command["params"] = params

        self.parent_target.protocol.write_json(json_command)

        return {"session_id":self.session_id, "message_id": current_id}
