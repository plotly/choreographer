import sys

from collections import OrderedDict

from .session import Session
from .protocol import DevtoolsProtocolError


class Target:
    def __init__(self, target_id, browser):
        if not isinstance(target_id, str):
            raise TypeError("target_id must be string")
        # Resources
        self.browser = browser

        # States
        self.sessions = OrderedDict()
        self.target_id = target_id

    def _add_session(self, session):
        if not isinstance(session, Session):
            raise TypeError("session must be an object of class Session")
        self.sessions[session.session_id] = session
        self.browser.protocol.sessions[session.session_id] = session

    def _remove_session(self, session_id):
        if isinstance(session_id, Session):
            session_id = session_id.session_id
        _ = self.sessions.pop(session_id, None)
        _ = self.browser.protocol.sessions.pop(session_id, None)

    async def create_session(self):
        if not self.browser.loop:
            raise RuntimeError(
                "There is no eventloop, or was not passed to browser. Cannot use async methods"
            )
        response = await self.browser.send_command(
            "Target.attachToTarget", params=dict(targetId=self.target_id, flatten=True)
        )
        if "error" in response:
            raise RuntimeError("Could not create session") from DevtoolsProtocolError(
                response
            )
        session_id = response["result"]["sessionId"]
        new_session = Session(self.browser, session_id)
        self._add_session(new_session)
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
        self._remove_session(session_id)
        if "error" in response:
            raise RuntimeError("Could not close session") from DevtoolsProtocolError(
                response
            )
        print(f"The session {session_id} has been closed", file=sys.stderr)
        return response

    def send_command(self, command, params=None):
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        return list(self.sessions.values())[0].send_command(command, params)

    def _get_first_session(self):
        if not self.sessions.values():
            raise RuntimeError(
                "Cannot use this method without at least one valid session"
            )
        return list(self.sessions.values())[0]

    def subscribe(self, string, callback, repeating=True):
        session = self._get_first_session()
        session.subscribe(string, callback, repeating)

    def unsubscribe(self, string):
        session = self._get_first_session()
        session.unsubscribe(string)

    def subscribe_once(self, string):
        session = self._get_first_session()
        return session.subscribe_once(string)
