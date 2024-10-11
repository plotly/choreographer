
import devtools
import time


browser = devtools.Browser(headless=False, debug=True)
old_temp_file = str(browser.temp_dir.name)
time.sleep(2)

browser.close()

time.sleep(2)

print(browser._retry_manual_delete(old_temp_file))
time.sleep(1)
print(browser._retry_manual_delete(old_temp_file, delete=True))
time.sleep(1)
print(browser._retry_manual_delete(old_temp_file))
time.sleep(1)

