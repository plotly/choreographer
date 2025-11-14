"""Defaults used when arguments not supplied."""

from pathlib import Path

from platformdirs import PlatformDirs

default_download_path = (
    Path(
        PlatformDirs("choreographer", "plotly").user_data_dir,
    )
    / "deps"
)
"""The path where we download chrome if no path argument is supplied."""
