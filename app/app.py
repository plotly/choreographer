import devtools
import time
import asyncio

indent = ">>>>>"

async def print_event(event):
    print(f"{indent} event: {event}")

def create_printer(prefix):
    async def print_event(event):
        print(f"{indent} {prefix} event: {event}")
    return print_event

def print_state(browser):
    print(f"\n{indent} List of browser tabs: {browser.tabs.items()}")
    print(f"\n{indent} List of browser sessions: {browser.sessions.items()}")
    for tab in browser.tabs.values():
        print(f"\n{indent} List of tab sessions: {tab.sessions.items()}")
    print(f"\n{indent} List of all sessions: {browser.protocol.sessions.items()}")

def sync():
    # Doing the full test w/o async framework is tedious and unreliable, so we don't...
    print(f"{indent} Starting sync test")
    with devtools.Browser(headless=False, debug=True, debug_browser=True) as browser:
        print(f"{indent} Starting output thread")
        browser.run_output_thread()
        print(f"{indent} Starting commands")
        browser.send_command(command="Target.getTargets")
        browser.send_command(
            command="Target.createTarget", params={"url": "https://www.youtube.com"}
        )
        time.sleep(1)
        print(f"{indent} Finished commands")
        time.sleep(3)
    print(f"{indent} Finished Sync Tests")

async def async_with_context():
    async with devtools.Browser(headless=False, debug=True, debug_browser=True) as browser:
        browser.subscribe("*", create_printer("browser"), repeating=True)
        print_state(browser)
        # Navigate on current tab TODO (after populate)
        new_tab = await browser.create_tab("https://google.com")
        new_tab.subscribe("*", create_printer("session1"), repeating=True)
        new_session = await new_tab.create_session()
        new_session.subscribe("*", create_printer("session2"), repeating=True)
        print_state(browser)
        await asyncio.sleep(2)
        await new_tab.send_command("Page.navigate", params=dict(url="https://youtube.com"))
        await asyncio.sleep(2)
        await new_session.send_command("Page.navigate", params=dict(url="https://github.com"))
        await asyncio.sleep(2)
        # Enable Page TODO
        # Catch Reload TODO 
        # Catch Page Events TODO 
        await new_tab.close()
        await asyncio.sleep(2)
        print_state(browser)
        # Close First Tab TODO

async def async_no_context():
    browser = await devtools.Browser(headless=False, debug=True, debug_browser=True)
    browser.subscribe("*", create_printer("browser"), repeating=True)
    print_state(browser)
    # Navigate on current tab TODO (after populate)
    new_tab = await browser.create_tab("https://google.com")
    new_tab.subscribe("*", create_printer("session1"), repeating=True)
    new_session = await new_tab.create_session()
    new_session.subscribe("*", create_printer("session2"), repeating=True)
    print_state(browser)
    await asyncio.sleep(2)
    await new_tab.send_command("Page.navigate", params=dict(url="https://youtube.com"))
    await asyncio.sleep(2)
    await new_session.send_command("Page.navigate", params=dict(url="https://github.com"))
    await asyncio.sleep(2)
    # Enable Page TODO
    # Catch Reload TODO 
    # Catch Page Events TODO 
    await new_tab.close()
    await asyncio.sleep(2)
    print_state(browser)
    # Close First Tab TODO
    browser.close()

indent2 = "####"
if __name__ == "__main__":
    """
    print(f"{indent2} __main__: running sync() test")
    sync()
    print(f"{indent2} __main__: ran sync() test")
    time.sleep(3)

    print(f"{indent2} __main__: running async_no_context() test")
    asyncio.run(async_no_context())
    print(f"{indent2} __main__: ran async_no_context() test")
    """    
    print(f"{indent2} __main__: running async_with_context() test")
    asyncio.run(async_with_context())
    print(f"{indent2} __main__: ran async_with_context() test")

