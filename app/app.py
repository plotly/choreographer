import devtools
import time


def main():
    # Interface Test
    # Process/Pipes Test
    with devtools.Browser(headless=False) as browser:
        ## Create Protocol
        connection = browser.protocol

        connection.send_command(command="Target.createTarget", params={"url": "https://www.youtube.com/"})

        connection.pipe.read_jsons(debug=True)
        connection.pipe.read_jsons(blocking=False, debug=True)
        connection.pipe.read_jsons(blocking=False, debug=True)
        connection.pipe.read_jsons(blocking=False, debug=True)

        time.sleep(10)

if __name__ == "__main__":
    main()
