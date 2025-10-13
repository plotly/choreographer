import asyncio

import logistro
import pytest
from choreographer import errors
from choreographer.protocol import devtools_async

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)


# this ignores extra stuff in received- only that we at least have what is expected
def check_response_dictionary(response_received, response_expected):
    for k, v in response_expected.items():
        if isinstance(v, dict):
            check_response_dictionary(v, v)
        assert (
            response_received.get(
                k,
                float("NaN"),
            )
            == v
        ), f"Expected: {response_expected}\nReceived: {response_received}"


@pytest.mark.asyncio
async def test_create_and_close_session(browser):
    _logger.info("testing...")
    tab = await browser.create_tab("")
    session = await tab.create_session()
    assert isinstance(session, devtools_async.Session)
    await tab.close_session(session)
    assert session.session_id not in tab.sessions


@pytest.mark.asyncio
async def test_tab_send_command(browser):
    _logger.info("testing...")
    tab = await browser.create_tab("")
    # Test valid request with correct command
    response = await tab.send_command(command="Page.enable")
    check_response_dictionary(response, {"result": {}})

    # Test invalid method name should return error
    response = await tab.send_command(command="dkadklqwmd")
    assert "error" in response

    # Test int method should return error
    with pytest.raises(
        errors.MessageTypeError,
    ):
        await tab.send_command(command=12345)


@pytest.mark.asyncio
async def test_subscribe_once(browser):
    _logger.info("testing...")
    tab = await browser.create_tab("")
    subscription_result = tab.subscribe_once("Page.*")
    _ = await tab.send_command("Page.enable")
    _ = await tab.send_command("Page.reload")
    _ = await subscription_result
    assert not subscription_result.exception()


@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe(browser):
    _logger.info("testing...")
    tab = await browser.create_tab("")
    counter = 0
    old_counter = counter

    async def count_event(_r):
        nonlocal counter
        counter += 1

    tab.subscribe("Page.*", count_event)
    assert "Page.*" in next(iter(tab.sessions.values())).subscriptions
    await tab.send_command("Page.enable")
    await tab.send_command("Page.reload")
    await asyncio.sleep(0.5)
    assert counter > old_counter

    tab.unsubscribe("Page.*")
    old_counter = counter

    assert "Page.*" not in next(iter(tab.sessions.values())).subscriptions
    await tab.send_command("Page.enable")
    await tab.send_command("Page.reload")
    assert old_counter == counter
