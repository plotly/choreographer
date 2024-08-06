import devtools

from app_utils import start_browser

def main():
    # Interface Test
    browser = devtools.Connection()
    browser.list_tabs()
    myTab = browser.create_tab()
    browser.list_tabs()
    browser.close_tab(myTab)
    browser.list_tabs()

    # Process/Pipes Test
    proc, pipe = start_browser()

    pipe.write("{}")
    print(pipe.read_jsons())

    proc.terminate()
    proc.wait(10)
    proc.kill()

if __name__ == '__main__':
    main()
