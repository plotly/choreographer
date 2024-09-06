from collections import OrderedDict

from .session import Session


class Target:
    def __init__(self, target_id, browser):
        if not isinstance(target_id, str):
            raise TypeError("target_id must be string")
        self.sessions = OrderedDict()
        self.target_id = target_id
        self.browser = browser
        self.protocol = browser.protocol

    def add_session(self, session):
        if not isinstance(session, Session):
            raise TypeError("session must be an object of class Session")
        self.sessions[session.session_id] = session

    def remove_session(self, session_id):
        if isinstance(session_id, Session):
            session_id = session_id.session_id
        del self.sessions[session_id]

    async def create_session(self):
        if not self.browser.loop:
            raise RuntimeError(
                "There is no eventloop, or was not passed to browser. Cannot use async methods"
            )
        response = await self.browser.send_command(
            "Target.attachToTarget", params=dict(targetId=self.target_id, flatten=True)
        )
        if "error" in response:
            raise RuntimeError("Could not create session") from Exception(
                response["error"]
            )
        session_id = response["result"]["sessionId"]
        new_session = Session(self, session_id)
        self.add_session(new_session)
        return new_session

    async def close_session(self, session):
        if not self.browser.loop:
            raise RuntimeError(
                "There is no eventloop, or was not passed to browser. Cannot use async methods"
            )
        if isinstance(session, Session):
            session = session.session_id
        response = await self.browser.send_command(
            command="Target.detachFromTarget",
            params={"sessionId": session},
        )
        self.remove_session(session)
        if "error" in response:
            raise RuntimeError("Could not close session") from Exception(
                response["error"]
            )
        print(f"The session {session} has been closed")
        return response

    def send_command(self, command, params=None):
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        return list(self.sessions.values())[0].send_command(command, params)
