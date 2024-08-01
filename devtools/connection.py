from session import Session
from collections import OrderedDict

class Connection:
    def __init__(self, *args):
        self.session = Session(*args)
        od = OrderedDict()
        self.sessions = od[self.session.sessionId] = self.session