from .tab import Tab
from .pipe import Pipe
from collections import OrderedDict


class Protocol:
    def __init__(self, browser_pipe=Pipe()):
        self.browser_tab = Tab()
        self.tabs = OrderedDict()
        self.browser_pipe = browser_pipe

    def create_tab(self):
        tab_obj = Tab()
        self.tabs[id(tab_obj)] = tab_obj
        print("New Tab Created")
        return tab_obj

    def list_tabs(self):
        print("Tabs".center(50, "-"))
        for tab in self.tab.values():
            print(str(tab.session_id).center(50, " "))
        print("End".center(50, "-"))

    def close_tab(self, tab_obj):
        del self.tabs[id(tab_obj)]
        print(f"The following tab was deleted: {tab_obj}")

    def send_command(self, command, params=None, cb=None):
        return self.browser_tab.send_command(self, command, params, cb)
