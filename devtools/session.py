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
        self.subscriptions = {}

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
        if possible_future:
            return possible_future

        return {"session_id": self.session_id, "message_id": current_id}

    def subscribe(self, string, callback, repeating):
        if string in self.subscriptions:
            raise ValueError("You are already subscribed to this string, duplicate subscriptions are not allowed.")
        else:
            self.subscriptions[string] = (callback, repeating)

    def unsubscribe(self, string):
        if string not in self.subscriptions:
            raise ValueError("Cannot unsubscribe as string is not present in subscriptions")
        self.subscriptions.remove(string)
