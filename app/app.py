import devtools
import time
import asyncio

def main_sync():
    # Interface Test
    # Process/Pipes Test
    with devtools.Browser(headless=False, debug=True, debug_browser=False) as browser:
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
    with devtools.Browser(debug=True, loop=asyncio.get_running_loop()) as browser:
        tab1 = await browser.create_tab("https://www.youtube.com")
        print("created tab")
        await asyncio.sleep(5)
        await tab1.send_command("Page.navigate", params=dict(url="https://github.com"))
        await asyncio.sleep(5)
        tab2 = await browser.create_tab("https://plotly.com/python/")
        await asyncio.sleep(3)
        tab3 = await browser.create_tab("https://plotly.com/")
        await asyncio.sleep(3)
        browser.create_session()
        print("Create session in browser")
        session1 = await tab3.create_session()
        print("create session in plotly page")
        await asyncio.sleep(3)
        await tab3.close_session(session1)
        await browser.close_tab(tab2)
        await asyncio.sleep(4)
        await browser.populate_targets()
        print("All is done")

if __name__ == "__main__":
    #main_sync()
    asyncio.run(main_async())


# blocking, regular blocking, you read and write, good luck (we need to be able to piece-meal the thing together)

# blocking with dumping out output off separate thread that you can see
# that one should probably be working with a queue
