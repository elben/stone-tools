import gently
import os
import time

# amount the new file must differ by to be considered a new sermon
FS_DIFF = 0.5

# URL of teacher
URL = "http://10.100.1.242/"

# various file and directory names
WEB_DIR = "/var/www"
SERMON_DIR = "/sermons"
TEACHER_SYMLINK = "sermon_symlink"

def main():
    # create sermon directory if it doesn't exist
    try:
        os.mkdir(WEB_DIR + SERMON_DIR)
        print "Creating sermon directory in", "'" +  WEB_DIR + SERMON_DIR + "'"
    except:
        pass
    
    # various file names
    sermon_num = 1
    prefix = time.strftime("%m-%d-%Y_%H:%M_")
    filename = prefix + str(sermon_num)
    sermon_filename = WEB_DIR + SERMON_DIR + "/" + filename + ".ts"
    
    # create the object that will download, but only if the symlink exists
    while True:
        try:
            wget = gently.WGet(URL, TEACHER_SYMLINK,
                               sermon_filename, delay_wget = 5)
            wget.connect()
            break
        except:
            print "Waiting for teacher to create symlink..."
            time.sleep(0.5)
    
    print "Starting download to", sermon_filename
    print "Creating pointer file in '" + WEB_DIR + "'"
    create_pointer_file(WEB_DIR, SERMON_DIR, filename)
    
    # main loop
    fs = wget.size_remote()
    while True:
        # keep from burning cycles and spamming server with fs requests
        time.sleep(2)
        
        # update file size (not too often)
        prev_fs = fs
        fs = wget.size_remote()

        # if the file we're trying to download is 50% smaller than the last one
        # or if there is not a file at all
        if fs <= FS_DIFF * prev_fs:
            # create a new file name for it
            sermon_num += 1
            
            prefix = time.strftime("%m-%d-%Y_%H:%M_")
            filename = prefix + str(sermon_num)
            sermon_filename = WEB_DIR + SERMON_DIR + "/" + filename + ".ts"
            pointer_filename = WEB_DIR + "/" + filename
            
            # kill the old wget to start a new one
            try:
                wget.terminate()
            except:
                pass
            
            print "Downloading new sermon to ", "'" + sermon_filename + "'"
            print "Creating pointer file in '" + WEB_DIR + "'"
        
            # create the pointer file, which is downloaded by gentile
            create_pointer_file(WEB_DIR, SERMON_DIR, filename)
        
            # reconnect since the file download location changed
            while True:
                try:
                    wget = gently.WGet(URL, TEACHER_SYMLINK,
                                       sermon_filename, delay_wget = 5)
                    wget.connect()
                    break
                except:
                    print "Waiting for teacher to create symlink..."
                    time.sleep(0.5)
    
        # download the file (new or otherwise)
        wget.download(autokill = True)
        wget.log_status()

def create_pointer_file(web_dir, sermon_dir, name):
    with open(web_dir + "/" + name + ".pt", "w") as file:
        file.write(web_dir + sermon_dir + "/" + name + "\n")

if __name__ == "__main__":
    main()

