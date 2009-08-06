import gently
import time
import sys
import subprocess as sp

#url = "http://localhost:8888/elbenshira/d/"
url = "http://192.168.1.101"
remote_file = "sermon.ts"
local_file = "sermon.ts"

def main(argv=None):
    if argv is None:
        argv = sys.argv

    wget = gently.WGet(url, remote_file, local_file, delay_wget=5)
    
    mplayer = None
    mplayer_size = 25000
    
    while True:
        time.sleep(0.2)     # no spin zone!
        wget.download(autokill=True)
        
        if ( (mplayer == None or mplayer.poll() != None)
             and wget.size_local() > mplayer_size ):
            mplayer = sp.Popen( ["mplayer", local_file] )
        
        wget.log_status()

if __name__ == '__main__':
    main()
