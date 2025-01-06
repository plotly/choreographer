import json
from threading import Thread

from choreographer import protocol

from ._channels import ChannelClosedError


class BrokerSync:
    def __init__(self, browser, channel):
        self.browser = browser
        self.channel = channel

    # This is the broker
    def run_output_thread(self, **kwargs):
        def run_print():
            try:
                while True:
                    responses = self.channel.read_jsons()
                    for response in responses:
                        print(json.dumps(response, indent=4), **kwargs)
            except ChannelClosedError:
                print("ChannelClosedError caught", **kwargs)

        Thread(target=run_print).start()

    def send_json(self, obj):
        protocol.verify_params(obj)
        key = protocol.calculate_message_key(obj)
        self.channel.write_json(obj)
        return key
