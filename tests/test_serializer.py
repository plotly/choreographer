try:
    from datetime import UTC, datetime  #  type: ignore [attr-defined]
except ImportError:
    from datetime import datetime, timezone

    UTC = timezone.utc

import logistro
import numpy as np
import pytest

import choreographer.channels._wire as wire

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")


_timestamp = datetime(1970, 1, 1, tzinfo=UTC)

data = [1, 2.00, 3, float("nan"), float("inf"), float("-inf"), _timestamp]
expected_message = b'[1, 2.0, 3, null, null, null, "1970-01-01T00:00:00+00:00"]'
converted_type = [int, float, int, type(None), type(None), type(None), str]

_logger = logistro.getLogger(__name__)


@pytest.mark.asyncio
async def test_de_serialize():
    _logger.info("testing...")
    message = wire.serialize(data)
    assert message == expected_message
    obj = wire.deserialize(message)
    assert len(obj) == len(converted_type)
    for o, t in zip(obj, converted_type):
        assert isinstance(o, t)
    message_np = wire.serialize(np.array(data))
    assert message_np == expected_message
    obj_np = wire.deserialize(message_np)
    assert len(obj_np) == len(converted_type)
    for o, t in zip(obj_np, converted_type):
        assert isinstance(o, t)
