from .session import Session
from collections import OrderedDict
import uuid


class Tab:
    def __init__(self):
        self.tab_sessions = OrderedDict()
        self.target_id = str(uuid.uuid4())
        self.id = 0

    def add_session(self):
        session_id = str(uuid.uuid4())
        session_obj = Session(self, session_id=session_id)
        self.tab_sessions[id(session_obj)] = session_obj
        print(f"New Session Added: {session_obj.session_id}")
        return session_obj

    def list_sessions(self):
        print("Sessions".center(50, "-"))
        for session_instance in self.tab_sessions.values():
            print(str(session_instance.session_id).center(50, " "))
        print("End".center(50, "-"))

    def close_session(self, session_obj):
        del self.tab_sessions[id(session_obj)]
        print(f"The following session was deleted: {session_obj.session_id}")
