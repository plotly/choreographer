import pytest
import devtools


url = (
    "https://plotly.com/",
    "https://plotly.com/python/",
    "https://plotly.com/graphing-libraries/",
    "https://plotly.com/python/getting-started/",
)


@pytest.mark.parametrize(
    "test_input_debug", [True, False], ids=["async_debug", "async_no_debug"]
)
@pytest.mark.parametrize(
    "test_input_headless", [True, False], ids=["async_headless", "async_no_headless"]
)
@pytest.mark.parametrize(
    "test_input_debug_browser",
    [True, False],
    ids=["async_debug_browser", "async_no_debug_browser"],
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
        assert isinstance(session, devtools.session.Session)
        assert (
            await browser.write_json({"id": 0, "method": "Target.getTargets"})
            is not None
        )
        assert await browser.populate_targets() is None
        assert tab_2.target_id in browser.tabs


@pytest.mark.parametrize(
    "test_input_debug", [True, False], ids=["sync_debug", "sync_no_debug"]
)
@pytest.mark.parametrize(
    "test_input_headless", [True, False], ids=["sync_headless", "sync_no_headless"]
)
@pytest.mark.parametrize(
    "test_input_debug_browser",
    [True, False],
    ids=["sync_debug_browser", "sync_no_debug_browser"],
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
