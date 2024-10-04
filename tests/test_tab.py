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


def check_response_dictionary(response_received, response_expected):
    for k, v in response_expected.items():
        if isinstance(v, dict):
            check_response_dictionary(v, response_expected[k])
        return k in response_received and response_received[k] == v


@pytest.mark.asyncio
async def test_async_tab(headless, debug, debug_browser):
    async with devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
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
        response = await tab_1.send_command("Page.enable")
        assert check_response_dictionary(response, {"result": {}})
        tab_1.subscribe_once("Page.*")
        assert "Page.*" in list(tab_1.sessions.values())[0].subscriptions_futures
        tab_1.subscribe("*", print_obj, True)
        assert "*" in list(tab_1.sessions.values())[0].subscriptions
        tab_1.subscribe("INVALID", print_obj, False)
        assert "INVALID" in list(tab_1.sessions.values())[0].subscriptions
        tab_1.unsubscribe("INVALID")
        assert "INVALID" not in list(tab_1.sessions.values())[0].subscriptions
        await tab_1.send_command("Page.navigate", params=dict(url=url[3]))
        await tab_2.send_command("Page.navigate", params=dict(url=url[1]))
