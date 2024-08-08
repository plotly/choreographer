import devtools

## Create Variables
r1 = {
    "method": "Browser.setDownloadBehavior",
    "params": {
        "behavior": "allowAndName",
        "downloadPath": "str(cwd)",
        "eventsEnabled": True,
    },
}
r2 = {"method": "Target.getTargets"}
r3 = {
    "method": "Target.createTarget",
    "params": {"url": "file://str(cwd / test.html)"},
}
r4 = {
    "method": "Target.attachToTarget",
    "params": {"flatten": True, "targetId": "tId"},
}
r5 = {"method": "Page.enable"}
r6 = {"method": "Page.reload"}
r7 = {
    "method": "Browser.setDownloadBehavior",
    "params": {
        "behavior": "allow",
        "downloadPath": "str(cwd)",
        "eventsEnabled": True,
    },
}
r8 = {
    "method": "Page.setDownloadBehavior",
    "params": {
        "behavior": "allow",
        "downloadPath": "str(cwd)",
        "eventsEnabled": True,
    },
}
r9 = {
    "method": "Page.setInterceptFileChooserDialog",
    "params": {"enabled": True},
}
r10 = {"method": "Runtime.enable"}
r11 = {
    "method": "Runtime.compileScript",
    "params": {
        "expression": "console.log(document.getElementsByTagName(\\'body\\')[0].innerHTML); 10; let goose = document.getElementById(\\'agoose2\\'); goose.download=\\'goose.jpg\\';goose.click();', 'sourceURL':'str( cwd / 'test.html' )', 'persistScript':true"
    },
}
r12 = {
    "method": "Runtime.runScript",
    "params": {"scriptId": "scriptId"},
}


list_r = [r1, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12]

## Create Connection
browser = devtools.Connection()

browser.list_tabs()

## Print Commands
for r in list_r:
    if "params" in r.keys():
        print(browser.browser_session.send_command(command=r["method"], params=r["params"]))
    else:
        print(browser.browser_session.send_command(command=r["method"], params=None))