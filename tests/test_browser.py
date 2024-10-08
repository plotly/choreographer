import warnings
import pytest
import devtools
import devtools.protocol


url = (
    "https://plotly.com/",
    "https://plotly.com/python/",
)


@pytest.mark.asyncio
async def test_create_and_close_tab(browser):
    tab = await browser.create_tab(url[0])
    assert isinstance(tab, devtools.tab.Tab)
    assert tab.target_id in browser.tabs
    await browser.close_tab(tab)
    assert tab.target_id not in browser.tabs


@pytest.mark.asyncio
async def test_create_and_close_session(browser):
    with pytest.warns(devtools.protocol.ExperimentalFeatureWarning):
        session = await browser.create_session()
        warnings.warn(
            "Creating new sessions on Browser() only works with some versions of Chrome, it is experimental.",
            devtools.protocol.ExperimentalFeatureWarning,
        )
    assert isinstance(session, devtools.session.Session)
    assert session.session_id in browser.sessions
    await browser.close_session(session)
    assert session.session_id not in browser.sessions


@pytest.mark.asyncio
async def test_browser_write_json(browser):
    response = await browser.write_json({"id": 0, "method": "Target.getTargets"})
    assert "result" in response and "targetInfos" in response["result"]


@pytest.mark.asyncio
async def test_browser_send_command(browser):
    response = await browser.send_command(command="Target.getTargets")
    assert "result" in response and "targetInfos" in response["result"]


@pytest.mark.asyncio
async def test_populate_targets(browser):
    await browser.send_command(command="Target.createTarget", params={"url": url[1]})
    await browser.populate_targets()
    if browser.headless is False:
        assert len(browser.tabs) > 1
    else:
        assert len(browser.tabs) == 1


def test_get_tab(browser):
    if browser.headless:
        assert browser.get_tab() is None
    else:
        assert browser.get_tab() == list(browser.tabs.values())[0]
