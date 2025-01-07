"""protocol.py includes helpers and constants for the Chrome Devtools Protocol."""

from enum import Enum


class Ecode(Enum):
    """Ecodes are a list of possible error codes chrome returns."""

    TARGET_NOT_FOUND = -32602


class DevtoolsProtocolError(Exception):
    """Raise a general error reported by the devtools protocol."""

    def __init__(self, response):
        """
        Construct a new DevtoolsProtocolError.

        Args:
            response: the json response that contains the error

        """
        super().__init__(response)
        self.code = response["error"]["code"]
        self.message = response["error"]["message"]


class MessageTypeError(TypeError):
    """An error for poorly formatted devtools protocol message."""

    def __init__(self, key, value, expected_type):
        """
        Construct a message about a poorly formed protocol message.

        Args:
            key: the key that has the badly typed value
            value: the type of the value that is incorrect
            expected_type: the type that was expected

        """
        value = type(value) if not isinstance(value, type) else value
        super().__init__(
            f"Message with key {key} must have type {expected_type}, not {value}.",
        )


class MissingKeyError(ValueError):
    """An error for poorly formatted devtools protocol message."""

    def __init__(self, key, obj):
        """
        Construct a MissingKeyError specifying which key was missing.

        Args:
            key: the missing key
            obj: the message without the key

        """
        super().__init__(
            f"Message missing required key/s {key}. Message received: {obj}",
        )


class ExperimentalFeatureWarning(UserWarning):
    """An warning to report that a feature may or may not work."""


def verify_params(obj):
    """
    Verify the message obj hast he proper keys and values.

    Args:
        obj: the object to check.

    Raises:
        MissingKeyError: if a key is missing.
        MessageTypeError: if a value type is incorrect.
        RuntimeError: if there are strange keys.

    """
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
    """
    Given a response from the browser, calculate the key corresponding to the command.

    Every message is uniquely identified by its sessionId and id (counter).

    Args:
        response: the message for which to calculate the key.

    """
    session_id = response.get("sessionId", "")
    message_id = response.get("id", None)
    if message_id is None:
        return None
    return (session_id, message_id)


def match_message_key(response, key):
    """
    Report True if a response matches with a certain key (sessionId, id).

    Args:
        response: the object response from the browser
        key: the (sessionId, id) key tubple we're looking for

    """
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
    """Return true if the browser response is an event notification."""
    required_keys = {"method", "params"}
    return required_keys <= response.keys() and "id" not in response


def get_target_id_from_result(response):
    """
    Extract target id from a browser response.

    Args:
        response: the browser response to extract the targetId from.

    """
    if "result" in response and "targetId" in response["result"]:
        return response["result"]["targetId"]
    else:
        return None


def get_session_id_from_result(response):
    """
    Extract session id from a browser response.

    Args:
        response: the browser response to extract the sessionId from.

    """
    if "result" in response and "sessionId" in response["result"]:
        return response["result"]["sessionId"]
    else:
        return None


def get_error_from_result(response):
    """
    Extract error from a browser response.

    Args:
        response: the browser response to extract the error from.

    """
    if "error" in response:
        return response["error"]
    else:
        return None
