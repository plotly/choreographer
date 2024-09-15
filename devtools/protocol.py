class Protocol:
    def __init__(self, debug=False):
        # Stored Resources

        # Configuration
        self.debug = debug

        # State
        self.sessions = {}


    def calculate_key(self, response):
        session_id = response["sessionId"] if "sessionId" in response else ""
        message_id = response["id"] if "id" in response else None
        if message_id is None:
            return None
        return (session_id, message_id)

    def verify_json(self, obj):
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
            raise RuntimeError(
                "Message objects must have id and method keys, and may have params and sessionId keys."
            )

    def match_key(self, response, key):
        session_id, message_id = key
        if "session_id" not in response and session_id == "":
            pass
        elif "session_id" in response and response["session_id"] == session_id:
            pass
        else:
            return False

        if "id" in response and str(response["id"]) == str(message_id):
            pass
        else:
            return False
        return True

    def has_id(self, response):
        return "id" in response

    def get_targetId(self, response):
        if "result" in response and "targetId" in response["result"]:
            return response["result"]["targetId"]
        else:
            return None

    def get_sessionId(self, response):
        if "result" in response and "sessionId" in response["result"]:
            return response["result"]["sessionId"]
        else:
            return None

    def get_error(self, response):
        if "error" in response:
            return response["error"]
        else:
            return None

    def is_event(self, response):
        required_keys = {"method", "params"}
        if required_keys <= response.keys() and "id" not in response:
            return True
        return False


