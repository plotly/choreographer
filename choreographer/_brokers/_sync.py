import json
from threading import Thread

import logistro

from choreographer.channels import ChannelClosedError

from . import protocol

logger = logistro.getLogger(__name__)


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
                print("ChannelClosedError caught.", **kwargs)

        logger.info("Starting thread to dump output to stdout.")
        Thread(target=run_print).start()

    def send_json(self, obj):
        protocol.verify_params(obj)
        key = protocol.calculate_message_key(obj)
        self.channel.write_json(obj)
        return key

    def clean(self):
        pass
