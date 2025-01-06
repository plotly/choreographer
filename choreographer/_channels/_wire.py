import logistro
import simplejson

from ._errors import JSONError

logger = logistro.getLogger(__name__)


class MultiEncoder(simplejson.JSONEncoder):
    """Special json encoder for numpy types."""

    def default(self, obj):
        if hasattr(obj, "dtype") and obj.dtype.kind == "i" and obj.shape == ():
            return int(obj)
        elif hasattr(obj, "dtype") and obj.dtype.kind == "f" and obj.shape == ():
            return float(obj)
        elif hasattr(obj, "dtype") and obj.shape != ():
            return obj.tolist()
        elif hasattr(obj, "isoformat"):
            return obj.isoformat()
        return simplejson.JSONEncoder.default(self, obj)


def serialize(obj):
    try:
        message = simplejson.dumps(
            obj,
            ensure_ascii=False,
            ignore_nan=True,
            cls=MultiEncoder,
        )
    except simplejson.errors.JSONDecodeError as e:
        raise JSONError from e
    logger.debug2(f"Serialized: {message}")
    return message.encode("utf-8")


def deserialize(message):
    try:
        return simplejson.loads(message)
    except simplejson.errors.JSONDecodeError as e:
        raise JSONError from e
