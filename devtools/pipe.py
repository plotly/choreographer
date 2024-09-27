import os
import sys
import json
import platform

# TODO: don't know about this
# TODO: use has_attr instead of np.integer, you'll be fine
class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if hasattr(obj, "dtype") and obj.dtype.kind == "i" and not hasattr(obj, "__len__"):
            return int(obj)
        elif hasattr(obj, "dtype") and obj.dtype.kind == "f" and not hasattr(obj, "__len__"):
            return float(obj)
        elif hasattr(obj, "dtype") and hasattr(obj, "__len__"):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class PipeClosedError(IOError):
    pass

class Pipe:
    def __init__(self, debug=False, cls=NumpyEncoder):
        self.read_from_chromium, self.write_from_chromium = list(os.pipe())
        self.read_to_chromium, self.write_to_chromium = list(os.pipe())
        self.debug = debug
        self.cls=cls

    def write_json(self, obj, debug=None):
        if not debug: debug = self.debug
        if debug:
            print("write_json:", file=sys.stderr)
        message = json.dumps(obj, ensure_ascii=False, cls=self.cls)
        encoded_message = message.encode("utf-8") + b"\0"
        if debug:
            print(f"write_json: {message}", file=sys.stderr)
            # windows may print weird characters if we set utf-8 instead of utf-16
            # check this TODO
        os.write(self.write_to_chromium, encoded_message)

    def read_jsons(self, blocking=True, debug=None):
        if not debug:
            debug = self.debug
        if debug:
            print(f"read_jsons ({'blocking' if blocking else 'not blocking'}):", file=sys.stderr)
        jsons = []
        os.set_blocking(self.read_from_chromium, blocking)
        try:
            raw_buffer = os.read(
                self.read_from_chromium, 10000
            )  # 10MB buffer, nbd, doesn't matter w/ this
            if not raw_buffer or raw_buffer == b'{bye}\n':
                # we seem to need {bye} even if chrome closes NOTE
                if debug: print("read_jsons pipe was closed, raising")
                raise PipeClosedError()
            while raw_buffer[-1] != 0:
                # still not great, return what you have
                os.set_blocking(self.read_from_chromium, True)
                raw_buffer += os.read(self.read_from_chromium, 10000)
        except BlockingIOError:
            if debug:
                print("read_jsons: BlockingIOError caught.", file=sys.stderr)
            return jsons
        decoded_buffer = raw_buffer.decode("utf-8")
        for raw_message in decoded_buffer.split("\0"):
            if raw_message:
                jsons.append(json.loads(raw_message))
                if debug:
                    # This debug is kinda late but the jsons package helps with decoding, since JSON optionally
                    # allows escaping unicode characters, which chrome does (oof)
                    print(f"read_jsons: {jsons[-1]}", file=sys.stderr)
        return jsons

    def close(self):
        if platform.system() == "Windows":
            try:
                os.set_blocking(self.write_from_chromium, False)
                os.write(self.write_from_chromium, b'{bye}\n')
            except Exception:
                pass
        os.close(self.write_to_chromium)
        os.close(self.read_from_chromium)
        os.close(self.write_from_chromium)
        os.close(self.read_to_chromium)
