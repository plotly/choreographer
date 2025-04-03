"""Provides the basic protocol class (the abstract base) for a protocol."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Mapping, MutableMapping, Sequence

    from choreographer.channels._interface_type import ChannelInterface


class BrowserImplInterface(Protocol):
    """Defines the basic interface of a channel."""

    # I guess we need to include __init__?
    def __init__(
        self,
        channel: ChannelInterface,
        path: Path | str | None = None,
        **kwargs: Any,
    ) -> None: ...
    def pre_open(self) -> None: ...
    def get_popen_args(self) -> Mapping[str, Any]: ...
    def get_cli(self) -> Sequence[str]: ...
    def get_env(self) -> MutableMapping[str, str]: ...
    def clean(self) -> None: ...
    def is_isolated(self) -> bool: ...
