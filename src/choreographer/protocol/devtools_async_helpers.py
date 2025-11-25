"""Async helper functions for common Chrome DevTools Protocol patterns."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from choreographer import Browser, Tab

    from . import BrowserResponse


async def create_and_wait(
    browser: Browser,
    url: str = "",
    *,
    timeout: float = 30.0,
) -> Tab:
    """
    Create a new tab and wait for it to load.

    Args:
        browser: Browser instance
        url: URL to navigate to (default: blank page)
        timeout: Seconds to wait for page load (default: 30.0)

    Returns:
        The created Tab

    """
    tab = await browser.create_tab(url)
    temp_session = await tab.create_session()

    try:
        load_future = temp_session.subscribe_once("Page.loadEventFired")
        await temp_session.send_command("Page.enable")
        await temp_session.send_command("Runtime.enable")

        if url:
            try:
                await asyncio.wait_for(load_future, timeout=timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError, TimeoutError):
                # Stop the page load when timeout occurs
                await temp_session.send_command("Page.stopLoading")
                raise
    finally:
        await tab.close_session(temp_session.session_id)

    return tab


async def navigate_and_wait(
    tab: Tab,
    url: str,
    *,
    timeout: float = 30.0,
) -> Tab:
    """
    Navigate an existing tab to a URL and wait for it to load.

    Args:
        tab: Tab to navigate
        url: URL to navigate to
        timeout: Seconds to wait for page load (default: 30.0)

    Returns:
        The Tab after navigation completes

    """
    temp_session = await tab.create_session()

    try:
        # Subscribe BEFORE enabling domains to avoid race condition
        load_future = temp_session.subscribe_once("Page.loadEventFired")
        await temp_session.send_command("Page.enable")
        await temp_session.send_command("Runtime.enable")
        try:

            async def _freezers() -> None:
                # If no resolve, will freeze
                await temp_session.send_command("Page.navigate", params={"url": url})
                # Can freeze if resolve bad
                await load_future

            await asyncio.wait_for(_freezers(), timeout=timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError, TimeoutError):
            # Stop the navigation when timeout occurs
            await temp_session.send_command("Page.stopLoading")
            raise
    finally:
        await tab.close_session(temp_session.session_id)

    return tab


async def execute_js_and_wait(
    tab: Tab,
    expression: str,
    *,
    timeout: float = 30.0,
) -> BrowserResponse:
    """
    Execute JavaScript in a tab and return the result.

    Args:
        tab: Tab to execute JavaScript in
        expression: JavaScript expression to evaluate
        timeout: Seconds to wait for execution (default: 30.0)

    Returns:
        Response dict from Runtime.evaluate with 'result' and optional
        'exceptionDetails'

    """
    temp_session = await tab.create_session()

    try:
        await temp_session.send_command("Page.enable")
        await temp_session.send_command("Runtime.enable")

        response = await asyncio.wait_for(
            temp_session.send_command(
                "Runtime.evaluate",
                params={
                    "expression": expression,
                    "awaitPromise": True,
                    "returnByValue": True,
                },
            ),
            timeout=timeout,
        )

        return response
    finally:
        await tab.close_session(temp_session.session_id)
