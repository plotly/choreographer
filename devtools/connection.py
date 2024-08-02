from .session import Session
from collections import OrderedDict


class Connection:
    def __init__(self, browser_process):
        self.browser_process = browser_process
        self.browser_session = Session(sessionId="")
        self.tab_sessions = OrderedDict()
