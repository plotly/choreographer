import devtools
import time
import asyncio

def main_sync():
    # Interface Test
    # Process/Pipes Test
    with devtools.Browser(headless=False, debug=True, debug_browser=True) as browser:
        browser.send_command(command="Target.getTargets")
        browser.protocol.pipe.read_jsons()
        browser.protocol.pipe.read_jsons(blocking=False)
        browser.protocol.pipe.read_jsons(blocking=False)
        browser.protocol.pipe.read_jsons(blocking=False)
        time.sleep(4)
        browser.send_command(
            command="Target.createTarget", params={"url": "https://www.youtube.com"}
        )
        browser.protocol.pipe.read_jsons()
        browser.protocol.pipe.read_jsons(blocking=False)
        browser.protocol.pipe.read_jsons(blocking=False)
        browser.protocol.pipe.read_jsons(blocking=False)
        time.sleep(5)
        browser.send_command(command="Target.getTargets")
        browser.protocol.pipe.read_jsons()
        browser.protocol.pipe.read_jsons(blocking=False)
        browser.protocol.pipe.read_jsons(blocking=False)
        browser.protocol.pipe.read_jsons(blocking=False)
        time.sleep(3)
        browser.send_command(command="Target.getTargets")
        browser.protocol.pipe.read_jsons()
        browser.protocol.pipe.read_jsons(blocking=False)
        browser.protocol.pipe.read_jsons(blocking=False)
        browser.protocol.pipe.read_jsons(blocking=False)
        time.sleep(3)
    time.sleep(3)

async def main_async():
    with devtools.Browser(headless=False, debug=True, loop=asyncio.get_running_loop(), debug_browser=True) as browser:
        tab1 = await browser.create_tab("https://www.youtube.com")
        await tab1.send_command("Page.navigate", params=dict(url="https://github.com"))
        tab2 = await browser.create_tab("https://plotly.com/")
        await asyncio.sleep(1)
        tab2_session2 = await tab2.create_session()
        await tab2.send_command("Page.navigate", params=dict(url="https://duckduckgo.com"))
        browser_session2 = await browser.create_session()
        await browser_session2.send_command("Target.getTargets")
        await tab2.close_session(tab2_session2)
        await browser.close_tab(tab2)
        print("All is done")
        await asyncio.sleep(5)

if __name__ == "__main__":
    main_sync()
    time.sleep(2)
    asyncio.run(main_async())


# blocking, regular blocking, you read and write, good luck (we need to be able to piece-meal the thing together)

# blocking with dumping out output off separate thread that you can see
# that one should probably be working with a queue
