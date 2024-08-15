import devtools
import time


def main():
    # Interface Test
    # Process/Pipes Test
    with devtools.Browser() as browser:
        pipe = browser.pipe
    ## Create Protocol
        connection = browser.connection_protocol

        connection.list_tabs()

    ## Simulate Commands
        print(
            connection.browser_session.send_command(
                "command1", dict(param1="1", param2="a")
            )
        )
        print(
            connection.browser_session.send_command(
                "command2", dict(param1="2", param2="b")
            )
        )

    ## Create Tab
        myTab = connection.create_tab()
        myTab.add_session()
        connection.list_tabs()

    ## Simulate Commands
        print(connection.send_command("tabCommand1", dict(param1="tab1", param2="taba")))
        print(connection.send_command("tabCommand2", dict(param1="tab2", param2="tabb")))
        print(
            connection.browser_session.send_command(
                "command3", dict(param1="3", param2="c")
            )
        )

    ## Close Tab
        connection.close_tab(myTab.target_id)
        connection.list_tabs()

    ## Simulate Commands
        print(
            connection.browser_session.send_command(
                "command4", dict(param1="4", param2="d")
            )
        )


        pipe.write_json("{}")
        print(pipe.read_jsons(debug=True))
        print(pipe.read_jsons(blocking=False, debug=True))
        print(pipe.read_jsons(blocking=False, debug=True))
        print(pipe.read_jsons(blocking=False, debug=True))

        time.sleep(10)


if __name__ == "__main__":
    main()
