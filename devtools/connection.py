from .session import Session
from collections import OrderedDict
import uuid


class Connection:
    def __init__(self, browser_process=None):
        self.browser_process = browser_process
        self.browser_session = Session(session_id="")
        self.tab_sessions = OrderedDict()

    def create_tab(self):
        session_id = str(uuid.uuid4())
        session_obj = Session(session_id)
        self.tab_sessions[session_id] = session_obj
        print("The session were created and added!")

    def list_tabs(self):
        print("Current sessions".center(50,'-'))
        for session_id, session_instance in self.tab_sessions.items():
            print(f"Session ID: {session_id}, Session instance: {session_instance}")

    def close_tab(self, session_id):
        del self.tab_sessions[session_id]
        print(f"The following session was deleted: {session_id}")
