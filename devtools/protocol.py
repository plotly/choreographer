from .tab import Tab
from .session import Session
from collections import OrderedDict
from .utils import verify_json_id


class Protocol:
    def __init__(self, browser_pipe):
        self.browser_session = Session(self, session_id="")
        self.target_id = 0
        self.tabs = OrderedDict()
        self.pipe = browser_pipe

    def send_command(self, command, params=None, cb=None, session_id=None):
        return self.browser_session.send_command(command, params, cb, session_id)

    def create_tab(self, debug=False):
        tab_obj = Tab(self.pipe)
        self.send_command(
            command="Target.createTarget", params={"url": "chrome://new-tab-page/"}
        )
        if debug:
            print("The tab was created with Target.createTarget")
        data = self.pipe.read_jsons(debug)
        json_obj = data[0]
        tab_obj.target_id = json_obj["result"]["targetId"]
        if debug:
            print(f"The json at create_tab() is: {data}")
            print(f"The target_id is: {tab_obj.target_id}")
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
