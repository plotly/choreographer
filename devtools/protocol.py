from .tab import Tab
from .session import Session
from collections import OrderedDict
import os
import json


class Protocol:
    def __init__(self, browser_pipe):
        self.browser_session = Session(self, session_id="")
        self.target_id = 0
        self.tabs = OrderedDict()
        self.pipe = browser_pipe

    def send_command(self, command, params=None, cb=None):
        return self.browser_session.send_command(command, params, cb)

    def verify_json_id(self, json_list):
        to_chromium = os.read(
                self.pipe.read_to_chromium, 10000
            )
        to_chromium = json.load(to_chromium.decode("utf-8").split("\0")) #DEBO AGREGAR UN FOR PARA QUE LEA LAS ID Y LAS COMPARE
        for json_ in json_list:
            if to_chromium.id == json_.id:
                return json_

    def create_tab(self):
        tab_obj = Tab()
        self.send_command(
            command="Target.createTarget", params={"url": "chrome://new-tab-page/"}
        )
        data = self.pipe.read_jsons(debug=True)
        json_obj = self.verify_json_id(data)
        tab_obj.target_id = json_obj["result"]["targetId"]
        self.tabs[tab_obj.target_id] = tab_obj

        print(f"New Tab Created: {tab_obj.target_id}")
        return tab_obj

    def list_tabs(self):
        print("Tabs".center(50, "-"))
        for target_id in self.tabs.keys():
            print(target_id.center(50, " "))
        print("End".center(50, "-"))

    def close_tab(self, tab):
        target_id = tab.target_id if hasattr(tab, "target_id") else tab
        self.send_command(command="Target.closeTarget", params={"targetId": target_id})
        del self.tabs[target_id]
        print(f"The following tab was deleted: {target_id}")
