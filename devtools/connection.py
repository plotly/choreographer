from session import Session
from collections import OrderedDict


class Connection:
    def __init__(self, *args):
        self.session = Session(*args)
        self.sessions = OrderedDict()
        self.sessions[self.session.sessionId] = self.session

    def add_session(self, *args):
        user_session = Session(*args)
        self.session = user_session
        self.sessions[self.session.sessionId] = self.session
