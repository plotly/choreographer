from __future__ import annotations

import json
from typing import TYPE_CHECKING

import logistro
import simplejson
from simplejson import errors as sjerrors

from ._errors import JSONError

if TYPE_CHECKING:
    from typing import Any

_logger = logistro.getLogger(__name__)

_custom_encoder: type[json.JSONEncoder] | None = None


def register_custom_encoder(e: type[json.JSONEncoder] | None) -> None:
    global _custom_encoder  # noqa: PLW0603 what other choice do we have
    _custom_encoder = e


class MultiEncoder(simplejson.JSONEncoder):
    """Special json encoder for numpy types."""

    # docs say subclassing inferior, just pass this method as a kward
    def default(self, obj: Any) -> Any:
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
        if not _custom_encoder:
            message = simplejson.dumps(
                obj,
                ensure_ascii=False,
                ignore_nan=True,
                cls=MultiEncoder,
            )
        else:
            message = json.dumps(obj, cls=_custom_encoder)
    except (json.JSONDecodeError, simplejson.JSONDecodeError) as e:
        raise JSONError from e
    _logger.debug(f"Serialized: {message[:15]}...{message[-15:]}, size: {len(message)}")
    _logger.debug2(f"Whole message: {message}")

    return message.encode("utf-8")


def deserialize(message: str) -> Any:
    try:
        return simplejson.loads(message)
    except sjerrors.JSONDecodeError as e:
        raise JSONError from e
