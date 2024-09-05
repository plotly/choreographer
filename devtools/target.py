from collections import OrderedDict

from .session import Session

class Target:
    def __init__(self, target_id, browser):
        if not isinstance(target_id, str):
            raise TypeError("target_id must be string")
        self.sessions = OrderedDict()
        self.target_id = target_id
        self.browser = browser

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
            raise RuntimeError("There is no eventloop, or was not passed to browser. Cannot use async methods")
        response = await self.browser.send_command("Target.attachToTarget",
                                                  params=dict(
                                                      targetId = self.target_id,
                                                      flatting=True
                                                      ))
        if "error" in response:
            raise RuntimeError("Could not create session") from Exception(response["error"])
        session_id = response["result"]["sessionId"]
        self.add_session(Session(self, session_id))

    # def close_session():

    def send_command(self, command, params=None):
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        return list(self.sessions.values())[0].send_command(command, params)


