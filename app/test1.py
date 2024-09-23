
import devtools
import time


browser = devtools.Browser(headless=False, debug=True)

time.sleep(2)

browser.close()
