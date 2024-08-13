from .tab import Tab
from .pipe import Pipe
from collections import OrderedDict


class Protocol:
    def __init__(self, browser_pipe=Pipe()):
        self.browser_tab = Tab()
        self.list_tab_id = [self.browser_tab.id]
        self.tabs = OrderedDict()
        self.browser_pipe = browser_pipe

    def create_tab(self):
        tab_obj = Tab()
        self.list_tab_id = self.list_tab_id.append(self.list_tab_id[-1] + 1)
        tab_obj.id = self.list_tab_id[-1]
        self.tabs[tab_obj] = tab_obj
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
        return self.browser_tab.send_command(self, command, params, cb)
