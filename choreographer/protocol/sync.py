"""Provide a lower-level sync interface to the Devtools Protocol."""

from __future__ import annotations

from typing import TYPE_CHECKING

import logistro

from choreographer._broker import BrokerSync

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from typing import Any

    from choreographer import protocol


_logger = logistro.getLogger(__name__)


class SessionSync:
    """A session is a single conversation with a single target."""

    _broker_type = BrokerSync
    # A list of the types that are essential to use
    # with this class

    def __init__(self, session_id: str, broker: BrokerSync) -> None:
        """
        Construct a session from the browser as an object.

        A session is like an open conversation with a target.
        All commands are sent on sessions.

        Args:
            broker:  a reference to the browser's broker
            session_id:  the id given by the browser

        """
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a string")
        # Resources
        self.broker = broker

        # State
        self.session_id = session_id
        _logger.debug(f"New session: {session_id}")
        self.message_id = 0

    def send_command(
        self,
        command: str,
        params: MutableMapping[str, Any] | None = None,
    ) -> protocol.MessageKey | None:
        """
        Send a devtools command on the session.

        https://chromedevtools.github.io/devtools-protocol/

        Args:
            command: devtools command to send
            params: the parameters to send

        Returns:
            A message key (session, message id) tuple or None

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
        _logger.debug(
            f"Sending {command} with {params} on session {self.session_id}",
        )
        return self.broker.send_json(json_command)


class TargetSync:
    """A target like a browser, tab, or others. It sends commands. It has sessions."""

    _session_type = SessionSync
    _broker_type = BrokerSync
    """Needs to know."""

    target_id: str
    """The browser's ID of the target."""

    def __init__(self, target_id: str, broker: BrokerSync):
        """
        Create a target after one ahs been created by the browser.

        Args:
            broker:  a reference to the browser's broker
            target_id:  the id given by the browser

        """
        if not isinstance(target_id, str):
            raise TypeError("target_id must be string")
        # Resources
        self.broker = broker

        # States
        self.sessions = {}
        self.target_id = target_id
        _logger.info(f"Created new target {target_id}.")

    def _add_session(self, session):
        if not isinstance(session, self._session_type):
            raise TypeError("session must be a session type class")
        self.sessions[session.session_id] = session

    def _remove_session(self, session_id):
        if isinstance(session_id, self._session_type):
            session_id = session_id.session_id
        _ = self.sessions.pop(session_id, None)

    def get_session(self):
        """Retrieve the first session of the target, if it exists."""
        if not self.sessions.values():
            raise RuntimeError(
                "Cannot use this method without at least one valid session",
            )
        return next(iter(self.sessions.values()))

    def send_command(
        self,
        command: str,
        params: MutableMapping[str, Any] | None = None,
    ) -> protocol.MessageKey | None:
        """
        Send a command to the first session in a target.

        https://chromedevtools.github.io/devtools-protocol/

        Args:
            command: devtools command to send
            params: the parameters to send

        """
        if not self.sessions.values():
            raise RuntimeError("Cannot send_command without at least one valid session")
        session = self.get_session()
        _logger.debug(
            f"Sending {command} with {params} on session {session.session_id}",
        )
        return session.send_command(command, params)
