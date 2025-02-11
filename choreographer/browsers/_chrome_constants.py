import os
import platform

chromium_names = ["chromium", "chromium-browser"]

chrome_names = [
    "chrome",
    "Chrome",
    "google-chrome",
    "google-chrome-stable",
    "Chrome.app",
    "Google Chrome",
    "Google Chrome.app",
    "Google Chrome for Testing",
]
chrome_names.extend(chromium_names)

typical_chrome_paths = None
if platform.system() == "Windows":
    typical_chrome_paths = [
        r"c:\Program Files\Google\Chrome\Application\chrome.exe",
        f"c:\\Users\\{os.environ.get('USER', 'default')}\\AppData\\"
        "Local\\Google\\Chrome\\Application\\chrome.exe",
    ]
elif platform.system() == "Linux":
    typical_chrome_paths = [
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chrome",
    ]
else:  # assume mac, or system == "Darwin"
    typical_chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
