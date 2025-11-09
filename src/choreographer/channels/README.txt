Browsers often accept two communication channels: websockets and pipes.

Both classes we implement will support `write_jsons()` and `read_jsons()`
with the same interface (as well as `__init__()` and `close()`).

But the browser implementation in _browsers/ will have to get specific
information from the pipe/websocket in order to properly build the CLI
command for the browser.

For example, the CLI command needs to know the file numbers (file descriptors)
for reading writing if using `Pipe()`, so `Pipe()` has the attributes:
`.from_external_to_choreo` and `.from_choreo_to_external`. They're part of
the interface as well.

In the same vein, when websockets in implemented, the CLI command will
need to know the port it's on. There may need to be a `open()` function for
after the CLI command is run.
