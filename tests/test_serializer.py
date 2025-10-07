from __future__ import annotations

try:
    from datetime import UTC, datetime  #  type: ignore [attr-defined]
except ImportError:
    from datetime import datetime, timezone

    UTC = timezone.utc

import json
from typing import TYPE_CHECKING

import choreographer.channels._wire as wire
import logistro
import numpy as np
import pytest
from choreographer.channels import register_custom_encoder

if TYPE_CHECKING:
    from typing import Any

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")


_timestamp = datetime(1970, 1, 1, tzinfo=UTC)

data = [1, 2.00, 3, float("nan"), float("inf"), float("-inf"), _timestamp]
expected_message = b'[1, 2.0, 3, null, null, null, "1970-01-01T00:00:00+00:00"]'
converted_type = [int, float, int, type(None), type(None), type(None), str]

_logger = logistro.getLogger(__name__)


async def test_custom_encoder():
    class NonsenseEncoder(json.JSONEncoder):
        def iterencode(
            self,
            o: Any,
            _one_shot: bool = False,  # noqa: FBT001, FBT002
        ) -> Any:
            _ = o
            yield "Test Passed."

        def encode(self, o: Any) -> Any:
            _ = o
            return "Test Passed."

    register_custom_encoder(NonsenseEncoder)
    message = wire.serialize(data)
    assert message == b"Test Passed."
    register_custom_encoder(None)
    message = wire.serialize(data)
    assert message == expected_message


@pytest.mark.asyncio
async def test_de_serialize():
    _logger.info("testing...")
    message = wire.serialize(data)
    assert message == expected_message
    obj = wire.deserialize(message.decode())
    assert len(obj) == len(converted_type)
    for o, t in zip(obj, converted_type):
        assert isinstance(o, t)
    message_np = wire.serialize(np.array(data))
    assert message_np == expected_message
    obj_np = wire.deserialize(message_np.decode())
    assert len(obj_np) == len(converted_type)
    for o, t in zip(obj_np, converted_type):
        assert isinstance(o, t)
