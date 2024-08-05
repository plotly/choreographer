from .session import Session
from collections import OrderedDict
import uuid


class Connection:
    def __init__(self, browser_process):
        self.browser_process = browser_process
        self.browser_session = Session(sessionId="")
        self.tab_sessions = OrderedDict()

    def create_tab(self):
        self.browser_session = Session(str(uuid.uuid4()))
        self.tab_sessions[self.browser_session.sessionId] = self.browser_session
        print("The session were created and added!")

    def open_tab(self):
        print("Current sessions:")
        for session_id in self.tab_sessions:
            print(f"Session ID: {session_id}")

    def add_tab(self, session_id):
        self.browser_session = Session(session_id)
        self.tab_sessions[self.browser_session.sessionId] = self.browser_session
        print("The session was added!")

    def close_tab(self):
        print("The following sessions were deleted:")
        for session_uuid in self.tab_sessions.values():
            print(session_uuid[1])
        self.tab_sessions = OrderedDict()
