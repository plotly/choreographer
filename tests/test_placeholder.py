import pytest
import asyncio

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

async def test_placeholder(capsys, browser):
    print("")
    assert capsys.readouterr().out == "\n", "stdout should be silent!"

    assert "result" in await browser.send_command("Target.getTargets")

    await asyncio.sleep(0)
