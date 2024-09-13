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
            if self.parent_target.protocol.debug:
                print("Waiting Future in send_command")
            return possible_future

        return {"session_id": self.session_id, "message_id": current_id}

    def subscribe(self, string, callback, repeating):
        if string in self.subscriptions:
            raise ValueError("This String was allready in subscriptions")
        else:
            self.subscriptions[string] = (callback, repeating)
            if self.parent_target.protocol.debug:
                print(
                    f"Subscribe to {self.session_id} the key-value: {string} and ({callback} - {repeating})"
                )
                print(f"Your subscriptions are: {self.subscriptions}")

    def unsubscribe(self, string):
        if string not in self.subscriptions:
            raise ValueError("The String is not in subscriptions")
        removed_subscription = self.subscriptions.pop(string)
        if self.parent_target.protocol.debug:
            print(
                f"Unsubscribe to {self.session_id} the key-value: {string} and {removed_subscription[0]}"
            )
            print(f"Your subscriptions are: {self.subscriptions}")
