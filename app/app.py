import devtools
import time

def main():
    # Interface Test

    ## Create Connection
    connection = devtools.Connection()

    connection.list_tabs()

    ## Simulate Commands
    print(connection.browser_session.send_command("command1", dict(param1="1", param2="a")))
    print(connection.browser_session.send_command("command2", dict(param1="2", param2="b")))

    ## Create Tab
    myTab = connection.create_tab()
    connection.list_tabs()

    ## Simulate Commands
    print(myTab.send_command("tabCommand1", dict(param1="tab1", param2="taba")))
    print(myTab.send_command("tabCommand2", dict(param1="tab2", param2="tabb")))
    print(connection.browser_session.send_command("command3", dict(param1="3", param2="c")))

    ## Close Tab
    connection.close_tab(myTab)
    connection.list_tabs()

    ## Simulate Commands
    print(connection.browser_session.send_command("command4", dict(param1="4", param2="d")))

    # Process/Pipes Test
    browser = devtools.Browser()
    pipe = browser.pipe
    proc = browser.subprocess

    pipe.write("{}")
    print(pipe.read_jsons(debug=True))
    print(pipe.read_jsons(blocking=False,debug=True))
    print(pipe.read_jsons(blocking=False,debug=True))
    print(pipe.read_jsons(blocking=False,debug=True))

    time.sleep(10)

    browser.close_browser(proc)

if __name__ == '__main__':
    main()
