# Choreographer

choreographer allows remote control of browsers from Python.
It was created to support image generation from browser-based charting tools,
but can be used for other purposes as well.

## Wait—I Thought This Was Kaleido?

[Kaleido][kaleido] is a cross-platform library for generating static images of plots.
The original implementation included a custom build of Chrome,
which has proven very difficult to maintain.
In contrast,
this package uses the Chrome binary on the user's machine
in the same way as testing tools like [Puppeteer][puppeteer];
the next step is to re-implement Kaleido as a layer on top of it.

## Status

choreographer is a work in progress:
only Chrome-ish browsers are supported at the moment,
though we hope to add others.
(Pull requests are greatly appreciated.)

Note that we strongly recommend using async/await with this package,
but it is not absolutely required.
The synchronous functions in this package are intended as building blocks
for other asynchronous strategies that Python may favor over async/await in the future.

## Testing

### Process Control Tests

- Verbose: `pytest -W error -n auto -vvv -rA --capture=tee-sys tests/test_process.py`
- Quiet:`pytest -W error -n auto -v -rFe --capture=fd tests/test_process.py`

### Browser Interaction Tests

- Verbose: `pytest --debug -n auto -W error -vvv -rA --capture=tee-sys --ignore=tests/test_process.py`
- Quiet :`pytest -W error -n auto -v -rFe --capture=fd --ignore=tests/test_process.py`

You can also add "--no-headless" to these if you want to see the browser pop up.

### Writing Tests

-   Put async and sync tests in different files. Add `_sync.py` to synchronous tests.
-   If doing process tests, maybe use the same decorators and fixtures in the `test_process.py` file.
-   If doing browser interaction tests, use `test_placeholder.py` as the minimum template.

## Help Wanted

We need your help to test this package on different platforms
and for different use cases.
To get started:

1.  Clone this repository.
1.  Create and activate a Python virtual environment.
1.  Install this repository using `pip install .` or the equivalent.
1.  Run `dtdoctor` and paste the output into an issue in this repository.

## Quickstart with `asyncio`

Save the following code to `example.py` and run with Python.

```
import asyncio
import choreographer as choreo


async def example():
    browser = await choreo.Browser(headless=False)
    tab = await browser.create_tab("https://google.com")
    await asyncio.sleep(3)
    await tab.send_command("Page.navigate", params={"url": "https://github.com"})
    await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(example())
```

Step by step, this example:

1.  Imports the required libraries.
1.  Defines an `async` function
    (because `await` can only be used inside `async` functions).
1.  Asks choreographer to create a browser.
    `headless=False` tells it to display the browser on the screen;
    the default is no display.
1.  Wait three seconds for the browser to be created.
1.  Create another tab.
    (Note that users can't rearrange programmatically-generated tabs using the mouse,
    but that's OK: we're not trying to replace testing tools like [Puppeteer][puppeteer].)
1.  Sleep again.
1.  Runs the example function.

See [the devtools reference][devtools-ref] for a list of possible commands.

### Subscribing to Events

Try adding the following to the example shown above:

```python
    # Callback for printing result
    async def dump_event(response):
        print(str(response))


    # Callback for raising result as error
    async def error_event(response):
        raise Exception(str(response))


    browser.subscribe("Target.targetCrashed", error_event)
    new_tab.subscribe("Page.loadEventFired", dump_event)
    browser.subscribe("Target.*", dump_event) # dumps all "Target" events
    response = await new_tab.subscribe_once("Page.lifecycleEvent")
    # do something with response
    browser.unsubscribe("Target.*")
    # events are always sent to a browser or tab,
    # but the documentation isn't always clear which.
    # Dumping all: `browser.subscribe("*", dump_event)` (on tab too)
    # can be useful (but verbose) for debugging.
```

## Synchronous Use

You can use this library without `asyncio`,

```
my_browser = choreo.Browser() # blocking until open
```

However,
you are responsible for calling `browser.pipe.read_jsons(blocking=True|False)` when necessary
and organizing the results.
`browser.run_output_thread()` will start a second thread that constantly prints all responses from the browser,
but it can't be used with `asyncio` and won't play nice with any other read.
In other words,
unles you're really, really sure you know what you're doing,
use `asyncio`.

## Low-Level Use

We provide a `Browser` and `Tab` interface,
but there is also a lower-level `Target` and `Session` interface that one can use if needed.
We will document these as the API stabilizes.

[devtools-ref]: https://chromedevtools.github.io/devtools-protocol/
[kaleido]: https://pypi.org/project/kaleido/
[puppeteer]: https://pptr.dev/


