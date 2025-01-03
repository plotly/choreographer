import asyncio
import os
import platform
import signal
import subprocess

import pytest
from async_timeout import timeout

import choreographer as choreo

# ruff: noqa: PLR0913 (lots of parameters)


@pytest.mark.asyncio(loop_scope="function")
async def test_context(capteesys, headless, debug, debug_browser, sandbox, gpu):
    async with (
        choreo.Browser(
            headless=headless,
            debug=debug,
            debug_browser=None if debug_browser else False,
            enable_sandbox=sandbox,
            enable_gpu=gpu,
        ) as browser,
        timeout(pytest.default_timeout),
    ):
        if sandbox and "ubuntu" in platform.version().lower():
            pytest.skip("Ubuntu doesn't support sandbox unless installed from snap.")
        temp_dir = browser.tmp_dir
        response = await browser.send_command(command="Target.getTargets")
        assert "result" in response and "targetInfos" in response["result"]  # noqa: PT018 combined assert
        assert len(response["result"]["targetInfos"]) != 0
        assert isinstance(browser.get_tab(), choreo.Tab)
        assert len(browser.get_tab().sessions) == 1
    print()  # this makes sure that capturing is working
    # stdout should be empty, but not
    # because capsys is broken, because nothing was print
    assert capteesys.readouterr().out == "\n", "stdout should be silent!"
    # let asyncio do some cleaning up if it wants, may prevent warnings
    await asyncio.sleep(0)
    assert not temp_dir.exists


@pytest.mark.asyncio(loop_scope="function")
async def test_no_context(capteesys, headless, debug, debug_browser, sandbox, gpu):
    browser = await choreo.Browser(
        headless=headless,
        debug=debug,
        debug_browser=None if debug_browser else False,
        enable_sandbox=sandbox,
        enable_gpu=gpu,
    )
    if sandbox and "ubuntu" in platform.version().lower():
        pytest.skip("Ubuntu doesn't support sandbox unless installed from snap.")
    temp_dir = browser.tmp_dir
    try:
        async with timeout(pytest.default_timeout):
            response = await browser.send_command(command="Target.getTargets")
            assert "result" in response and "targetInfos" in response["result"]  # noqa: PT018 combined assert
            assert len(response["result"]["targetInfos"]) != 0
            assert isinstance(browser.get_tab(), choreo.Tab)
            assert len(browser.get_tab().sessions) == 1
    finally:
        await browser.close()
    print()  # this make sure that capturing is working
    assert capteesys.readouterr().out == "\n", "stdout should be silent!"
    await asyncio.sleep(0)
    assert not temp_dir.exists


# Harass choreographer with a kill in this test to see if its clean in a way
# tempdir may survive protected by chromium subprocess surviving the kill
@pytest.mark.asyncio(loop_scope="function")
async def test_watchdog(capteesys, headless, debug, debug_browser):
    browser = await choreo.Browser(
        headless=headless,
        debug=debug,
        debug_browser=None if debug_browser else False,
    )

    if platform.system() == "Windows":
        # Blocking process here because it ensures the kill will occur rn
        subprocess.call(  # noqa: S603, ASYNC221 sanitize input, blocking process
            ["taskkill", "/F", "/T", "/PID", str(browser.subprocess.pid)],  # noqa: S607
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    else:
        os.kill(browser.subprocess.pid, signal.SIGKILL)
    await asyncio.sleep(1.5)

    with pytest.raises(
        (choreo.PipeClosedError, choreo.BrowserClosedError),
    ):
        await browser.send_command(command="Target.getTargets")

    await browser.close()
    await asyncio.sleep(0)
    print()
    assert capteesys.readouterr().out == "\n", "stdout should be silent!"
