import pytest

import devtools

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
    assert capsys.readouterr().out == "", "stdout should be silent!"

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
        assert capsys.readouterr().out == "", "stdout should be silent!"
