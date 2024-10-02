import pytest
import devtools
import asyncio


url = (
    "https://plotly.com/",
    "https://plotly.com/python/",
    "https://plotly.com/graphing-libraries/",
    "https://plotly.com/python/getting-started/",
)


async def print_obj(obj):
    print(obj)


@pytest.mark.parametrize(
    "test_input_debug", [True, False], ids=["async_debug", "async_no_debug"]
)
@pytest.mark.parametrize(
    "test_input_headless", [True, False], ids=["async_headless", "async_no_headless"]
)
@pytest.mark.parametrize(
    "test_input_debug_browser",
    [True, False],
    ids=["async_debug_browser", "async_no_debug_browser"],
)
@pytest.mark.asyncio
async def test_async_tab(
    test_input_headless, test_input_debug, test_input_debug_browser
):
    async with devtools.Browser(
        headless=test_input_headless,
        debug=test_input_debug,
        debug_browser=test_input_debug_browser,
    ) as browser:
        tab_1 = await browser.create_tab(url[0])
        tab_2 = await browser.create_tab(url[1])
        session_1 = await tab_1.create_session()
        session_2 = await tab_1.create_session()
        assert isinstance(tab_1, devtools.tab.Tab)
        assert isinstance(tab_2, devtools.tab.Tab)
        assert isinstance(session_1, devtools.session.Session)
        assert isinstance(session_2, devtools.session.Session)
        assert await tab_1.close_session(session_1) is not None
        await tab_1.send_command("Page.enable")
        assert tab_1.subscribe_once("Page") is None
        assert "Page" in list(tab_1.sessions.values())[0].subscriptions_futures
        assert tab_1.subscribe("*", print_obj, True) is None
        assert tab_1.subscribe("INVALID", print_obj, False) is None
        assert "*" in list(tab_1.sessions.values())[0].subscriptions
        assert tab_1.unsubscribe("INVALID") is None
        assert "INVALID" not in list(tab_1.sessions.values())[0].subscriptions
        await tab_1.send_command("Page.navigate", params=dict(url=url[3]))
        await tab_2.send_command("Page.navigate", params=dict(url=url[1]))
