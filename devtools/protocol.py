from .session import Session
from .pipe import Pipe
from collections import OrderedDict
import uuid


class Protocol:
    def __init__(self, browser_pipe=Pipe()):
        self.browser_session = Session(self, session_id="")
        self.tab_sessions = OrderedDict()
        self.browser_pipe = browser_pipe

    def create_tab(self):
        session_id = str(uuid.uuid4())
        session_obj = Session(self, session_id=session_id)
        self.tab_sessions[id(session_obj)] = session_obj
        print(f"New Session Created: {session_obj.session_id}")
        return session_obj

    def list_tabs(self):
        print("Sessions".center(50,'-'))
        for session_instance in self.tab_sessions.values():
            print(str(session_instance.session_id).center(50,' '))
        print("End".center(50,'-'))

    def close_tab(self, session_obj):
        del self.tab_sessions[id(session_obj)]
        print(f"The following session was deleted: {session_obj.session_id}")

    def send_command(self, command, params=None, cb=None):
        return self.browser_session.send_command(self, command, params, cb)
