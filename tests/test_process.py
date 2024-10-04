import pytest

import devtools

@pytest.mark.timeout(method="thread")
@pytest.mark.asyncio
async def test_context(
    headless, debug, debug_browser
):
    async with devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    ) as browser:
        response = await browser.send_command(command="Target.getTargets")
        assert "result" in response and "targetInfos" in response["result"]
        assert (len(response["result"]["targetInfos"]) != 0)

@pytest.mark.timeout(method="thread")
@pytest.mark.asyncio
async def test_no_context(headless, debug, debug_browser):
    browser = await devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    )
    try:
        response = await browser.send_command(command="Target.getTargets")
        assert "result" in response and "targetInfos" in response["result"]
        assert len(response["result"]["targetInfos"]) != 0
    finally:
        await browser.close()
