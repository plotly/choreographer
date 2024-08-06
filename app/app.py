#import devtools

from app_utils import start_browser

def main():
    proc, pipe = start_browser()

    pipe.write("{}")
    print(pipe.read(debug=True))

    # print(pipe.read(debug=True)) # this will block

    proc.terminate()
    proc.wait(10)
    proc.kill()

## NOTES
#
# os.set_blocking(from_chromium[0], False)
# except BlockingIOError:
#
#
# # read reach file close or EOF, empty  bytes, else block
#


if __name__ == '__main__':
    main()
