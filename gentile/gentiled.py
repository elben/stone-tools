import gently
import time
import sys

#url = "http://localhost:8888/elbenshira/d/"
url = "http://192.168.1.101"
filename = "sermon.ts"
outfile = "sermon.ts"

def main(argv=None):
    if argv is None:
        argv = sys.argv

    wget = gently.WGet(url, filename, outfile, delay_wget=5)
    wget.connect()

    while True:
        time.sleep(0.2)     # no spin zone!
        wget.download(autokill=True)
        wget.log_status()

if __name__ == '__main__':
    main()
