import asyncio

import pytest

import devtools
@pytest.mark.asyncio
async def test_asyncio():
    await asyncio.sleep(0)

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

@pytest.mark.asyncio
async def test_no_context(headless, debug, debug_browser):
    browser = await devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    )

    # errors in this test will cause browser not to close
    # so lets make sure it does
    loop = asyncio.get_running_loop()
    exception_handler = loop.get_exception_handler()
    def close_browser(loop, context):
        browser.close() # posts task, doesn't need to be awaited
        if exception_handler:
            exception_handler(loop, context)
        else:
            loop.default_exception_handler(context)
    loop.set_exception_handler(close_browser)

    response = await browser.send_command(command="Target.getTargets")
    assert "result" in response and "targetInfos" in response["result"]
    assert len(response["result"]["targetInfos"]) != 0
    await browser.close()
