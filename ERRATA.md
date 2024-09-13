TODO: Mark lack of gracefulness.
TODO: See if this works with async.
TODO: Try browser.close() w/ devtools command.
TODO: Make sure no-debug is silent silent.
TODO: Make a "kill"
TODO: Try moving over to async. process
TODO: Are we growing massive temporary directories.
TOOD: POPULATE

Windows:

1) We have to kill the browser process on close w/ a separate windows task. It's... not great.
2) The pipe stays open and our reader will block. 
3) We have to send an exit command ('{bye}\n') through the chromium side of the pipe and we also manually close file descriptors for pipes. However, the behavior seems to change if we're using async. In that case, os.close() is sufficient (it is not during sync type operations). The bad thing here is that with async i can't seem to catch the pipe closing, evne tho it functions correctly. Would like to see what the thread is doing.
