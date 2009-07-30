import gently
import time

url = "http://localhost:8888/elbenshira/d/"
filename = "rangers.mp3"
outfile = "out.mp3"

def main(argv=None):
    if argv is None:
        argv = sys.argv

    wget = gently.WGet(url, filename, outfile)

    while True:
        time.sleep(0.2)     # no spin zone!
        wget.download()
        wget.log_status()

if __name__ == '__main__':
    main()
