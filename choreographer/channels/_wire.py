from __future__ import annotations

from typing import TYPE_CHECKING

import logistro
import simplejson
from simplejson.errors import JSONDecodeError

from ._errors import JSONError

if TYPE_CHECKING:
    from typing import Any

_logger = logistro.getLogger(__name__)


class MultiEncoder(simplejson.JSONEncoder):
    """Special json encoder for numpy types."""

    def default(self, obj):
        if hasattr(obj, "dtype") and obj.dtype.kind in ("i", "u") and obj.shape == ():
            return int(obj)
        elif hasattr(obj, "dtype") and obj.dtype.kind == "f" and obj.shape == ():
            return float(obj)
        elif hasattr(obj, "dtype") and obj.shape != ():
            if hasattr(obj, "values") and hasattr(obj.values, "tolist"):
                return obj.values.tolist()
            if hasattr(obj, "tolist"):
                return obj.tolist()
        elif hasattr(obj, "isoformat"):
            return obj.isoformat()
        return simplejson.JSONEncoder.default(self, obj)


def serialize(obj: Any) -> bytes:
    try:
        message = simplejson.dumps(
            obj,
            ensure_ascii=False,
            ignore_nan=True,
            cls=MultiEncoder,
        )
    except JSONDecodeError as e:
        raise JSONError from e
    _logger.debug(f"Serialized: {message[:15]}...{message[-15:]}, size: {len(message)}")
    _logger.debug2(f"Whole message: {message}")

    return message.encode("utf-8")


def deserialize(message: str) -> Any:
    try:
        return simplejson.loads(message)
    except simplejson.errors.JSONDecodeError as e:
        raise JSONError from e
