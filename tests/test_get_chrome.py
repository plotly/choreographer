import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest

from choreographer.cli._cli_utils import get_chrome_sync


@pytest.fixture
def mock_last_known_good_json():
    """Mock the last known good chrome version."""
    return {
        "version": "135.0.7011.0",
        "revision": "1418433",
        "downloads": {
            "chrome": [
                {"platform": "linux64", "url": "https://example.com/linux64.zip"},
                {"platform": "mac-arm64", "url": "https://example.com/mac-arm64.zip"},
                {"platform": "win64", "url": "https://example.com/win64.zip"},
            ],
        },
    }


# Thanks Claude!
def test_get_chrome_sync_download_behavior(
    tmp_path,
    mock_last_known_good_json,
):
    """Test chrome download/skip behavior: existing, force, version change."""
    exe_path = tmp_path / "chrome-linux64" / "chrome"
    version_tag = tmp_path / "version_tag.txt"

    # Setup: create a fake existing installation with matching version
    exe_path.parent.mkdir(parents=True)
    exe_path.write_text("old chrome")
    version_tag.write_text("135.0.7011.0\n1418433")

    # Mock the URL download
    def create_mock_zip_response():
        mock_response = MagicMock()
        # Create a fresh zip buffer each time
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("chrome-linux64/chrome", "newly downloaded chrome")
        zip_buffer.seek(0)
        mock_response.read.return_value = zip_buffer.read()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    # Patch json.load to return our mock data (avoid broad Path.read_text patch)
    with patch("json.load", return_value=mock_last_known_good_json), patch(
        "urllib.request.urlopen",
        side_effect=lambda url: create_mock_zip_response(),  # noqa: ARG005
    ):
        # a) First call without force - should return existing, no download
        result = get_chrome_sync(arch="linux64", path=tmp_path, force=False)
        assert result == exe_path
        assert exe_path.read_text() == "old chrome"  # Should still be old

        # b) Call with force=True - should download and replace
        result = get_chrome_sync(arch="linux64", path=tmp_path, force=True)
        assert result == exe_path
        assert exe_path.read_text() == "newly downloaded chrome"
        assert version_tag.read_text() == "135.0.7011.0\n1418433"

        # c) Call again without force - should return existing, no re-download
        # (Modify the file to verify it doesn't get re-downloaded)
        exe_path.write_text("manually modified chrome")
        result = get_chrome_sync(arch="linux64", path=tmp_path, force=False)
        assert result == exe_path
        assert exe_path.read_text() == "manually modified chrome"

        # d) Change version on disk - should trigger download (version mismatch)
        version_tag.write_text("999.0.0.0\n999999")  # Old/different version
        result = get_chrome_sync(arch="linux64", path=tmp_path, force=False)
        assert result == exe_path
        assert exe_path.read_text() == "newly downloaded chrome"
        assert version_tag.read_text() == "135.0.7011.0\n1418433"  # Updated to new
