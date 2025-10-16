import os
import platform
import stat
from pathlib import Path

import pytest
from choreographer.browsers.chromium import _find_a_chromium_based_browser


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
        _r = _find_a_chromium_based_browser(skip_local=True, skip_typical=True)
        assert _r
        assert Path(_r).stem == _n
        _p.unlink()

    os.environ["PATH"] = _o
