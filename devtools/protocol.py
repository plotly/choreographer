from .tab import Tab
from .session import Session
from collections import OrderedDict


class Protocol:
    def __init__(self, browser_pipe):
        self.browser_session = Session(self, session_id="")
        self.target_id = 0
        self.tabs = OrderedDict()
        self.pipe = browser_pipe

    def send_command(self, command, params=None, cb=None):
        return self.browser_session.send_command(command, params, cb)

    def create_tab(self):
        tab_obj = Tab()
        self.send_command(
            command="Target.createTarget", params={"url": "chrome://new-tab-page/"}
        )
        data = self.pipe.read_jsons(debug=True)
        json_obj = data[0]
        tab_obj.target_id = json_obj["result"]["targetId"]
        self.tabs[tab_obj.target_id] = tab_obj

        print(f"New Tab Created: {tab_obj.target_id}")
        return tab_obj

    def list_tabs(self):
        print("Tabs".center(50, "-"))
        for target_id in self.tabs.keys():
            print(target_id.center(50, " "))
        print("End".center(50, "-"))

    def close_tab(self, tab_id):
        if isinstance(tab_id, str):
            self.send_command(command="Target.closeTarget", params={"targetId": tab_id})
            del self.tabs[tab_id]
        else:
            self.send_command(
                command="Target.closeTarget", params={"targetId": tab_id.target_id}
            )
            del self.tabs[tab_id.target_id]
        print(f"The following tab was deleted: {tab_id}")
