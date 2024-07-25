import json


class Session:
    def __init__(self, command, params):
        if not isinstance(command, str):
            raise TypeError("You must use an string for the command parameter")
        self._command = command
        self._params = params

    @property
    def command(self):
        return self._command

    @command.setter
    def command(self, command):
        self._command = command

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, params):
        self._params = params

    def send_command(self):
        json_command = {"method": self.command, "params": self.params}
        return json.dumps(json_command)
