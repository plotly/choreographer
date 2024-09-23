from collections import OrderedDict

from .session import Session


class Target:
    def __init__(self, target_id, browser):
        if not isinstance(target_id, str):
            raise TypeError("target_id must be string")
        # Resources
        self.browser = browser

        # States
        self.sessions = OrderedDict()
        self.target_id = target_id

    def add_session(self, session):
        if not isinstance(session, Session):
            raise TypeError("session must be an object of class Session")
        self.sessions[session.session_id] = session
        self.browser.protocol.sessions[session.session_id] = session

    def remove_session(self, session_id):
        if isinstance(session_id, Session):
            session_id = session_id.session_id
        if session_id not in self.sessions:
            return
        del self.sessions[session_id]
        del self.browser.protocol.sessions[session_id]

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
        new_session = Session(self.browser, session_id)
        self.add_session(new_session)
        return new_session

    async def close_session(self, session_id):
        if not self.browser.loop:
            raise RuntimeError(
                "There is no eventloop, or was not passed to browser. Cannot use async methods"
            )
        if isinstance(session_id, Session):
            session_id = session_id.session_id
        response = await self.browser.send_command(
            command="Target.detachFromTarget",
            params={"sessionId": session_id},
        )
        self.remove_session(session_id)
        if "error" in response:
            raise RuntimeError("Could not close session") from Exception(
                response["error"]
            )
        print(f"The session {session_id} has been closed")
        return response

    def send_command(self, command, params=None):
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        return list(self.sessions.values())[0].send_command(command, params)

    def subscribe(self, string, callback, repeating):
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        session = list(self.sessions.values())[0]
        session.subscribe(string, callback, repeating)

    def unsubscribe(self, string):
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        session = list(self.sessions.values())[0]
        session.unsubscribe(string)
