import devtools
import time


def main():
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


if __name__ == "__main__":
    main()


# blocking, regular blocking, you read and write, good luck (we need to be able to piece-meal the thing together)

# blocking with dumping out output off separate thread that you can see
# that one should probably be working with a queue
