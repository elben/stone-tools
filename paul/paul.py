import gently
import os
import sys
import time
import socket
import ConfigParser

# parse config file
config_file = "../config/config.conf"
if len(sys.argv) >= 2:
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
    while True:
        try:
            wget = gently.WGet(URL_TEACHER, TEACHER_SYMLINK, 
                               sermon_filename, delay_wget = 5)
            wget.download()
            break
        except:
            print "Waiting for teacher to create symlink..."
            time.sleep(0.5)
    
    print "Starting download to", "'" + sermon_filename + "'"
    print "Creating pointer file in '" + WEB_DIR + "'"
    create_pointer_file(WEB_DIR, SERMON_DIR, filename, REPORTED_IP)
    
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
        if fs <= FS_DIFF * prev_fs:
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
        
            # create the pointer file, which is downloaded by gentile
            create_pointer_file(WEB_DIR, SERMON_DIR, filename, REPORTED_IP)
        
            # reconnect since the file download location changed
            while True:
                try:
                    wget = gently.WGet(URL_TEACHER, TEACHER_SYMLINK,
                                       sermon_filename, delay_wget = 5)
                    wget.connect()
                    break
                except:
                    print "Waiting for teacher to create symlink..."
                    time.sleep(0.5)
            
        # download the file (new or otherwise)
        wget.download(autokill = True)
        wget.log_status()

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
