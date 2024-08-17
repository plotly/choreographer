import devtools
import time


def main():
    # Interface Test
    # Process/Pipes Test
    with devtools.Browser(headless=False) as browser:
        browser.create_tab()
        browser.create_tab()
        browser.create_tab()
        time.sleep(3)
        browser.close_tab(next(reversed(browser.protocol.tabs.keys())))
        time.sleep(3)
        browser.close_tab(next(reversed(browser.protocol.tabs.keys())))

        time.sleep(10)


if __name__ == "__main__":
    main()
