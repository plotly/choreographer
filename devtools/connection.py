from session import Session
from collections import OrderedDict


class Connection:
    def __init__(self, *args):
        self.session = Session(*args)
        self.sessions = OrderedDict()
        self.sessions[self.session.sessionId] = self.session
