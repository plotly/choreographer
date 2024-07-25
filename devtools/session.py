class Session:
    def __init__(self, command, params):
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
