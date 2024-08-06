#!/usr/bin/env -S python3 -u
import os
import subprocess
import time
import json
from pathlib import Path
import platform
system = platform.system()
if system == "Windows": import msvcrt

path=""
if system == "Linux":
    path = os.environ.get("BROWSER_PATH", "/usr/bin/google-chrome-stable")
elif system == "Windows":
    path = os.environ.get("BROWSER_PATH", r"c:\Program Files\Google\Chrome\Aprint_jsonslication\chrome.exe")
cwd = Path(__file__).parent.resolve()

def main():
    global path
    global cwd
    global system
    # chromium is going to output on 4
    # we will read on result_stream to get chromium's output
    from_chromium = list(os.pipe())
    to_chromium = list(os.pipe())

    print(f"from_chromium read: {from_chromium[0]} write: {from_chromium[1]}")
    print(f"to_chromium read: {to_chromium[0]} write: {to_chromium[1]}")


    if (from_chromium[1] != 4):
        print("from_chromium write is not 4")
        if (from_chromium[0] == 4):
            print("from_chromium[0] is!")
            temp = from_chromium[0]
            from_chromium[0] = os.dup(from_chromium[0])
            os.close(temp)
            print(f"from_chromium[0] is now {from_chromium}!")
        if (to_chromium[0] == 4):
            print("to_chromium[0] is!")
            temp = to_chromium[0]
            to_chromium[0] = os.dup(to_chromium[0])
            os.close(temp)
            print(f"to_chromium[0] is now {to_chromium}!")
        if (to_chromium[1] == 4):
            print("to_chromium[1] is!")
            temp = to_chromium[1]
            to_chromium[1] = os.dup(to_chromium[1])
            os.close(temp)
            print(f"to_chromium[1] is now {to_chromium}!")

        os.dup2(from_chromium[1], 4)
        os.close(from_chromium[1])
        os.from_chromium[1] = 4
        print("Finished the swap")

    if (to_chromium[0] != 3):
        print("to_chromium read is not 3")
        if (to_chromium[1] == 3):
            print("to_chromium[1] is!")
            temp = to_chromium[1]
            to_chromium[1] = os.dup(to_chromium[1])
            os.close(temp)
            print(f"to_chromium[1] is now {to_chromium}!")
        if (from_chromium[0] == 3):
            print("from_chromium[0] is!")
            temp = from_chromium[0]
            from_chromium[0] = os.dup(from_chromium[0])
            os.close(temp)
            print(f"from_chromium[0] is now {from_chromium}!")
        if (from_chromium[1] == 3):
            print("from_chromium[1] is!")
            temp = from_chromium[1]
            from_chromium[1] = os.dup(from_chromium[1])
            os.close(temp)
            print(f"from_chromium[1] is now {from_chromium}!")

        os.dup2(to_chromium[0], 3)
        os.close(to_chromium[0])
        to_chromium[0] = 3
        print("Finished the swap")

    print(f"from_chromium read: {from_chromium[0]} write: {from_chromium[1]}")
    print(f"to_chromium read: {to_chromium[0]} write: {to_chromium[1]}")
    os.set_inheritable(to_chromium[0], True)
    os.set_inheritable(to_chromium[1], True)
    os.set_inheritable(from_chromium[0], True)
    os.set_inheritable(from_chromium[1], True)

    cli = [path,
                "--headless",
                "--remote-debugging-pipe",
                "--disable-breakpad",
                "--allow-file-access-from-files"]
    if system == "Windows":
        to_chromium_handle = msvcrt.get_osfhandle(to_chromium[0])
        os.set_handle_inheritable(to_chromium_handle, True)
        from_chromium_handle = msvcrt.get_osfhandle(from_chromium[1])
        os.set_handle_inheritable(from_chromium_handle, True)
        cli += [f"--remote-debugging-io-pipes={str(to_chromium_handle)},{str(from_chromium_handle)}"]

    proc = subprocess.Popen(
            cli,
            close_fds=False,
            stdout=None,
            stderr=None,
            text=True,
            bufsize=1
            )
    prefix = ">>>>>>>>>>>>>> "
    class PipeClosedError(IOError):
        pass

    # semi blocking to get whole message
    # for full non-blocking, we need a global
    # state object
    def read_jsons(blocking=True):
        jsons = []
        os.set_blocking(from_chromium[0], blocking)
        try:
            raw_buffer = os.read(from_chromium[0], 10000) # 10MB buffer, nbd, doesn't matter w/ this
            if not raw_buffer:
                raise PipeClosedError()
            while raw_buffer[-1] != 0:
                os.set_blocking(from_chromium[0], True)
                raw_buffer += os.read(from_chromium[0], 10000)
        except BlockingIOError:
            return jsons
        for raw_message in raw_buffer.decode('utf-8').split('\0'):
            if raw_message:
                jsons.append(json.loads(raw_message))
        return jsons

    def print_jsons(data):
        print("Result".center(25,"*"))
        for datum in data:
            print(json.dumps(datum, indent=4))
        print("*".center(25,"*"))

    def write(msg, check=True):
        os.write(to_chromium[1], str.encode(msg+'\0'))
        if not check:
            return
        return read_jsons(blocking=True)

    # We need to see what events look like

    write('{"id":0, "method":"Browser.setDownloadBehavior", "params":{"behavior":"allowAndName", "downloadPath":"'+str(cwd.as_posix())+'", "eventsEnabled":true}}')
    print_jsons(read_jsons(blocking=True))
    print_jsons(read_jsons(blocking=False))
    print_jsons(read_jsons(blocking=False))
    write('{"id":1, "method":"Target.getTargets"}')
    print_jsons(read_jsons(blocking=True))
    print_jsons(read_jsons(blocking=False))
    time.sleep(.1)
    print_jsons(read_jsons(blocking=False))
    write('{"id":2, "method":"Target.createTarget","params":{"url":"file://'+str( (cwd / "test.html").as_posix() )+'"}}')
    print_jsons(read_jsons(blocking=True))
    tId = '"'+str(r[0]['result']['targetId'])+'"'
    print(prefix + "targetID:" + tId)
    print_jsons(read_jsons(blocking=False))
    time.sleep(.1)
    print_jsons(read_jsons(blocking=False))
    write('{"id":3, "method":"Target.attachToTarget","params":{"flatten": true, "targetId":'+tId+'}}')
    print_jsons(read_jsons(blocking=True))
    #sId='"' + r[1]['result']['sessionId'] + '"'
    #print(prefix + "sessionId:" + sId)
    print_jsons(read_jsons(blocking=False))
    time.sleep(.1)
    print_jsons(read_jsons(blocking=False))
    time.sleep(.1)
    print_jsons(read_jsons(blocking=False))
    time.sleep(.1)
    print_jsons(read_jsons(blocking=False))
    proc.terminate()
    proc.wait(2)
    proc.kill()
    exit()
    write('{"sessionId":'+sId+', "id":0, "method":"Page.enable"}')
    print_jsons(read_jsons(blocking=True))
    #time.sleep(.5)
    #print_jsons(read_jsons(blocking=False))
    #time.sleep(.5)
    #print_jsons(read_jsons(blocking=False))
    #time.sleep(.5)
    #print_jsons(read_jsons(blocking=False))
    #time.sleep(.5)
    #print_jsons(read_jsons(blocking=False))
    write('{"sessionId":'+sId+', "id":2, "method":"Page.reload"}')
    print_jsons(read_jsons(blocking=True))
    time.sleep(.5)
    #print_jsons(read_jsons(blocking=False))
    time.sleep(.5)
    #print_jsons(read_jsons(blocking=False))
    time.sleep(.5)
    #print_jsons(read_jsons(blocking=False))
    time.sleep(.5)
    print_jsons(read_jsons(blocking=False))
    write('{"sessionId":'+sId+', "id":3, "method":"Browser.setDownloadBehavior", "params":{"behavior":"allow", "downloadPath":"'+str(cwd.as_posix())+'", "eventsEnabled":true}}')
    print_jsons(read_jsons(blocking=True))
    #time.sleep(1)
    #print_jsons(read_jsons(blocking=False))
    #time.sleep(1)
    write('{"sessionId":'+sId+', "id":13, "method":"Page.setDownloadBehavior", "params":{"behavior":"allow", "downloadPath":"'+str(cwd.as_posix())+'", "eventsEnabled":true}}')
    print_jsons(read_jsons(blocking=True))
    #print_jsons(read_jsons(blocking=False))
    #time.sleep(1)
    #print_jsons(read_jsons(blocking=False))
    #time.sleep(1)
    write('{"sessionId":'+sId+', "id":23, "method":"Page.setInterceptFileChooserDialog", "params":{"enabled":true}}')
    print_jsons(read_jsons(blocking=True))
    #print_jsons(read_jsons(blocking=False))
    #write('{"id":4, "method":"Target.getTargets"}')
    #print_jsons(read_jsons(blocking=True))
    #time.sleep(1)
    #print_jsons(read_jsons(blocking=False))
    write('{"sessionId":'+sId+', "id":4, "method":"Runtime.enable"}')
    print_jsons(read_jsons(blocking=True))
    time.sleep(1)
    #print_jsons(read_jsons(blocking=False))
    time.sleep(1)
    print_jsons(read_jsons(blocking=False))
    write('{"sessionId":'+sId+', "id":5, "method":"Runtime.compileScript", "params":{"expression": "console.log(document.getElementsByTagName(\\"body\\")[0].innerHTML); 10; let goose = document.getElementById(\\"agoose2\\"); goose.download=\\"goose.jpg\\";goose.click();", "sourceURL":"'+str( (cwd / "test.html").as_posix() )+'", "persistScript":true}}')
    print_jsons(read_jsons(blocking=True))
    scriptId = '"' + r[0]['result']['scriptId'] + '"'
    print(prefix + "scriptId: " + scriptId)
    #time.sleep(1)
    #print_jsons(read_jsons(blocking=False))
    #time.sleep(1)
    #print_jsons(read_jsons(blocking=False))
    write('{"sessionId":'+sId+', "id":6, "method":"Runtime.runScript", "params":{"scriptId":'+scriptId+'}}')
    print_jsons(read_jsons(blocking=True))
    time.sleep(1)
    print_jsons(read_jsons(blocking=False))
    time.sleep(1)
    print_jsons(read_jsons(blocking=False))
    time.sleep(1)
    print_jsons(read_jsons(blocking=False))
    time.sleep(1)
    print_jsons(read_jsons(blocking=False))
    #x('{"sessionId":'+sId+', "id":7, "method":"Runtime.handleJavaScriptDialog", "params":{"accept":false}}', check=False)
    time.sleep(1)
    print_jsons(read_jsons(blocking=False))
    #x('{"sessionId":'+sId+', "id":8, "method":"Runtime.handleJavaScriptDialog", "params":{"accept":true}}', check=False)
    time.sleep(1)
    print_jsons(read_jsons(blocking=False))
    #x('{"sessionId":'+sId+', "id":9, "method":"Runtime.handleJavaScriptDialog", "params":{"accept":false}}', check=False)
    #time.sleep(1)
    #print_jsons(read_jsons(blocking=False))
    #x('{"sessionId":'+sId+', "id":10, "method":"Runtime.handleJavaScriptDialog", "params":{"accept":true}}', check=False)
    #time.sleep(1)
    #print_jsons(read_jsons(blocking=False))
    #time.sleep(1)
    #print_jsons(read_jsons(blocking=False))
    #time.sleep(1)
    #print_jsons(read_jsons(blocking=False))

    # restructure a bit... no, not now...
    # get back to the other work


    proc.terminate()

if __name__ == '__main__':
    main()
