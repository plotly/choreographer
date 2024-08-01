import json


class Session:
    def __init__(self, sessionId):
        if isinstance(sessionId, str):
            self.sessionId = sessionId
        else:
            raise TypeError("You must use an string object for sessionId")

        self.eventCbs = {}
        self.messageCbs = {}
        self.messageId = 0

    def send_command(self, command, params, cb=False):

        if cb is False and callable(cb) is False:
                raise TypeError("The arg that you use, is not able at cb")
        elif cb is False:
            cb = None
        
        self.messageCbs[self.messageId] = cb

        if not isinstance(command, str):
            raise TypeError("You must use an string for the command parameter")
        json_command = {
            "method": command,
            "params": params,
            "Id": self.messageId,
            "messageCbs": self.messageCbs,
        }
        self.messageId = +1
        return json.dumps(json_command)
