import devtools
import time


def main():
    # Interface Test
    # Process/Pipes Test
    with devtools.Browser(headless=False) as browser:
        browser.protocol.send_command(command="Target.getTargets")
        browser.protocol.pipe.read_jsons(debug=True)
        browser.protocol.pipe.read_jsons(blocking=False, debug=True)
        browser.protocol.pipe.read_jsons(blocking=False, debug=True)
        browser.protocol.pipe.read_jsons(blocking=False, debug=True)
        browser.create_tab(True)
        browser.create_tab(True)
        browser.create_tab(True)
        browser.protocol.tabs[next(reversed(browser.protocol.tabs))].add_session()
        tab_browser = browser.protocol.tabs[next(reversed(browser.protocol.tabs))]
        browser.protocol.send_command(
            command="Page.navigate",
            params={"url": "https://github.com/", "targetId": next(reversed(tab_browser.tab_sessions))},
        )
        time.sleep(4)
        browser.protocol.send_command(
            command="Target.createTarget", params={"url": "https://www.youtube.com"}
        )
        time.sleep(5)
        browser.protocol.send_command(command="Target.getTargets")
        browser.protocol.pipe.read_jsons(debug=True)
        browser.protocol.pipe.read_jsons(blocking=False, debug=True)
        browser.protocol.pipe.read_jsons(blocking=False, debug=True)
        browser.protocol.pipe.read_jsons(blocking=False, debug=True)
        time.sleep(3)
        browser.protocol.send_command(command="Target.getTargets")
        browser.protocol.pipe.read_jsons(debug=True)
        browser.protocol.pipe.read_jsons(blocking=False, debug=True)
        browser.protocol.pipe.read_jsons(blocking=False, debug=True)
        browser.protocol.pipe.read_jsons(blocking=False, debug=True)
        time.sleep(3)
    time.sleep(3)


if __name__ == "__main__":
    main()


# blocking, regular blocking, you read and write, good luck (we need to be able to piece-meal the thing together)

# blocking with dumping out output off separate thread that you can see
# that one should probably be working with a queue
