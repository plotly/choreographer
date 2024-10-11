
import devtools
import time


browser = devtools.Browser(headless=False, debug=True)
old_temp_file = str(browser.temp_dir.name)
time.sleep(2)

browser.close()

time.sleep(1)

print("Counting".center(20, "-"))
count = browser._retry_delete_manual(old_temp_file)
print(f"Found {count[0]} files, {count[1]} directories")
print(f"Errors: {count[2]}")

time.sleep(1)

print("Deleting".center(20, "-"))
count = browser._retry_delete_manual(old_temp_file, delete=True)
print(f"Errors: {count[2]}")

time.sleep(1)

print("Counting".center(20, "-"))
count = browser._retry_delete_manual(old_temp_file)
print(f"Found {count[0]} files, {count[1]} directories")
print(f"Errors: {count[2]}")

