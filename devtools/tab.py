from .session import Session
from collections import OrderedDict
import uuid


class Tab:
    def __init__(self, browser_pipe):
        self.tab_sessions = OrderedDict()
        self.target_id = str(uuid.uuid4())
        self.pipe = browser_pipe

    def add_session(self):
        session_obj = Session(self)
        session_obj.send_command(
            command="Target.attachToTarget", params={"targetId": self.target_id}
        )
        data = self.pipe.read_jsons(debug=True)
        json_obj = data[0]
        session_obj.target_id = json_obj["result"]["sessionId"]
        self.tab_sessions[session_obj.session_id] = session_obj
        print(f"New Session Added: {session_obj.session_id}")
        return session_obj

    def list_sessions(self):
        print("Sessions".center(50, "-"))
        for session_instance in self.tab_sessions.values():
            print(str(session_instance.session_id).center(50, " "))
        print("End".center(50, "-"))

    def close_session(self, session):
        session_id = session.session_id if hasattr(session, "session_id") else session
        self.send_command(
            command="Target.detachFromTarget", params={"sessionId": session_id}
        )
        del self.tab_sessions[session_id]
        print(f"The following session was deleted: {session_id}")
