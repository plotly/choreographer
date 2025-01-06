from ._tab import Tab


class BrowserBase:
    def __init__(self):
        self.tabs = {}

    def _add_tab(self, tab):
        if not isinstance(tab, Tab):
            raise TypeError("tab must be an object of (sub)class Tab")
        self.tabs[tab.target_id] = tab

    def _remove_tab(self, target_id):
        if isinstance(target_id, Tab):
            target_id = target_id.target_id
        del self.tabs[target_id]

    def get_tab(self):
        if self.tabs.values():
            return next(iter(self.tabs.values()))
        return None
