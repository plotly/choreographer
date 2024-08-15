from .tab import Tab
from .session import Session
from collections import OrderedDict


class Protocol:
    def __init__(self, browser_pipe):
        self.browser_session = Session(self, session_id="")
        self.target_id = 0
        self.tabs = OrderedDict()
        self.browser_pipe = browser_pipe
        self._id_zero = True

    def create_tab(self):
        tab_obj = Tab()
        if self._id_zero and 0 not in self.tabs.keys():
            self._id_zero = False
            self.tabs[tab_obj.id] = tab_obj
        else:
            tab_obj.id =  next(reversed(self.tabs.keys())) + 1
            self.tabs[tab_obj.id] = tab_obj
        print(f"New Tab Created: {tab_obj.id}")
        return tab_obj

    def list_tabs(self):
        print("Tabs".center(50, "-"))
        for tab in self.tabs.values():
            print(str(tab.id).center(50, " "))
        print("End".center(50, "-"))

    def close_tab(self, tab_id):
        del self.tabs[tab_id]
        print(f"The following tab was deleted: {tab_id}")

    def send_command(self, command, params=None, cb=None):
        return self.tab.send_command(self, command, params, cb)