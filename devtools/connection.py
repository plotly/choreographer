from .session import Session
from collections import OrderedDict
import uuid


class Connection:
    def __init__(self, browser_process):
        self.browser_process = browser_process
        self.browser_session = Session(sessionId="")
        self.tab_sessions = OrderedDict()
        self._i = 0

    def create_tab(self):
        self.browser_session = Session(str(self._i))
        self._i += 1
        self.tab_sessions[self.browser_session.sessionId] = (self.browser_session, str(uuid.uuid4()))
        print("The session were created and added!")

    def open_tab(self):
        print(self.tab_sessions)

    def add_tab(self, session_id):
        self.browser_session = Session(session_id)
        self.tab_sessions[self.browser_session.sessionId] = (self.browser_session, str(uuid.uuid4()))
        print("The session was added!")
    
    def close_tab(self):
        print("The following sessions were deleted:")
        for session_info in self.tab_sessions.values():
            print(session_info[1])
        self.tab_sessions = OrderedDict()