import json


class Session:
    def __init__(self, sessionId):
        if isinstance(sessionId, str):
            self._sessionId = sessionId
        else:
            raise TypeError("You must use an string object for sessionId")

        self._eventCbs = {}
        self._messageCbs = {}
        self._messageId = 0

        @property
        def eventCbs(self):
            return self._eventCbs

        @eventCbs.setter
        def eventCbs(self, eventCbs):
            self._eventCbs = eventCbs

        @property
        def messageCbs(self):
            return self._messageCbs

        @messageCbs.setter
        def messageCbs(self, messageCbs):
            self._messageCbs = messageCbs

        @property
        def messageId(self):
            return self._messageId

        @messageId.setter
        def messageId(self, messageId):
            self._messageId = messageId

    def send_command(self, command, params, **kwargs):
        cb = kwargs("cb", None)

        if cb:
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
