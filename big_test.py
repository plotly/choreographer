
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

import asyncio
import choreographer as choreo

MB = 110
size = MB * 1024 * 1024
chunk = "x" * size

async def arun():
    async with choreo.Browser(headless=False) as b: # prob should use context manager for autoclose huh
        t = await b.create_tab("about:blank")
        await t.send_command(
                "Runtime.evaluate",
                {"expression":f"console.log(\"hello world\")"},
        )
        await t.send_command(
            "Runtime.evaluate",
            {"expression":f"console.log('{chunk}')"},
        )
        input("Press Enter to quit...")

asyncio.run(arun())

