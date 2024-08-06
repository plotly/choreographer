from .session import Session
from collections import OrderedDict
import uuid


class Connection:
    def __init__(self, browser_process=None):
        self.browser_process = browser_process
        self.browser_session = Session(session_id="", parent=self)
        self.tab_sessions = OrderedDict()

    def create_tab(self):
        session_id = str(uuid.uuid4())
        session_obj = Session(session_id, parent=self)
        self.tab_sessions[id(session_obj)] = session_obj
        print("The session were created and added!")
        return session_obj

    def list_tabs(self):
        print("Current sessions".center(50,'-'))
        for session_instance in self.tab_sessions.values():
            print(f"Session ID: {session_instance.session_id}, Session instance: {session_instance}")

    def close_tab(self, session_obj):
        del self.tab_sessions[id(session_obj)]
        print(f"The following session was deleted: {session_obj}")
