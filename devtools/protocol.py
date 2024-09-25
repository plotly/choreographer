import sys
import warnings

from .pipe import PipeClosedError

class UnhandledMessageWarning(UserWarning):
    pass

class Protocol:
    def __init__(self, browser, debug=False):
        # Stored Resources
        self.browser = browser
        # Configuration
        self.debug = debug

        # State
        self.sessions = {}

        self.futures = {}

    def calculate_key(self, response):
        session_id = response["sessionId"] if "sessionId" in response else ""
        message_id = response["id"] if "id" in response else None
        if message_id is None:
            return None
        return (session_id, message_id)

    def verify_json(self, obj):
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

    def match_key(self, response, key):
        session_id, message_id = key
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

    def get_target_id(self, response):
        if "result" in response and "targetId" in response["result"]:
            return response["result"]["targetId"]
        else:
            return None

    def get_session_id(self, response):
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
        loop = self.browser.loop
        pipe = self.browser.pipe
        executor = self.browser.executor
        async def read_loop():
            try:
                responses = await loop.run_in_executor(
                    executor, pipe.read_jsons, True, self.debug
                )
                for response in responses:
                    error = self.get_error(response)
                    key = self.calculate_key(response)
                    if not self.has_id(response) and error:
                        raise RuntimeError(error)
                    elif self.is_event(response):
                        session_id = (
                            response["sessionId"] if "sessionId" in response else ""
                        )
                        session = self.sessions[session_id]
                        subscriptions = session.subscriptions
                        subscriptions_futures = session.subscriptions_futures
                        for sub_key in list(subscriptions):
                            similar_strings = sub_key.endswith("*") and response[
                                "method"
                            ].startswith(sub_key[:-1])
                            equals_method = response["method"] == sub_key
                            if self.debug:
                                print(f"Checking subscription key: {sub_key} against event method {response['method']}", file=sys.stderr)
                            if similar_strings or equals_method:
                                loop.create_task(
                                    subscriptions[sub_key][0](response)
                                )
                                if not subscriptions[sub_key][1]: # if not repeating
                                    self.sessions[session_id].unsubscribe(sub_key)

                        for sub_key, futures in list(subscriptions_futures.items()):
                            similar_strings = sub_key.endswith("*") and response["method"].startswith(sub_key[:-1])
                            equals_method = response["method"] == sub_key
                            if self.debug:
                                print(f"Checking subscription key: {sub_key} against event method {response['method']}", file=sys.stderr)
                            if similar_strings or equals_method:
                                for future in futures:
                                    if self.debug:
                                        print(f"Processing future {id(future)}", file=sys.stderr)
                                    future.set_result(response)
                                    if self.debug:
                                        print(f"Future resolved with response {future}", file=sys.stderr)
                                del session.subscriptions_futures[sub_key]


                    elif key:
                        future = None
                        if key in self.futures:
                            if self.debug:
                                print(
                                    f"run_read_loop() found future foor key {key}"
                                )
                            future = self.futures.pop(key)
                        else:
                            raise RuntimeError(f"Couldn't find a future for key: {key}")
                        if error:
                            future.set_result(response)
                        else:
                            future.set_result(response)
                    else:
                        warnings.warn(f"Unhandled message type:{str(response)}", UnhandledMessageWarning)
            except PipeClosedError:
                if self.debug:
                    print("PipeClosedError caught", file=sys.stderr)
                return
            loop.create_task(read_loop())

        loop.create_task(read_loop())

    def write_json(self, obj):
        self.verify_json(obj)
        key = self.calculate_key(obj)
        if self.browser.loop:
            future = self.browser.loop.create_future()
            self.futures[key] = future
            self.browser.loop.run_in_executor(
                self.browser.executor, self.browser.pipe.write_json, obj
            )  # ignore result (what happens if there is error)
            return future
        else:
            self.browser.pipe.write_json(obj)
            return key


