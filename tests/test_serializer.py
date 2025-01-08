from datetime import UTC, datetime

import numpy as np

from choreographer._pipe import Pipe

_timestamp = datetime(1970, 1, 1, tzinfo=UTC)

data = [1, 2.00, 3, float("nan"), float("inf"), float("-inf"), _timestamp]
expected_message = b'[1, 2.0, 3, null, null, null, "1970-01-01T00:00:00+00:00"]\x00'
converted_type = [int, float, int, type(None), type(None), type(None), str]


def test_de_serialize():
    pipe = Pipe()
    message = pipe.serialize(data)
    assert message == expected_message
    obj = pipe.deserialize(message[:-1])  # split out \0
    for o, t in zip(obj, converted_type, strict=False):
        assert isinstance(o, t)
    message_np = pipe.serialize(np.array(data))
    assert message_np == expected_message
    obj_np = pipe.deserialize(message_np[:-1])  # split out \0
    for o, t in zip(obj_np, converted_type, strict=False):
        assert isinstance(o, t)
