from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any


class SessionInterface(Protocol):
    def send_command(
        self,
        command: str,
        params: Mapping[str, Any] | None = None,
    ) -> Any: ...


class TargetInterface(Protocol):
    def send_command(
        self,
        command: str,
        params: Mapping[str, Any] | None = None,
    ) -> Any: ...

    def get_session(self) -> SessionInterface: ...
