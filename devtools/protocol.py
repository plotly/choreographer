import json
import sys
import warnings
# from functools import partial

from .pipe import PipeClosedError
from threading import Thread


class Protocol:
    # TODO: detect default loop?
    def __init__(self, browser_pipe, loop=None, executor=None, debug=False):
        # Stored Resources
        self.pipe = browser_pipe
        self.loop = loop
        self.executor = executor

        # Configuration
        self.debug = debug

        # State Variables
        self.futures = None
        self.sessions = {}

        # Init
        if loop:
            self.futures = {}
            self.run_read_loop()

    def key_from_obj(self, response):
        session_id = response["sessionId"] if "sessionId" in response else ""
        message_id = response["id"] if "id" in response else None
        if message_id is None:
            return None
        return (session_id, message_id)

    def write_json(self, obj):
        n_keys = 0
        if "id" in obj and "method" in obj:
            n_keys += 2
        else:
            raise RuntimeError("Each message object must contain an id and method key")

        if "params" in obj:
            n_keys += 1
        if "sessionId" in obj:
            n_keys += 1

        if len(obj.keys()) != n_keys:
            raise RuntimeError(
                "Message objects must have id and method keys, and may have params and sessionId keys."
            )
        if self.loop:
            key = self.key_from_obj(obj)
            future = self.loop.create_future()
            self.futures[key] = future
            self.loop.run_in_executor(
                self.executor, self.pipe.write_json, obj
            )  # ignore result
            return future
        else:
            self.pipe.write_json(obj)

    def verify_response(self, response, session_id, message_id):
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

    def get_targetId(self, response):
        if "result" in response and "targetId" in response["result"]:
            return response["result"]["targetId"]
        else:
            return None

    def get_sessionId(self, response):
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

    def run_read_loop(self):
        async def read_loop():
            try:
                responses = await self.loop.run_in_executor(
                    self.executor, self.pipe.read_jsons, True, self.debug
                )
                for response in responses:
                    error = self.get_error(response)
                    key = self.key_from_obj(response)
                    if not self.has_id(response) and error:
                        raise RuntimeError(error)
                    elif self.is_event(response):
                        session_id = (
                            response["sessionId"] if "sessionId" in response else ""
                        )
                        session = self.sessions[session_id]
                        subscriptions = session.subscriptions
                        for key in subscriptions:
                            similar_strings = key.endswith("*") and response[
                                "method"
                            ].startswith(key[:-1])
                            equals_method = response["method"] == key
                            if similar_strings or equals_method:
                                self.loop.create_task(subscriptions[key], response)
                    elif key:
                        future = None
                        if key in self.futures:
                            future = self.futures.pop(key)
                        else:
                            raise RuntimeError(f"Couldn't find a future for key: {key}")
                        if error:
                            future.set_result({"error": error})
                        else:
                            future.set_result(
                                {"result": response["result"]}
                            )  # correcto?
                    else:
                        warnings.warn("Unhandled message type:")
                        continue  # TODO make this work
                        warnings.warn(json.dumps(response))
                        warnings.warn("Current futures:")
                        warnings.warn(self.futures.keys())

            except PipeClosedError:
                # TODO this isn't being caught
                return
            self.loop.create_task(read_loop())

        self.loop.create_task(read_loop())

    def run_output_thread(self, debug=None):
        if not debug:
            debug = self.debug

        def run_print(debug):
            while True:
                try:
                    responses = self.pipe.read_jsons(debug=debug)
                    for response in responses:
                        print(json.dumps(response, indent=4))
                except PipeClosedError:
                    print("Pipe closed.", file=sys.stderr)
                    break

        Thread(target=run_print, args=(debug,)).start()
