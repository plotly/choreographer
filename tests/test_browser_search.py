import os
import platform
import stat
import sys
from pathlib import Path

import pytest

from choreographer.browsers import chromium
from choreographer.cli._cli_utils import get_chrome_download_path


def test_internal(tmp_path):
    if platform.system() == "Windows":
        pytest.skip("Windows hard to trick about PATH.")
    _o = str(os.environ["PATH"])
    os.environ["PATH"] = str(tmp_path)
    print(os.environ["PATH"])
    names = ["chrome", "chromium", "msedge", "brave", "vivaldi"]
    paths = []

    for n in names:
        p = tmp_path / (n)
        p.touch()
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        paths.append(p)

    for _p, _n in zip(paths, names):
        _r = chromium.Chromium.find_browser(skip_local=True, skip_typical=True)
        assert _r
        assert Path(_r).stem == _n
        _p.unlink()

    os.environ["PATH"] = _o


def test_canary():
    # This ensures we are finding the local install
    if os.getenv("TEST_SYSTEM_BROWSER"):
        pytest.skip("Okay, no need to test for local.")
    _r = chromium.Chromium.find_browser(skip_local=False, skip_typical=True)
    print(sys.path, file=sys.stderr)
    assert _r
    assert Path(_r) == get_chrome_download_path()
    # if _r != get_chrome_download_path():
