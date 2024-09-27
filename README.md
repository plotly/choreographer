# Devtools Protocol

`pip install devtools` not released yet!

`devtools` allows remote control of browsers (currently only chrome-ish) from python. Python's async/await is strongly recommended and supported, but not required.

### ⚠️⚠️⚠️**Testers Needed!**⚠️⚠️⚠️

Please install this repo with `pip` (`pip install .`) and run `dtdoctor`, pasting the output in an issue or to slack!

## Quickstart (asyncio)

Easy:
```python
import asyncio # required for this example only
import devtools


async with Browser(headless=False) as browser:
	new_tab = await browser.create_tab("https://google.com")
	await asyncio.sleep(3)
	await new_tab.send_command("Page.navigate", params=dict(url="https://github.com"))
	await asyncio.sleep(3)


## NOTE:
# if you wish to use interactively, ie in a console,
# it is better to use, instead of `async with`:

browser = await Browser(headless=False)

# as exiting the context will close the browser
```

See [the devtools reference](https://chromedevtools.github.io/devtools-protocol/) for a list of all possible commands.

### Subscribing to Events

```python
	... # continued from above

	# Callback for printing result
	async def dump_event(response):
		print(str(response))

	# Callback for raising result as error
	async def error_event(response):
		raise Exception(str(response))

	browser.subscribe("Target.targetCrashed", error_event)
	new_tab.subscribe("Page.loadEventFired", dump_event)
	browser.subscribe("Target.*", dump_event) # dumps all "Target" events
	reponse = await new_tab.subscribe_once("Page.lifecycleEvent")
	# do something with response
	browser.unsubscribe("Target.*")
	# events are always sent to a browser or tab,
  # but the documentation isn't always clear which.
	# Dumping all: `browser.subscribe("*", dump_event)` (on tab too)
  # can be useful (but verbose) for debugging.
```

## Other Options

### Non-asyncio

You can use this library without `asyncio`,
```
my_browser = devtools.Browser() # blocking until open
```
But you are responsible for calling all `browser.pipe.read_jsons(blocking=True|False)` and organizing the results. `browser.run_output_thread()` will start a second thread that constantly prints all responses from the browser, it can't be used with `asyncio`- it won't play nice with any other read.

### Low-level use

We provide a `Browser` and `Tab` interface, but there is also a lower-level `Target` and `Session` interface that one can use if needed.
