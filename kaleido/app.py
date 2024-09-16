import asyncio
import base64
import json
from pathlib import Path

from devtools import Browser

script_path = Path(__file__).resolve().parent / "index.html"
print(script_path)

_text_formats = ("svg", "json", "eps")

# Taken from Jon Mease's Kaleido
def prepare_spec(figure, format=None, width=None, height=None, scale=None):
    default_format = "png"
    default_scale = 1
    default_width = 700
    default_height = 500
    _all_formats = ("png", "jpg", "jpeg", "webp", "svg", "pdf", "eps", "json") # TODO not all supported...

    from plotly.graph_objects import Figure
    if isinstance(figure, Figure):
        figure = figure.to_dict()
    
    # Apply default format and scale
    format = format if format is not None else default_format
    scale = scale if scale is not None else default_scale

    # Get figure layout
    layout = figure.get("layout", {})

    # Compute image width / height
    width = (
            width
            or layout.get("width", None)
            or layout.get("template", {}).get("layout", {}).get("width", None)
            or default_width
    )
    height = (
            height
            or layout.get("height", None)
            or layout.get("template", {}).get("layout", {}).get("height", None)
            or default_height
    )

    # Normalize format
    original_format = format
    format = format.lower()
    if format == 'jpg':
        format = 'jpeg'

    if format not in _all_formats:
        supported_formats_str = repr(list(self._all_formats))
        raise ValueError(
            "Invalid format '{original_format}'.\n"
            "    Supported formats: {supported_formats_str}"
            .format(
                original_format=original_format,
                supported_formats_str=supported_formats_str
            )
        )
    args = dict(format=format, width=width, height=height, scale=scale)

    spec = dict(args, data=figure)

    return spec

async def print_all(thing):
    print(thing)

async def to_image(figure, path):
    async with Browser(headless=False) as browser:
        tab = await browser.create_tab(script_path.as_uri())
        await tab.send_command("Page.enable")
        await tab.send_command("Runtime.enable")
        
        # Create a future for the event automatically TODO
        event_done = asyncio.get_running_loop().create_future()
        async def execution_started_cb(response):
            event_done.set_result(response)
        tab.subscribe("Runtime.executionContextCreated", execution_started_cb, repeating=False)
        await tab.send_command("Page.reload")
        await event_done
        execution_context_id = event_done.result()["params"]["context"]["id"]
        # this could just as easily be part of the original script
        # some changes could be made their to download more easily TODO
        # read original python, read original javascript
         
        event_done = asyncio.get_running_loop().create_future()
        async def load_done_cb(response):
            event_done.set_result(response)
        tab.subscribe("Page.loadEventFired", load_done_cb, repeating=False)
        await event_done
        
        kaleido_jsfn = r"function(spec, ...args) { console.log(typeof spec); console.log(spec); return kaleido_scopes.plotly(spec, ...args).then(JSON.stringify); }"
       
        spec = prepare_spec(figure)
        params = dict(
                functionDeclaration=kaleido_jsfn,
                arguments=[dict(value=spec)],
                returnByValue=False,
                userGesture=True,
                awaitPromise=True,
                executionContextId=execution_context_id,
                )
        response = await tab.send_command("Runtime.callFunctionOn", params=params)

        # Check for export error, later can customize error messages for plotly Python users
        code = response.get("code", 0)
        if code != 0:
            message = response.get("message", None)
            raise ValueError(
                "Transform failed with error code {code}: {message}".format(
                    code=code, message=message
                )
            )

        # hate TODO
        img = json.loads(response.get("result").get("result").get("value")).get("result")

        # Base64 decode binary types
        if format not in _text_formats:
            img = base64.b64decode(img)

        # TODO: not async
        with open(path, "wb") as f:
            f.write(img)

        # Cleanup Close TODO
        # https://stackoverflow.com/questions/1262708/suppress-command-line-output  TODO

####
####
#### START TESTING
####
####

import os

dirIn = Path(__file__).resolve().parent / "mocks/"
ALL_MOCKS = [os.path.splitext(a)[0] for a in os.listdir(dirIn) if a.endswith('.json')]
ALL_MOCKS.sort()
allNames = ALL_MOCKS


for name in allNames:
    with open(os.path.join(dirIn, name + '.json'), 'r') as _in :
        try:
            fig = json.load(_in)
        except Exception as e:
            print("No load")
            print(e)
            print(_in)
            print("***")
            continue

        width = 700
        height = 500
        if 'layout' in fig :
            layout = fig['layout']
            if 'autosize' not in layout or layout['autosize'] != True :
                if 'width' in layout :
                    width = layout['width']
                if 'height' in layout :
                    height = layout['height']
        try:
            asyncio.run(to_image(fig, "./results/" + name+".png"))
        except Exception as e:
            print("No to image")
            print(e)
            print(_in)
            print("***")


# option to block on this thread TODO
# option to go into background thread TODO
# option to use it in my task manager TODO
