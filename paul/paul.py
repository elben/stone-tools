import gently
import os
import time

# amount the new file must differ by to be considered a new sermon
FS_DIFF = 0.5

# how many sermons we've downloaded so far
sermon_num = 0

# file size storage, for comparison
fs = 0
prev_fs = 0

symlink_file = "sermon_symlink"
local_symlink = "sermon.ts"
url = "http://10.100.1.242/"

web_dir = "/var/www/"
prefix = time.strftime("%m-%d-%Y_%H:%M_")
filename = web_dir + prefix + str(sermon_num)

wget = gently.WGet(url, symlink_file, filename, delay_wget=5)
wget.connect()

try:
    os.remove(web_dir + local_symlink)
except:
    pass

os.symlink(filename, web_dir + local_symlink)

print "Starting download to", filename
while True:
    # keep from burning cycles and spamming server with fs requests
    time.sleep(2)
    
    # update file size (not too often)
    prev_fs = fs
    fs = wget.size_remote()

    # if the file we're trying to download is 50% smaller than the last one
    if fs < FS_DIFF * prev_fs:
        # create a new file name for it
        sermon_num += 1
        prefix = time.strftime("%m-%d-%Y_%H:%M_")
        filename = web_dir + prefix + str(sermon_num)
        
        # start a new wget and symlink to the new file
        wget.terminate()
        
        print "New sermon started remotely, downloading to", filename
        
        wget = gently.WGet(url, symlink_file, filename, delay_wget=5)
        
        try:
            os.remove(web_dir + local_symlink)
        except:
            pass
        
        os.symlink(filename, web_dir + local_symlink)
        
        # reconnect since the file download location changed
        wget.connect()
    
    # download the file (new or otherwise)
    wget.download(autokill=True)
    wget.log_status()
