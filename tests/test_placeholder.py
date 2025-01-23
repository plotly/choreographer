import asyncio

import pytest

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")


async def test_placeholder(browser):
    assert "result" in await browser.send_command("Target.getTargets")
    await asyncio.sleep(0)
