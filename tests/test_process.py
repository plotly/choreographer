import pytest
import devtools

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
        response = await browser.send_command(command="Target.getTargets")
        assert "result" in response and "targetInfos" in response["result"]