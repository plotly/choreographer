import asyncio

import logistro
import pytest

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)


async def test_placeholder(browser):
    _logger.info("testing...")
    assert "result" in await browser.send_command("Target.getTargets")
    await asyncio.sleep(0)
