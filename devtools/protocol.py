from .tab import Tab
from collections import OrderedDict


class Protocol:
    def __init__(self, browser_pipe):
        self.tab = Tab()
        self.tabs = OrderedDict()
        self.browser_pipe = browser_pipe

    def create_tab(self):
        tab_obj = Tab()
        tab_obj.id = list(self.tabs.keys())[-1] + 1
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
