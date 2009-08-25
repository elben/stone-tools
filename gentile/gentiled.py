import gently
import time
import sys
import subprocess as sp

LOCAL_FILE = "sermon.ts"

def main(argv = None):
    if argv is None:
        argv = sys.argv
    
    # get the download location from the pointer file we were passed
    try:
        with open(argv[0], "r") as file:
            # get data from pointer file
            file_contents = file.readlines()
            
            # first line is the server url and directory
            url = file_contents[0].strip()
            
            # first line is the sermon video location
            remote_file = file_contents[1].strip()
    except:
        print "Failed to parse download location from pointer file!"
        return 1
    
    # remove previously played file
    try:
        os.remove(LOCAL_FILE)
    except:
        pass
    
    wget = gently.WGet(url, remote_file, LOCAL_FILE, delay_wget=5)
    
    mplayer = None
    mplayer_size = 25000
    
    while True:
        time.sleep(0.1)     # no spin zone!
        wget.download(autokill=True)
        
        if ( (mplayer == None or mplayer.poll() != None)
             and wget.size_local() > mplayer_size ):
            mplayer = sp.Popen( ["mplayer", LOCAL_FILE] )
        
        wget.log_status()

if __name__ == '__main__':
    main()
