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
        old_temp_file = str(browser.temp_dir.name)
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
    import sys # TEMP
    await asyncio.sleep(1)
    print("Counting".center(20, "-"), file=sys.stderr)
    count = browser._retry_delete_manual(old_temp_file)
    print(f"Found {count[0]} files, {count[1]} directories", file=sys.stderr)
    print(f"Errors: {count[2]}", file=sys.stderr)


    await asyncio.sleep(1)

    print("Deleting".center(20, "-"), file=sys.stderr)
    count = browser._retry_delete_manual(old_temp_file, delete=True)
    print(f"Errors: {count[2]}", file=sys.stderr)

    await asyncio.sleep(1)

    print("Counting".center(20, "-"), file=sys.stderr)
    count = browser._retry_delete_manual(old_temp_file)
    print(f"Found {count[0]} files, {count[1]} directories", file=sys.stderr)
    print(f"Errors: {count[2]}", file=sys.stderr)

@pytest.mark.asyncio(loop_scope="function")
async def test_no_context(capteesys, headless, debug, debug_browser):
    browser = await devtools.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    )
    old_temp_file = str(browser.temp_dir.name)
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
        import sys # TEMP
        await asyncio.sleep(1)
        print("Counting".center(20, "-"), file=sys.stderr)
        count = browser._retry_delete_manual(old_temp_file)
        print(f"Found {count[0]} files, {count[1]} directories", file=sys.stderr)
        print(f"Errors: {count[2]}", file=sys.stderr)


        await asyncio.sleep(1)

        print("Deleting".center(20, "-"), file=sys.stderr)
        count = browser._retry_delete_manual(old_temp_file, delete=True)
        print(f"Errors: {count[2]}", file=sys.stderr)

        await asyncio.sleep(1)

        print("Counting".center(20, "-"), file=sys.stderr)
        count = browser._retry_delete_manual(old_temp_file)
        print(f"Found {count[0]} files, {count[1]} directories", file=sys.stderr)
        print(f"Errors: {count[2]}", file=sys.stderr)
