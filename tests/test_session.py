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
async def test_async_session(
    test_input_headless, test_input_debug, test_input_debug_browser
):
    async with devtools.Browser(
        headless=test_input_headless,
        debug=test_input_debug,
        debug_browser=test_input_debug_browser,
    ) as browser:
        session_1 = await browser.create_session()
        assert isinstance(session_1, devtools.session.Session)
        assert session_1.send_command("Page.enable")
        assert session_1.subscribe_once("Page")
        assert "Page" in session_1.subscriptions_futures
        assert session_1.subscribe("*", print_obj, True) is None
        assert session_1.subscribe("INVALID", print_obj, False) is None
        assert "*" in session_1.subscriptions
        assert session_1.unsubscribe("INVALID") is None
        assert "INVALID" not in session_1.subscriptions
        await session_1.send_command(
            "Page.navigate", params=dict(url=url[2])
        ) is not None
        await session_1.send_command(
            "Page.navigate", params=dict(url=url[-1])
        ) is not None
