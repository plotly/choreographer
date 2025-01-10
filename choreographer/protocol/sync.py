"""Provide a lower-level sync interface to the Devtools Protocol."""

import logistro

logger = logistro.getLogger(__name__)


class SessionSync:
    """A session is a single conversation with a single target."""

    def __init__(self, browser, session_id):
        """
        Construct a session from the browser as an object.

        A session is like an open conversation with a target.
        All commands are sent on sessions.

        Args:
            browser:  a reference to the main browser
            session_id:  the id given by the browser

        """
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a string")
        # Resources
        self.browser = browser

        # State
        self.session_id = session_id
        logger.debug(f"New session: {session_id}")
        self.message_id = 0

    def send_command(self, command, params=None):
        """
        Send a devtools command on the session.

        https://chromedevtools.github.io/devtools-protocol/

        Args:
            command: devtools command to send
            params: the parameters to send

        """
        current_id = self.message_id
        self.message_id += 1
        json_command = {
            "id": current_id,
            "method": command,
        }

        if self.session_id:
            json_command["sessionId"] = self.session_id
        if params:
            json_command["params"] = params
        logger.debug(
            f"Sending {command} with {params} on session {self.session_id}",
        )
        return self.browser.broker.send_json(json_command)


class TargetSync:
    """A target like a browser, tab, or others. It sends commands. It has sessions."""

    _session_type = SessionSync
    """Like generic typing<>. This is the session type associated with TargetSync."""

    def __init__(self, target_id, browser):
        """Create a target after one ahs been created by the browser."""
        if not isinstance(target_id, str):
            raise TypeError("target_id must be string")
        # Resources
        self.browser = browser

        # States
        self.sessions = {}
        self.target_id = target_id
        logger.info(f"Created new target {target_id}.")

    def _add_session(self, session):
        if not isinstance(session, self._session_type):
            raise TypeError("session must be a session type class")
        self.sessions[session.session_id] = session
        self.browser.all_sessions[session.session_id] = session

    def _remove_session(self, session_id):
        if isinstance(session_id, self._session_type):
            session_id = session_id.session_id
        _ = self.sessions.pop(session_id, None)
        _ = self.browser.all_sessions.pop(session_id, None)

    def _get_first_session(self):
        if not self.sessions.values():
            raise RuntimeError(
                "Cannot use this method without at least one valid session",
            )
        return next(iter(self.sessions.values()))

    def send_command(self, command, params=None):
        """
        Send a command to the first session in a target.

        https://chromedevtools.github.io/devtools-protocol/

        Args:
            command: devtools command to send
            params: the parameters to send

        """
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        session = self._get_first_session()
        logger.debug(
            f"Sending {command} with {params} on session {session.session_id}",
        )
        return session.send_command(command, params)
