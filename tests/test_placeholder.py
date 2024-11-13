import asyncio

import pytest

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

async def test_placeholder(browser, capteesys):
    print("")
    assert "result" in await browser.send_command("Target.getTargets")
    out, err = capteesys.readouterr()
    assert out == "\n", f"stdout should be silent! -{out}-{err}-"
    await asyncio.sleep(0)
