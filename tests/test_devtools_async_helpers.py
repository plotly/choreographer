import asyncio

import logistro
import pytest

from choreographer.protocol.devtools_async_helpers import (
    create_and_wait,
    execute_js_and_wait,
    navigate_and_wait,
)

pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)


# Errata: don't use data urls, whether or not they load is variable
# depends on how long chrome has been open for, how they were entered,
# etc


@pytest.mark.asyncio
async def test_create_and_wait(browser):
    """Test create_and_wait with both valid data URL and blank URL."""
    _logger.info("testing create_and_wait...")

    # Count tabs before
    initial_tab_count = len(browser.tabs)

    # Create a simple HTML page as a data URL
    data_url = "https://www.example.com"

    # Test 1: Create tab with data URL - should succeed
    tab1 = await create_and_wait(browser, url=data_url, timeout=5.0)
    assert tab1 is not None

    # Verify the page loaded correctly using execute_js_and_wait
    result = await execute_js_and_wait(tab1, "window.location.href", timeout=5.0)
    location = result["result"]["result"]["value"]
    assert location.startswith(data_url)

    # Test 2: Create tab without URL - should succeed (blank page)
    tab2 = await create_and_wait(browser, url="", timeout=5.0)
    assert tab2 is not None

    # Verify we have 2 more tabs
    final_tab_count = len(browser.tabs)
    assert final_tab_count == initial_tab_count + 2

    # Test 3: Create tab with bad URL that won't load - should timeout
    with pytest.raises(asyncio.TimeoutError):
        await create_and_wait(browser, url="http://192.0.2.1:9999", timeout=0.5)


@pytest.mark.asyncio
async def test_navigate_and_wait(browser):
    """Test navigate_and_wait with both valid data URL and bad URL."""
    _logger.info("testing navigate_and_wait...")
    # Create two blank tabs first
    tab = await browser.create_tab("")

    # navigating to dataurls seems to be fine right now,
    # but if one day you have an error here,
    # change to the strategy above

    # Create a data URL with identifiable content
    html_content1 = "<html><body><h1>Navigation Test 1</h1></body></html>"
    data_url1 = f"data:text/html,{html_content1}"

    html_content2 = "<html><body><h1>Navigation Test 2</h1></body></html>"
    data_url2 = f"data:text/html,{html_content2}"

    # Test 1: Navigate first tab to valid data URL - should succeed
    result_tab1 = await navigate_and_wait(tab, url=data_url1, timeout=5.0)
    assert result_tab1 is tab

    # Verify the navigation succeeded using execute_js_and_wait
    result = await execute_js_and_wait(tab, "window.location.href", timeout=5.0)
    location = result["result"]["result"]["value"]
    assert location.startswith("data:text/html")

    # Test 2: Navigate second tab to another valid data URL - should succeed
    result_tab2 = await navigate_and_wait(tab, url=data_url2, timeout=5.0)
    assert result_tab2 is tab

    # Verify the navigation succeeded
    result = await execute_js_and_wait(tab, "window.location.href", timeout=5.0)
    location = result["result"]["result"]["value"]
    assert location.startswith("data:text/html")
    # Test 3: Navigate to bad URL that won't load - should timeout
    with pytest.raises(asyncio.TimeoutError):
        await navigate_and_wait(tab, url="http://192.0.2.1:9999", timeout=0.5)
