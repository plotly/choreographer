import asyncio

import devtools

import pytest
from async_timeout import timeout


@pytest.mark.asyncio(loop_scope="function")
async def test_context(capteesys, headless, debug, debug_browser):
    async with devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    ) as browser, timeout(pytest.default_timeout):
            response = await browser.send_command(command="Target.getTargets")
            assert "result" in response and "targetInfos" in response["result"]
            assert (len(response["result"]["targetInfos"]) != 0) != headless
            if not headless:
                assert isinstance(browser.get_tab(), devtools.tab.Tab)
                assert len(browser.get_tab().sessions) == 1
    print("") # this makes sure that capturing is working
    # stdout should be empty, but not because capsys is broken, because nothing was print
    assert capteesys.readouterr().out == "\n", "stdout should be silent!"
    # let asyncio do some cleaning up if it wants, may prevent warnings
    await asyncio.sleep(0)

@pytest.mark.asyncio(loop_scope="function")
async def test_no_context(capteesys, headless, debug, debug_browser):
    browser = await devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    )
    try:
        async with timeout(pytest.default_timeout):
            response = await browser.send_command(command="Target.getTargets")
            assert "result" in response and "targetInfos" in response["result"]
            assert (len(response["result"]["targetInfos"]) != 0) != headless
            if not headless:
                assert isinstance(browser.get_tab(), devtools.tab.Tab)
                assert len(browser.get_tab().sessions) == 1
    finally:
        await browser.close()
        print("") # this make sure that capturing is working
        assert capteesys.readouterr().out == "\n", "stdout should be silent!"
        await asyncio.sleep(0)
