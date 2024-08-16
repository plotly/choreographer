import devtools
import time


def main():
    # Interface Test
    # Process/Pipes Test
    with devtools.Browser(headless=False) as browser:
        browser.create_tab()
        browser.create_tab()
        browser.create_tab()
        time.sleep(10)

        browser.pipe.read_jsons(debug=True)
        browser.pipe.read_jsons(blocking=False, debug=True)
        browser.pipe.read_jsons(blocking=False, debug=True)
        browser.pipe.read_jsons(blocking=False, debug=True)

        time.sleep(10)


if __name__ == "__main__":
    main()
