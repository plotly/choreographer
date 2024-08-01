from session import Session
from collections import OrderedDict


class Connection:
    def __init__(self, browser):
        self.session = Session(browser)
        self.sessions = OrderedDict()
        self.sessions[self.session.sessionId] = self.session
