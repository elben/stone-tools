#!/usr/bin/python

import gently
import os
import sys
import time
import socket
import ConfigParser

# parse config file
config_file = "../config/config.conf"
if len(sys.argv) >= 2 and sys.argv[1] != '':
    # passed in as first argument
    config_file = sys.argv[1]
configs = ConfigParser.ConfigParser()
configs.read(config_file)

# amount the new file must differ by to be considered a new sermon
FS_DIFF = configs.getfloat("paul", "fs_diff")

# url of teacher
URL_TEACHER = configs.get("paul", "url_teacher")

# various file and directory names
WEB_DIR = configs.get("paul", "web_dir")
SERMON_DIR = configs.get("paul", "sermon_dir")
TEACHER_SYMLINK = configs.get("paul", "teacher_symlink")

# set the ip of the local machine, to put in pointer file
REPORTED_IP = configs.get("paul", "reported_ip")

def main():
    # create sermon directory if it doesn't exist
    try:
        os.mkdir(WEB_DIR + SERMON_DIR)
        print "Creating sermon directory in", "'" +  WEB_DIR + SERMON_DIR + "'"
    except:
        pass
    
    # various file names
    sermon_num = 1
    prefix = time.strftime("%m-%d-%Y_%H%M_")
    filename = prefix + str(sermon_num)
    sermon_filename = WEB_DIR + SERMON_DIR + "/" + filename + ".ts"
    
    # create the object that will download, but only if the symlink exists
    wget = gently.WGet( URL_TEACHER, TEACHER_SYMLINK,
                        sermon_filename, delay_wget = 5 )
    
    # wait for the symlink file to show up before starting
    print "Waiting for symlink to be created..."
    while not wget.remote_file_exists():
        time.sleep(1)
    print "Symlink found"
    print
    
    # start the download once we know the file exists    
    wget.download(autokill = True)
    
    print "Starting download to", "'" + sermon_filename + "'"
    print "Creating pointer file in", "'" + WEB_DIR + "'"
    create_pointer_file(WEB_DIR, SERMON_DIR, filename, REPORTED_IP)
    print
    
    # main loop
    fs = wget.size_remote()
    while True:
        # keep from burning cycles and spamming server with fs requests
        time.sleep(2)
        
        # update file size (not too often)
        prev_fs = fs
        fs = wget.size_remote()
        
        # if the file we're trying to download is much smaller
        # than the last one, or if there is not a file at all
        if fs <= FS_DIFF * prev_fs and fs != 0:
            # create a new file name for it
            sermon_num += 1
            
            prefix = time.strftime("%m-%d-%Y_%H%M_")
            filename = prefix + str(sermon_num)
            sermon_filename = WEB_DIR + SERMON_DIR + "/" + filename + ".ts"
            
            # kill the old wget to start a new one
            try:
                wget.terminate()
            except:
                pass
            
            print "Downloading new sermon to ", "'" + sermon_filename + "'"
            print "Creating pointer file in '" + WEB_DIR + "'"
            print
        
            # create the pointer file, which is downloaded by gentile
            create_pointer_file(WEB_DIR, SERMON_DIR, filename, REPORTED_IP)
            
            # we need to factor this part out, but i'm lazy right now
            # create the object that will download
            wget = gently.WGet( URL_TEACHER, TEACHER_SYMLINK,
                                sermon_filename, delay_wget = 5 )
            
            print "Waiting for symlink to be created..."
            while not wget.remote_file_exists():
                time.sleep(1)
            print "Symlink found"
            print
            
            print "Starting download to", "'" + sermon_filename + "'"
            print "Creating pointer file in", "'" + WEB_DIR + "'"
            create_pointer_file(WEB_DIR, SERMON_DIR, filename, REPORTED_IP)
            print
            
            # start the download once we know the file exists    
            wget.download(autokill = True)
        
        # download the file (new or otherwise)
        wget.download(autokill = True)
        wget.log_status()
        dload = str(int(wget.rate() / 1024 / 1024)) + " KB/s"
        
        # print out our status, to let us know paul is still working
        print "Downloading", "'" + sermon_filename + "'", "at", dload

def create_pointer_file(web_dir, sermon_dir, name, ip):
    with open(web_dir + "/" + name + ".pt", "w") as file:
        # first line is server ip and directory
        url = "http://" + ip + sermon_dir + "/" + "\n"
        
        # second is the file in that directory
        filename = name + ".ts" + "\n"
        
        str = url + filename
        
        file.write(str)

if __name__ == "__main__":
    main()
