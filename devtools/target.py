from collections import OrderedDict

from .session import Session

class Target:
    def __init__(self, target_id, pipe):
        if not isinstance(target_id, str):
            raise TypeError("target_id must be string")
        self.sessions = OrderedDict()
        self.target_id = target_id
        self.pipe = pipe

    def add_session(self, session):
        if not isinstance(session, Session):
            raise TypeError("session must be an object of class Session")
        self.sessions[session.session_id] = session

    def remove_session(self, session_id):
        if isinstance(session_id, Session):
            session_id = session_id.session_id
        del self.sessions[session_id]

    def send_command(self, command, params=None):
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        list(self.sessions.values())[0].send_command(command, params)


