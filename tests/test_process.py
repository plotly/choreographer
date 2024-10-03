import pytest
import devtools


@pytest.mark.asyncio
async def test_async_tab(headless, debug, debug_browser):
    browser = await devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    )
    response = await browser.send_command(command="Target.getTargets")
    assert "result" in response and "targetInfos" in response["result"]
    await browser.close()
