Brokers will handle all events and promises, if there are any.

For example, the _sync.py broker only gives us the option of
starting a thread to dump all events. Writing a broker without
a concurrent structure would be fruitless- it would block and break.


The _async.py broker is much more complex, and will allow users to subscribe
to events, will fulfill processes when receiving responses from the browser
addressed to the user's commands, and generally absorbs all browser communication.

Brokers do not have a standard interface, they are usually 1-1 matched with a particular
`class Browser*` implementation.
