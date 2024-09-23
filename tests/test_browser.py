import pytest
import devtools


url = (
    "https://plotly.com/",
    "https://plotly.com/python/",
    "https://plotly.com/graphing-libraries/",
    "https://plotly.com/python/getting-started/",
)


@pytest.mark.parametrize(
    "test_input_headless,test_input_debug,test_input_debug_browser",
    [
        (True, True, True),
        (True, True, False),
        (True, False, True),
        (True, False, False),
        (False, True, True),
        (False, True, False),
        (False, False, True),
        (False, False, False),
    ],
    ids=[
        "async_browser_1",
        "async_browser_2",
        "async_browser_3",
        "async_browser_4",
        "async_browser_5",
        "async_browser_6",
        "async_browser_7",
        "async_browser_8",
    ],
)
@pytest.mark.asyncio
async def test_async_browser(
    test_input_headless, test_input_debug, test_input_debug_browser
):
    async with devtools.Browser(
        headless=test_input_headless,
        debug=test_input_debug,
        debug_browser=test_input_debug_browser,
    ) as browser:
        tab_1 = await browser.create_tab(url[0])
        tab_2 = await browser.create_tab(url[1])
        session = await browser.create_session()
        assert isinstance(tab_1, devtools.tab.Tab)
        assert await browser.close_tab(tab_1) is not None
        assert browser.get_tab() == list(browser.tabs.values())[0]
        browser.remove_tab(tab_2)
        assert tab_2 not in browser.tabs
        assert isinstance(session, devtools.session.Session)
        assert (
            await browser.write_json({"id": 0, "method": "Target.getTargets"})
            is not None
        )
        assert await browser.populate_targets() is None
        assert tab_2.target_id in browser.tabs


@pytest.mark.parametrize(
    "test_input_headless,test_input_debug,test_input_debug_browser",
    [
        (True, True, True),
        (True, True, False),
        (True, False, True),
        (True, False, False),
        (False, True, True),
        (False, True, False),
        (False, False, True),
        (False, False, False),
    ],
    ids=[
        "sync_browser_1",
        "sync_browser_2",
        "sync_browser_3",
        "sync_browser_4",
        "sync_browser_5",
        "sync_browser_6",
        "sync_browser_7",
        "sync_browser_8",
    ],
)
def test_sync_browser(test_input_headless, test_input_debug, test_input_debug_browser):
    with devtools.Browser(
        headless=test_input_headless,
        debug=test_input_debug,
        debug_browser=test_input_debug_browser,
    ) as browser:
        print(browser)
        assert (
            browser.send_command(command="Target.createTarget", params={"url": url[1]})
            is not None
        )
        assert browser.write_json({"id": 0, "method": "Target.getTargets"}) is not None
        browser.loop = None
        assert browser.run_output_thread() is None
