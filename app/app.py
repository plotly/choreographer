import devtools

from app_utils import start_browser

def main():
    # Interface Test
    browser = devtools.Connection()
    browser.list_tabs()
    print(browser.browser_session.send_command("command1", dict(param1="1", param2="a")))
    print(browser.browser_session.send_command("command2", dict(param1="2", param2="b")))
    myTab = browser.create_tab()
    print(myTab.send_command("tabCommand1", dict(param1="tab1", param2="taba")))
    print(myTab.send_command("tabCommand2", dict(param1="tab2", param2="tabb")))
    browser.list_tabs()
    browser.close_tab(myTab)
    browser.list_tabs()
    print(browser.browser_session.send_command("command3", dict(param1="3", param2="c")))
    print(browser.browser_session.send_command("command4", dict(param1="4", param2="d")))

    # Process/Pipes Test
    proc, pipe = start_browser()

    pipe.write("{}")
    print(pipe.read_jsons())

    proc.terminate()
    proc.wait(10)
    proc.kill()

if __name__ == '__main__':
    main()
