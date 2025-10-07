import asyncio
import os
import platform
import signal
import subprocess

import choreographer as choreo
import logistro
import pytest
from async_timeout import timeout
from choreographer import errors

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)


@pytest.mark.asyncio(loop_scope="function")
async def test_context(headless, sandbox, gpu):
    _logger.info("testing...")
    async with timeout(pytest.default_timeout):  # type: ignore[reportAttributeAccessIssue]
        async with choreo.Browser(
            headless=headless,
            enable_sandbox=sandbox,
            enable_gpu=gpu,
        ) as browser:
            if sandbox and "ubuntu" in platform.version().lower():
                pytest.skip(
                    "Ubuntu doesn't support sandbox unless installed from snap.",
                )
            elif sandbox:
                _logger.info(
                    "Not skipping sandbox: "
                    f"Sandbox: {sandbox},"
                    f"Version: {platform.version().lower()}",
                )
            response = await browser.send_command(command="Target.getTargets")
            assert "result" in response and "targetInfos" in response["result"]  # noqa: PT018 combined assert
            if len(response["result"]["targetInfos"]) == 0:
                await browser.create_tab()
            assert isinstance(browser.get_tab(), choreo.Tab)
            tab = browser.get_tab()
            assert tab is not None
            assert len(tab.sessions) == 1
        # let asyncio do some cleaning up if it wants, may prevent warnings
        await asyncio.sleep(0)
        if hasattr(browser._browser_impl, "tmp_dir"):  # noqa: SLF001
            assert not browser._browser_impl.tmp_dir.exists  # type: ignore[reportAttributeAccessIssue] # noqa: SLF001


@pytest.mark.asyncio(loop_scope="function")
async def test_no_context(headless, sandbox, gpu):
    _logger.info("testing...")
    browser = await choreo.Browser(
        headless=headless,
        enable_sandbox=sandbox,
        enable_gpu=gpu,
    )
    if sandbox and "ubuntu" in platform.version().lower():
        pytest.skip("Ubuntu doesn't support sandbox unless installed from snap.")
    try:
        async with timeout(pytest.default_timeout):  # type: ignore[reportAttributeAccessIssue]
            response = await browser.send_command(command="Target.getTargets")
            assert "result" in response and "targetInfos" in response["result"]  # noqa: PT018 combined assert
            if len(response["result"]["targetInfos"]) == 0:
                await browser.create_tab()
            assert isinstance(browser.get_tab(), choreo.Tab)
            tab = browser.get_tab()
            assert tab is not None
            assert len(tab.sessions) == 1
    finally:
        await browser.close()
    await asyncio.sleep(0)
    if hasattr(browser._browser_impl, "tmp_dir"):  # noqa: SLF001
        assert not browser._browser_impl.tmp_dir.exists  # type: ignore[reportAttributeAccessIssue] # noqa: SLF001


# Harass choreographer with a kill in this test to see if its clean in a way
# tempdir may survive protected by chromium subprocess surviving the kill
@pytest.mark.asyncio(loop_scope="function")
async def test_watchdog(headless):
    _logger.info("testing...")
    browser = await choreo.Browser(
        headless=headless,
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
        (errors.ChannelClosedError, errors.BrowserClosedError),
    ):
        await browser.send_command(command="Target.getTargets")

    await browser.close()
    await asyncio.sleep(0)
