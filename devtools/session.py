from .tab import Tab


class Session:
    def __init__(self, parent_tab, session_id):
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a string")
        if not isinstance(parent_tab, Tab):
            raise TypeError("parent must be a tab object")

        self.session_id = session_id
        self.message_id = 0
        self.parent_tab = parent_tab

    def send_command(self, command, params=None):
        current_id = self.message_id
        self.message_id += 1
        json_command = {
            "message_id": current_id,
            "method": command,
        }

        if self.session_id:
            json_command["session_id"] = self.session_id
        if params:
            json_command["params"] = params

        self.parent_connection.pipe.write_json(**json_command)
