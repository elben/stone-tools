import gently.WGet
import os
import time
        
FS_DIFF = .5
sermon_num = 0
fs = 0
prev_fs = 0
symlink_file = "sermon.ts"

wget = gently.WGet(url, filename, outfile, delay_wget=5)
wget.connect()
while True:
    prev_fs = fs
    fs = wget.size_local()

    if fs < FS_DIFF * prev_fs:
        sermon_num += 1
        prefix = time.strftime("%Y-%m-%d_%H:%M:%S_")
        filename = prefix + str(sermon_num)
        wget.outfile = filename
        os.remove(symlink_file)
        os.symlink(symlink_file, filename)

        wget.connect()

    wget.download(autokill=True)
    wget.log_status()
