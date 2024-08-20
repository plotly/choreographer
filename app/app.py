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
        browser.create_tab()
        browser.create_tab()
        browser.create_tab()
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

if __name__ == "__main__":
    main()


# blocking, regular blocking, you read and write, good luck (we need to be able to piece-meal the thing together)

# blocking with dumping out output off separate thread that you can see
# that one should probably be working with a queue
