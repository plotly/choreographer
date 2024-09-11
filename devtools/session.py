import inspect


class Session:
    def __init__(self, parent_target, session_id):
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a string")
        if not hasattr(parent_target, "target_id"):
            raise TypeError("parent must be a target object")
        # Resources
        self.parent_target = parent_target

        # State
        self.session_id = session_id
        self.message_id = 0
        self.suscribe_dict = {}

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

        possible_future = self.parent_target.protocol.write_json(json_command)
        if possible_future: return possible_future

        return {"session_id": self.session_id, "message_id": current_id}

    def suscribe(self, string, callback):
        if string in self.suscribe_dict:
            raise ValueError("This value is in suscribe_dict")
        if not inspect.isawaitable(callback):
            raise TypeError("You may use a callback in this method")
        self.suscribe_dict[string] = callback

    def unsuscrib(self, string):
        if string in self.subscribe_dict:
            self.suscribe_dict.pop(string)
        else:
            raise ValueError("The String is not in suscribe_dict")
