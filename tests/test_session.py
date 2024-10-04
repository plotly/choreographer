import pytest
import devtools


url = (
    "https://plotly.com/",
    "https://plotly.com/python/",
    "https://plotly.com/graphing-libraries/",
    "https://plotly.com/python/getting-started/",
)


async def print_obj(obj):
    print(obj)


@pytest.mark.asyncio
async def test_async_session(headless, debug, debug_browser):
    async with devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    ) as browser:
        session_1 = await browser.create_session()
        assert isinstance(session_1, devtools.session.Session)
        await session_1.send_command("Page.enable")
        session_1.subscribe_once("Page.*")
        assert "Page.*" in session_1.subscriptions_futures
        session_1.subscribe("*", print_obj, True)
        assert "*" in session_1.subscriptions
        session_1.subscribe("INVALID", print_obj, False)
        assert "INVALID" in session_1.subscriptions
        session_1.unsubscribe("INVALID")
        assert "INVALID" not in session_1.subscriptions
        await session_1.send_command("Page.navigate", params=dict(url=url[2]))
        await session_1.send_command("Page.navigate", params=dict(url=url[-1]))
