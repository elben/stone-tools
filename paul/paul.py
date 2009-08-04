import gently.WGet
import os
import time

# amount the new file must differ by to be considered a new sermon
FS_DIFF = .5

# how many sermons we've downloaded so far
sermon_num = 0

# file size storage, for comparison
fs = 0
prev_fs = 0

symlink_file = "sermon.ts"
wget = gently.WGet(url, filename, outfile, delay_wget=5)
wget.connect()

while True:
    # keep from burning cycles and spamming server with fs requests
    time.sleep(2)
    
    # update file size (not too often)
    prev_fs = fs
    fs = wget.size_local()
    
    # set the file name
    prefix = time.strftime("%Y-%m-%d_%H:%M:%S_")
    filename = prefix + str(sermon_num)
    
    # if the file we're trying to download is 50% smaller than the last one
    if fs < FS_DIFF * prev_fs:
        # create a new file name for it
        sermon_num += 1
        prefix = time.strftime("%Y-%m-%d_%H:%M:%S_")
        filename = prefix + str(sermon_num)
        
        # chenge the downlaod clocation and symlink to the new file
        wget.outfile = filename
        os.remove(symlink_file)
        os.symlink(symlink_file, filename)
        
        # reconnect since the file download location changed
        wget.connect()
    
    # download the file (new or otherwise)
    wget.download(autokill=True)
    wget.log_status()
