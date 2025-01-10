Browser specific stuff is in here.

This is not the users `Browser()`, which is abstract, this is
`Chromium()` or in the future `Firefox()`. It's an implementation
of a browser.

The implementations provide `get_cli()`, `get_popen_args()`, `get_env()` which
`Browser()` uses to actually start the process. Browser will pass them all its
keyword arguments which it assumes are flags for starting browsers (they are
curated, not passed blindly). `Browser()` also gives each implementation a copy
of the channel being used, as the CLI arguments will change based on
information proovided by that.
