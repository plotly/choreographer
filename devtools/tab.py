from .session import Session
from collections import OrderedDict
import uuid


class Tab:
    def __init__(self):
        self.browser_session = Session(self, session_id="")
        self.tab_sessions = OrderedDict()

    def add_session(self):
        session_id = str(uuid.uuid4())
        session_obj = Session(self, session_id=session_id)
        self.tab_sessions[id(session_obj)] = session_obj
        print(f"New Session Added: {session_obj.session_id}")
        return session_obj
