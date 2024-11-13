import asyncio

import pytest
import pytest_asyncio

import choreographer as choreo


def check_response_dictionary(response_received, response_expected):
    for k, v in response_expected.items():
        if isinstance(v, dict):
            check_response_dictionary(v, response_expected[k])
        assert (
            k in response_received and response_received[k] == v
        ), "Expected: {response_expected}\nReceived: {response_received}"


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def tab(browser):
    tab_browser = await browser.create_tab("")
    yield tab_browser
    try:
        await browser.close_tab(tab_browser)
    except choreo.browser.BrowserClosedError:
        pass


@pytest.mark.asyncio
async def test_create_and_close_session(tab):
    session = await tab.create_session()
    assert isinstance(session, choreo.session.Session)
    await tab.close_session(session)
    assert session.session_id not in tab.sessions


@pytest.mark.asyncio
async def test_tab_send_command(tab):
    # Test valid request with correct command
    response = await tab.send_command(command="Page.enable")
    check_response_dictionary(response, {"result": {}})

    # Test invalid method name should return error
    response = await tab.send_command(command="dkadklqwmd")
    assert "error" in response

    # Test int method should return error
    with pytest.raises(
        choreo.protocol.MessageTypeError,
    ):
        await tab.send_command(command=12345)


@pytest.mark.asyncio
async def test_subscribe_once(tab):
    subscription_result = tab.subscribe_once("Page.*")
    assert "Page.*" in list(tab.sessions.values())[0].subscriptions_futures
    _ = await tab.send_command("Page.enable")
    _ = await tab.send_command("Page.reload")
    _ = await subscription_result
    assert not subscription_result.exception()


@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe(tab):
    counter = 0
    old_counter = counter

    async def count_event(r):
        nonlocal counter
        counter += 1

    tab.subscribe("Page.*", count_event)
    assert "Page.*" in list(tab.sessions.values())[0].subscriptions
    await tab.send_command("Page.enable")
    await tab.send_command("Page.reload")
    await asyncio.sleep(0.5)
    assert counter > old_counter

    tab.unsubscribe("Page.*")
    old_counter = counter

    assert "Page.*" not in list(tab.sessions.values())[0].subscriptions
    await tab.send_command("Page.enable")
    await tab.send_command("Page.reload")
    assert old_counter == counter
