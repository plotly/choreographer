from __future__ import annotations

from choreographer.browsers.chromium import Chromium
from choreographer.channels import Pipe


def _get_cli(tmp_path, **kwargs) -> list[str]:
    executable = tmp_path / "chrome"
    executable.touch()
    channel = Pipe()
    browser = Chromium(channel, executable, **kwargs)
    browser.pre_open()
    try:
        return list(browser.get_cli())
    finally:
        browser.clean()
        channel.close()


def test_proxy_server_argument(tmp_path, monkeypatch):
    monkeypatch.delenv("CHOREO_PROXY_SERVER", raising=False)

    cli = _get_cli(tmp_path, proxy_server="http://proxy.example:8080")

    assert "--proxy-server=http://proxy.example:8080" in cli


def test_proxy_server_environment_variable(tmp_path, monkeypatch):
    monkeypatch.setenv("CHOREO_PROXY_SERVER", "socks5://proxy.example:1080")

    cli = _get_cli(tmp_path)

    assert "--proxy-server=socks5://proxy.example:1080" in cli


def test_proxy_server_argument_overrides_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("CHOREO_PROXY_SERVER", "http://environment.example:8080")

    cli = _get_cli(tmp_path, proxy_server="http://argument.example:8080")

    assert "--proxy-server=http://argument.example:8080" in cli
    assert "--proxy-server=http://environment.example:8080" not in cli


def test_proxy_server_is_not_added_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("CHOREO_PROXY_SERVER", raising=False)

    cli = _get_cli(tmp_path)

    assert not any(arg.startswith("--proxy-server=") for arg in cli)


def test_none_proxy_server_uses_environment_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("CHOREO_PROXY_SERVER", "http://environment.example:8080")

    cli = _get_cli(tmp_path, proxy_server=None)

    assert "--proxy-server=http://environment.example:8080" in cli


def test_empty_proxy_server_uses_environment_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("CHOREO_PROXY_SERVER", "http://environment.example:8080")

    cli = _get_cli(tmp_path, proxy_server="")

    assert "--proxy-server=http://environment.example:8080" in cli
