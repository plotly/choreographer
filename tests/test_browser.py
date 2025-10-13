import choreographer as choreo
import logistro
import pytest
from choreographer import errors
from choreographer.protocol import devtools_async

# We no longer use live URLs to as not depend on the network

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)


@pytest.mark.asyncio
async def test_create_and_close_tab(browser):
    _logger.info("testing...")
    tab = await browser.create_tab("")
    assert isinstance(tab, choreo.Tab)
    assert tab.target_id in browser.tabs
    await browser.close_tab(tab)
    assert tab.target_id not in browser.tabs


@pytest.mark.asyncio
async def test_create_and_close_session(browser):
    _logger.info("testing...")
    with pytest.warns(errors.ExperimentalFeatureWarning):
        session = await browser.create_session()
    assert isinstance(session, devtools_async.Session)
    assert session.session_id in browser.sessions
    await browser.close_session(session)
    assert session.session_id not in browser.sessions


# Along with testing, this could be repurposed as well to diagnose
# This deserves some thought re. difference between write_json and send_command
@pytest.mark.asyncio
async def test_broker_write_json(browser):
    _logger.info("testing...")
    # Test valid request with correct id and method
    response = await browser._broker.write_json(  # noqa: SLF001
        {"id": 0, "method": "Target.getTargets"},
    )
    assert "result" in response and "targetInfos" in response["result"]  # noqa: PT018 I like this assertion

    # Test invalid method name should return error
    response = await browser._broker.write_json(  # noqa: SLF001
        {"id": 2, "method": "dkadklqwmd"},
    )
    assert "error" in response

    # Test missing 'id' key
    with pytest.raises(
        errors.MissingKeyError,
    ):
        await browser._broker.write_json(  # noqa: SLF001
            {"method": "Target.getTargets"},
        )

    # Test missing 'method' key
    with pytest.raises(
        errors.MissingKeyError,
    ):
        await browser._broker.write_json(  # noqa: SLF001
            {"id": 1},
        )

    # Test empty dictionary
    with pytest.raises(
        errors.MissingKeyError,
    ):
        await browser._broker.write_json({})  # noqa: SLF001

    # Test invalid parameter in the message
    with pytest.raises(
        RuntimeError,
    ):
        await browser._broker.write_json(  # noqa: SLF001
            {"id": 0, "method": "Target.getTargets", "invalid_parameter": "kamksamdk"},
        )

    # Test int method should return error
    with pytest.raises(
        errors.MessageTypeError,
    ):
        await browser._broker.write_json(  # noqa: SLF001
            {"id": 3, "method": 12345},
        )

    # Test non-integer id should return error
    with pytest.raises(
        errors.MessageTypeError,
    ):
        await browser._broker.write_json(  # noqa: SLF001
            {"id": "string", "method": "Target.getTargets"},
        )


@pytest.mark.asyncio
async def test_browser_send_command(browser):
    _logger.info("testing...")
    # Test valid request with correct command
    response = await browser.send_command(command="Target.getTargets")
    assert "result" in response and "targetInfos" in response["result"]  # noqa: PT018 I like this assertion

    # Test invalid method name should return error
    response = await browser.send_command(command="dkadklqwmd")
    assert "error" in response

    # Test int method should return error
    with pytest.raises(
        errors.MessageTypeError,
    ):
        await browser.send_command(command=12345)


@pytest.mark.asyncio
async def test_populate_targets(browser):
    _logger.info("testing...")
    await browser.send_command(command="Target.createTarget", params={"url": ""})
    await browser.populate_targets()
    assert len(browser.tabs) >= 1


@pytest.mark.asyncio
async def test_get_tab(browser):
    _logger.info("testing...")
    await browser.create_tab("")
    assert browser.get_tab() == next(iter(browser.tabs.values()))
    await browser.create_tab()
    await browser.create_tab("")
    assert browser.get_tab() == next(iter(browser.tabs.values()))
