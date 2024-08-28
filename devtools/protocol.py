from .tab import Tab
from .session import Session
from collections import OrderedDict
from .utils import verify_target_id, verify_json_list


class Protocol:
    def __init__(self, browser_pipe):
        self.browser_session = Session(self, session_id="")
        self.target_id = 0
        self.tabs = OrderedDict()
        self.pipe = browser_pipe

    def send_command(self, command, params=None, cb=None, session_id=None, debug=False):
        return self.browser_session.send_command(command, params, cb, session_id, debug)

    def create_tab_1(self, url="chrome://new-tab-page/", debug=False):
        if debug:
            print(">create_tab_1")
        tab_obj = Tab(self.pipe)
        self.send_command(
            command="Target.createTarget",
            params={"url": url},
            debug=debug,
        )
        if debug:
            print("The tab was created with Target.createTarget")
        return tab_obj

    def create_tab_2(self, tab_obj, data, debug=False):
        if debug:
            print(">create_tab_2")
            print(f"The json at create_tab() is: {data}")
        target_bool = False
        json_obj = verify_json_list(data, verify_target_id, target_bool, debug)
        tab_obj.target_id = verify_target_id(json_obj)
        if debug:
            print(f"The target_id is: {tab_obj.target_id}")
        self.tabs[tab_obj.target_id] = tab_obj
        print(f"New Tab Created: {tab_obj.target_id}")
        return tab_obj

    def create_tab_3(self, url="chrome://new-tab-page/", session_obj=None, debug=False):
        if debug:
            print(">create_tab_3")
        tab_obj = self.create_tab_1(url, debug)
        data = self.pipe.read_jsons(debug)
        if session_obj:
            while any(dict_data["id"] != session_obj.message_id for dict_data in data):
                data = self.pipe.read_jsons(debug)
        else:
            while any(
                dict_data["id"] != tab_obj.browser_session.message_id
                for dict_data in data
            ):
                data = self.pipe.read_jsons(debug)
        return self.create_tab_2(tab_obj, data, debug)

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
