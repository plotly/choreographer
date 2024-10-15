import pytest
import pytest_asyncio

import choreograph as choreo


async def print_obj(obj):
    print(obj)


def check_response_dictionary(response_received, response_expected):
    for k, v in response_expected.items():
        if isinstance(v, dict):
            check_response_dictionary(v, response_expected[k])
        return k in response_received and response_received[k] == v


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def tab(browser):
    tab_browser = await browser.create_tab("")
    yield tab_browser
    await browser.close_tab(tab_browser)


@pytest.mark.asyncio
async def test_create_and_close_session(tab):
    session = await tab.create_session()
    assert isinstance(session, choreo.session.Session)
    await tab.close_session(session)
    assert session.session_id not in tab.sessions


@pytest.mark.asyncio
async def test_send_command(tab):
    response = await tab.send_command("Page.enable")
    assert check_response_dictionary(response, {"result": {}})


@pytest.mark.asyncio
async def test_subscribe_once(tab):
    await tab.send_command("Page.enable")
    tab.subscribe_once("Page.*")
    assert "Page.*" in list(tab.sessions.values())[0].subscriptions_futures


@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe(tab):
    await tab.send_command("Page.enable")
    tab.subscribe("*", print_obj, True)
    assert "*" in list(tab.sessions.values())[0].subscriptions
    tab.subscribe("INVALID", print_obj, False)
    assert "INVALID" in list(tab.sessions.values())[0].subscriptions
    tab.unsubscribe("INVALID")
    assert "INVALID" not in list(tab.sessions.values())[0].subscriptions
