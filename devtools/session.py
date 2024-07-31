import json


class Session:
    def __init__(self, sessionId):
        if isinstance(sessionId, str):
            self._sessionId = sessionId
        else:
            raise TypeError("You must use an string object for sessionId")

        self._messageId = 0
        
        @property
        def messageId(self):
            return self._messageId
        
        @messageId.setter
        def messageId(self, messageId):
            self._messageId = messageId

    def send_command(self, command, params):
        if not isinstance(command, str):
            raise TypeError("You must use an string for the command parameter")
        json_command = {"method": command, "params": params, "menssageId": self.messageId}
        self.messageId=+1
        return json.dumps(json_command)
