import devtools

from app_utils import start_browser

def main():
    print(dir(devtools))
    print("Hello")
    process = start_browser()
    browser = devtools.Connection(process)
    print(dir(browser))

if __name__ == '__main__':
    main()
