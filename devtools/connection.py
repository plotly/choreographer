from .session import Session
from collections import OrderedDict
import uuid


class Connection:
    def __init__(self, browser_process=None):
        self.browser_process = browser_process
        self.browser_session = Session(session_id="")
        self.tab_sessions = OrderedDict()
        self.tab_sessions[self.browser_session.session_id] = self.browser_session

    def create_tab(self):
        session_obj = Session(str(uuid.uuid4()))
        self.tab_sessions[self.browser_session.session_id] = session_obj
        print("The session were created and added!")
        print("Current sessions".center(50,'-'))
        for session_id in self.tab_sessions:
            print(f"Session ID: {session_id}, Session instance: {self.tab_sessions[session_id]}")

    def close_tab(self):
        print("The following sessions were deleted:")
        for session_uuid in self.tab_sessions:
            print(session_uuid)
        self.tab_sessions = OrderedDict()
