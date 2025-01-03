import pytest

import choreographer as choreo

# We no longer use live URLs to as not depend on the network


@pytest.mark.asyncio
async def test_create_and_close_tab(browser):
    tab = await browser.create_tab("")
    assert isinstance(tab, choreo.Tab)
    assert tab.target_id in browser.tabs
    await browser.close_tab(tab)
    assert tab.target_id not in browser.tabs


@pytest.mark.asyncio
async def test_create_and_close_session(browser):
    with pytest.warns(choreo.protocol.ExperimentalFeatureWarning):
        session = await browser.create_session()
    assert isinstance(session, choreo.protocol.Session)
    assert session.session_id in browser.sessions
    await browser.close_session(session)
    assert session.session_id not in browser.sessions


# Along with testing, this could be repurposed as well to diagnose
# This deserves some thought re. difference between write_json and send_command
@pytest.mark.asyncio
async def test_browser_write_json(browser):
    # Test valid request with correct id and method
    response = await browser.write_json({"id": 0, "method": "Target.getTargets"})
    assert "result" in response and "targetInfos" in response["result"]  # noqa: PT018 I like this assertion

    # Test invalid method name should return error
    response = await browser.write_json({"id": 2, "method": "dkadklqwmd"})
    assert "error" in response

    # Test missing 'id' key
    with pytest.raises(
        choreo.protocol.MissingKeyError,
    ):
        await browser.write_json({"method": "Target.getTargets"})

    # Test missing 'method' key
    with pytest.raises(
        choreo.protocol.MissingKeyError,
    ):
        await browser.write_json({"id": 1})

    # Test empty dictionary
    with pytest.raises(
        choreo.protocol.MissingKeyError,
    ):
        await browser.write_json({})

    # Test invalid parameter in the message
    with pytest.raises(
        RuntimeError,
    ):
        await browser.write_json(
            {"id": 0, "method": "Target.getTargets", "invalid_parameter": "kamksamdk"},
        )

    # Test int method should return error
    with pytest.raises(
        choreo.protocol.MessageTypeError,
    ):
        await browser.write_json({"id": 3, "method": 12345})

    # Test non-integer id should return error
    with pytest.raises(
        choreo.protocol.MessageTypeError,
    ):
        await browser.write_json({"id": "string", "method": "Target.getTargets"})


@pytest.mark.asyncio
async def test_browser_send_command(browser):
    # Test valid request with correct command
    response = await browser.send_command(command="Target.getTargets")
    assert "result" in response and "targetInfos" in response["result"]  # noqa: PT018 I like this assertion

    # Test invalid method name should return error
    response = await browser.send_command(command="dkadklqwmd")
    assert "error" in response

    # Test int method should return error
    with pytest.raises(
        choreo.protocol.MessageTypeError,
    ):
        await browser.send_command(command=12345)


@pytest.mark.asyncio
async def test_populate_targets(browser):
    await browser.send_command(command="Target.createTarget", params={"url": ""})
    await browser.populate_targets()
    assert len(browser.tabs) >= 1


@pytest.mark.asyncio
async def test_get_tab(browser):
    await browser.create_tab("")
    assert browser.get_tab() == next(iter(browser.tabs.values()))
    await browser.create_tab()
    await browser.create_tab("")
    assert browser.get_tab() == next(iter(browser.tabs.values()))
