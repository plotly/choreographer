import asyncio

import devtools

import pytest
from async_timeout import timeout


@pytest.mark.asyncio
async def test_context(capsys, headless, debug, debug_browser):
    async with devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    ) as browser, timeout(2):
            response = await browser.send_command(command="Target.getTargets")
            assert "result" in response and "targetInfos" in response["result"]
            assert (len(response["result"]["targetInfos"]) != 0) != headless
    print("") # this makes sure that capturing is working
    # stdout should be empty, but not because capsys is broken, because nothing was print
    assert capsys.readouterr().out == "\n", "stdout should be silent!"
    # let asyncio do some cleaning up if it wants, may prevent warnings
    await asyncio.sleep(0)

@pytest.mark.asyncio
async def test_no_context(capsys, headless, debug, debug_browser):
    browser = await devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    )
    try:
        async with timeout(2):
            response = await browser.send_command(command="Target.getTargets")
            assert "result" in response and "targetInfos" in response["result"]
            assert (len(response["result"]["targetInfos"]) != 0) != headless
    finally:
        await browser.close()
        print("") # this make sure that capturing is working
        assert capsys.readouterr().out == "\n", "stdout should be silent!"
        await asyncio.sleep(0)
