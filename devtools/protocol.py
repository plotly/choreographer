import json

class Protocol:
    def __init__(self, browser_pipe):
        self.pipe = browser_pipe

    def write_json(self, obj):
        n_keys = 0
        if "id" in obj and "method" in obj:
            n_keys += 2
        else:
            raise RuntimeError("Each message object must contain an id and method key")
        if "params" in obj:
            n_keys += 1
        if "sessionId" in obj:
            n_keys += 1

        if len(obj.keys()) != n_keys:
            raise RuntimeError("Message objects must have id and method keys, and may have params and sessionId keys")

        self.pipe.write_json(obj)

    # def find message
