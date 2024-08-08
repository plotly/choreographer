import devtools

r1 = {
    "method": "Browser.setDownloadBehavior",
    "params": {
        "behavior": "allowAndName",
        "downloadPath": "'+str(cwd)+'",
        "eventsEnabled": True,
    },
}
r2 = {"method": "Target.getTargets"}
r3 = {
    "method": "Target.createTarget",
    "params": {"url": "file://'+str(cwd / test.html)+'"},
}
r4 = {
    "method": "Target.attachToTarget",
    "params": {"flatten": True, "targetId": "+tId+"},
}
r5 = {"method": "Page.enable"}
r6 = {"method": "Page.reload"}
r7 = {
    "method": "Browser.setDownloadBehavior",
    "params": {
        "behavior": "allow",
        "downloadPath": "'+str(cwd)+'",
        "eventsEnabled": True,
    },
}
r8 = {
    "method": "Page.setDownloadBehavior",
    "params": {
        "behavior": "allow",
        "downloadPath": "'+str(cwd)+'",
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
        "expression": "console.log(document.getElementsByTagName(\\'body\\')[0].innerHTML); 10; let goose = document.getElementById(\\'agoose2\\'); goose.download=\\'goose.jpg\\';goose.click();', 'sourceURL':'+str( cwd / 'test.html' )+', 'persistScript':true"
    },
}
r12 = {
    "method": "Runtime.runScript",
    "params": {"scriptId": "+scriptId+"},
}


list_r = [r1, r3, r4]
list_r_session_id = [r7, r8, r9, r11, r12]

session_1 = devtools.Session()
for r in list_r:
    print(session_1.send_command(command=r["method"], params=r["params"]))

print(session_1.send_command(command=r2["method"], params=None))

print(
    devtools.Session(str(r5["sessionId"])).send_command(
        command=r5["method"], params=None
    )
)
print(
    devtools.Session(str(r6["sessionId"])).send_command(
        command=r6["method"], params=None
    )
)
print(
    devtools.Session(str(r10["sessionId"])).send_command(
        command=r10["method"], params=None
    )
)

for r in list_r_session_id:
    print(
        devtools.Session(str(r["sessionId"])).send_command(
            command=r["method"], params=r["params"]
        )
    )
