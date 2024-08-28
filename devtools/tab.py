from .session import Session
from .utils import verify_session_id, verify_json_list
from collections import OrderedDict
import uuid


class Tab:
    def __init__(self, browser_pipe):
        self.tab_sessions = OrderedDict()
        self.target_id = str(uuid.uuid4())
        self.pipe = browser_pipe

    def add_session_1(self, debug=False):
        if debug:
            print(">>>Add_session_1")
        session_obj = Session(self, session_id="")
        session_obj.send_command(
            command="Target.attachToTarget",
            params={"targetId": self.target_id, "flatten": True},
            debug=debug,
        )
        if debug:
            print("The tab was created with Target.createTarget")
        return session_obj

    def add_session_2(self, session_obj, data, debug=False):
        if debug:
            print(">>>Add_session_2")
            print(f"The json at create_tab() is: {data}")
        session_bool = False
        json_obj = verify_json_list(data, verify_session_id, session_bool, debug)
        session_obj.session_id = verify_session_id(json_obj)
        if debug:
            print(f"The session_id is: {session_obj.session_id}")
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
