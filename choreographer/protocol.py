TARGET_NOT_FOUND = -32602


class DevtoolsProtocolError(Exception):
    def __init__(self, response):
        super().__init__(response)
        self.code = response["error"]["code"]
        self.message = response["error"]["message"]


class MessageTypeError(TypeError):
    def __init__(self, key, value, expected_type):
        super().__init__(
            f"Message with key {key} must have type {expected_type}, not {type(value)}."
        )


class MissingKeyError(ValueError):
    def __init__(self, key, obj):
        super().__init__(
            f"Message missing required key/s {key}. Message received: {obj}"
        )


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
            if not isinstance(obj["id"], int):
                raise MessageTypeError("id", type(obj["id"]), int)
            if not isinstance(obj["method"], str):
                raise MessageTypeError("method", type(obj["method"]), str)
            n_keys += 2
        elif "id" not in obj and "method" in obj:
            raise MissingKeyError("id", obj)
        elif "method" not in obj and "id" in obj:
            raise MissingKeyError("method", obj)
        else:
            raise MissingKeyError("id and method", obj)

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

    def get_target_id(self, response):
        if "result" in response and "targetId" in response["result"]:
            return response["result"]["targetId"]
        else:
            return None

    def get_session_id(self, response):
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
