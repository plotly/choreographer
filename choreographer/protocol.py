"""protocol.py includes helpers and constants for the Chrome Devtools Protocol."""

from enum import Enum


class Ecode(Enum):
    """Ecodes are a list of possible error codes chrome returns."""

    TARGET_NOT_FOUND = -32602


class DevtoolsProtocolError(Exception):
    """."""

    def __init__(self, response):
        """."""
        super().__init__(response)
        self.code = response["error"]["code"]
        self.message = response["error"]["message"]


class MessageTypeError(TypeError):
    """."""

    def __init__(self, key, value, expected_type):
        """."""
        value = type(value) if not isinstance(value, type) else value
        super().__init__(
            f"Message with key {key} must have type {expected_type}, not {value}.",
        )


class MissingKeyError(ValueError):
    """."""

    def __init__(self, key, obj):
        """."""
        super().__init__(
            f"Message missing required key/s {key}. Message received: {obj}",
        )


class ExperimentalFeatureWarning(UserWarning):
    """."""


def verify_params(obj):
    n_keys = 0

    required_keys = {"id": int, "method": str}
    for key, type_key in required_keys.items():
        if key not in obj:
            raise MissingKeyError(key, obj)
        if not isinstance(obj[key], type_key):
            raise MessageTypeError(key, type(obj[key]), type_key)
    n_keys += 2

    if "params" in obj:
        n_keys += 1
    if "sessionId" in obj:
        n_keys += 1

    if len(obj.keys()) != n_keys:
        raise RuntimeError(
            "Message objects must have id and method keys, "
            "and may have params and sessionId keys.",
        )


def calculate_message_key(response):
    session_id = response.get("sessionId", "")
    message_id = response.get("id", None)
    if message_id is None:
        return None
    return (session_id, message_id)


def match_message_key(response, key):
    session_id, message_id = key
    if ("session_id" not in response and session_id == "") or (  # is browser session
        "session_id" in response and response["session_id"] == session_id  # is session
    ):
        pass
    else:
        return False

    if "id" in response and str(response["id"]) == str(message_id):
        pass
    else:
        return False
    return True


def is_event(response):
    required_keys = {"method", "params"}
    return required_keys <= response.keys() and "id" not in response


def get_target_id_from_result(response):
    if "result" in response and "targetId" in response["result"]:
        return response["result"]["targetId"]
    else:
        return None


def get_session_id_from_result(response):
    if "result" in response and "sessionId" in response["result"]:
        return response["result"]["sessionId"]
    else:
        return None


def get_error_from_result(response):
    if "error" in response:
        return response["error"]
    else:
        return None
