import os
import subprocess
import time
import json
#from multiprocessing import Process

#def read_results():
#    os.read

def main():
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

    stderr_pipe = list(os.pipe())
    os.set_inheritable(stderr_pipe[0], True)
    os.set_inheritable(stderr_pipe[1], True)
    proc = subprocess.Popen(
            ["/usr/bin/google-chrome-stable",
                "--headless",
                "--remote-debugging-pipe",
                "--disable-breakpad",
                "--allow-file-access-from-files"],
            close_fds=False,
            stdout=stderr_pipe[1],
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
            )
    def pp(data):
        print("Result:")
        for datum in data:
            print(json.dumps(datum, indent=4))

    prefix=">>>>>>>> "
    def check():
        os.set_blocking(from_chromium[0], False)
        try:
            result = bytes.decode(os.read(from_chromium[0], 10000)).replace('\0','')
            dec = json.JSONDecoder()
            pos = 0
            res = []
            while not pos == len(str(result)):
                #print(" Decoding:")
                #print(" " + result[pos:])
                j, json_len = dec.raw_decode(result[pos:])
                pos += json_len
                res.append(j)
            pp(res)
        except BlockingIOError:
            print(prefix + "No message")
            return None

    def x(msg, check=True):
        os.set_blocking(from_chromium[0], True)
        print("\n\nNew:")
        print(f" Message: {msg}")
        os.write(to_chromium[1], str.encode(msg+'\0'))
        if not check: return
        result = bytes.decode(os.read(from_chromium[0], 10000)).replace('\0','')
        dec = json.JSONDecoder()
        pos = 0
        res = []
        while not pos == len(str(result)):
            #print(" Decoding:")
            #print(" " + result[pos:])
            j, json_len = dec.raw_decode(result[pos:])
            pos += json_len
            res.append(j)
        return res


    r = x('{"id":0, "method":"Browser.setDownloadBehavior", "params":{"behavior":"allowAndName", "downloadPath":"/home/ajp/test/downloads/", "eventsEnabled":true}}')
    pp(r)
    r = x('{"id":1, "method":"Target.getTargets"}')
    pp(r)
    r = x('{"id":2, "method":"Target.createTarget","params":{"url":"file:///home/ajp/test/test.html"}}')
    pp(r)
    tId = '"'+str(r[0]['result']['targetId'])+'"'
    print(prefix + "targetID:" + tId)
    r = x('{"id":3, "method":"Target.attachToTarget","params":{"flatten": true, "targetId":'+tId+'}}')
    pp(r)
    sId='"' + r[1]['result']['sessionId'] + '"'
    print(prefix + "sessionId:" + sId)
    time.sleep(.5)
    check()
    time.sleep(.5)
    check()
    time.sleep(.5)
    check()
    time.sleep(.5)
    check()
    r = x('{"sessionId":'+sId+', "id":0, "method":"Page.enable"}')
    pp(r)
    time.sleep(.5)
    check()
    time.sleep(.5)
    check()
    time.sleep(.5)
    check()
    time.sleep(.5)
    check()
    r = x('{"sessionId":'+sId+', "id":2, "method":"Page.reload"}')
    pp(r)
    time.sleep(.5)
    check()
    time.sleep(.5)
    check()
    time.sleep(.5)
    check()
    time.sleep(.5)
    check()
    r = x('{"sessionId":'+sId+', "id":3, "method":"Browser.setDownloadBehavior", "params":{"behavior":"allow", "downloadPath":"/home/ajp/test/downloads/", "eventsEnabled":true}}')
    pp(r)
    time.sleep(1)
    check()
    time.sleep(1)
    r = x('{"sessionId":'+sId+', "id":13, "method":"Page.setDownloadBehavior", "params":{"behavior":"allow", "downloadPath":"/home/ajp/test/downloads/", "eventsEnabled":true}}')
    pp(r)
    check()
    time.sleep(1)
    check()
    time.sleep(1)
    r = x('{"sessionId":'+sId+', "id":23, "method":"Page.setInterceptFileChooserDialog", "params":{"behavior":true}')
    pp(r)
    check()
    r = x('{"id":4, "method":"Target.getTargets"}')
    pp(r)
    time.sleep(1)
    check()
    r = x('{"sessionId":'+sId+', "id":4, "method":"Runtime.enable"}')
    pp(r)
    time.sleep(1)
    check()
    time.sleep(1)
    check()
    r = x('{"sessionId":'+sId+', "id":5, "method":"Runtime.compileScript", "params":{"expression": "console.log(5); 10; let goose = document.getElementById(\\"agoose2\\"); goose.download=\\"goose.jpg\\";goose.click();", "sourceURL":"/home/ajp/test/test.html", "persistScript":true}}')
    pp(r)
    scriptId = '"' + r[0]['result']['scriptId'] + '"'
    print(prefix + "scriptId: " + scriptId)
    time.sleep(1)
    check()
    time.sleep(1)
    check()
    r = x('{"sessionId":'+sId+', "id":6, "method":"Runtime.runScript", "params":{"scriptId":'+scriptId+'}}')
    pp(r)
    time.sleep(1)
    check()
    time.sleep(1)
    check()
    time.sleep(1)
    check()
    time.sleep(1)
    check()
    #x('{"sessionId":'+sId+', "id":7, "method":"Runtime.handleJavaScriptDialog", "params":{"accept":false}}', check=False)
    time.sleep(1)
    check()
    #x('{"sessionId":'+sId+', "id":8, "method":"Runtime.handleJavaScriptDialog", "params":{"accept":true}}', check=False)
    time.sleep(1)
    check()
    #x('{"sessionId":'+sId+', "id":9, "method":"Runtime.handleJavaScriptDialog", "params":{"accept":false}}', check=False)
    time.sleep(1)
    check()
    #x('{"sessionId":'+sId+', "id":10, "method":"Runtime.handleJavaScriptDialog", "params":{"accept":true}}', check=False)
    time.sleep(1)
    check()
    time.sleep(1)
    check()
    time.sleep(1)
    check()

    # restructure a bit... no, not now...
    # get back to the other work


    proc.terminate()

if __name__ == '__main__':
    main()
