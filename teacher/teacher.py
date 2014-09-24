#!/usr/bin/python

import os
import sys
import time
import ConfigParser

# parse config file
config_file = "../config/config.conf"
if len(sys.argv) >= 2 and sys.argv[1] != '':
    # passed in as first argument
    config_file = sys.argv[1]
configs = ConfigParser.ConfigParser()
configs.read(config_file)

VIDEO_DIR = configs.get("teacher", "video_dir")
SIGNALS_DIR = configs.get("webapp", "signals_dir")
VIDEO_PREFIX = configs.get("teacher", "video_prefix")

def main():
    # initialize 
    current_files = []
    previous_files = []
    bad_files = []
    
    prev_symlink = None
    symbolic_link = None
    
    print "Starting program..."
    while True:
        # done at beginning to prevent spamming messages via 'continue'
        sleep_time = 2.5
        time.sleep(sleep_time)
        
        # keep previous sizes
        previous_files = []
        previous_files.extend(current_files)
        
        # get files and their sizes from the directory
        current_files = get_video_files(VIDEO_DIR, VIDEO_PREFIX)
        
        if current_files == []:
            print "Waiting for video files..."
        
        # find bad files
        for cur_name, cur_size in current_files:
            for prev_name, prev_size in previous_files:
                # if files have the same name and the size has not grown
                # and that file is not already in bad_files
                if ( cur_name == prev_name and cur_size <= prev_size ):
                    # don't add new recordings to bad_files
                    if cur_size <= 0.5 * prev_size:
                        # if it has shrunk drastically, it is no longer bad
                        print
                        print "New sermon found, removing from bad files"
                        
                        # remove it whether it's in bad_files or not
                        try:
                            bad_files.remove(cur_name)
                        except:
                            pass
                    else:
                        # add it to bad_files if it's not already there
                        if not cur_name in bad_files:
                            bad_files.append(cur_name)
                            
                            print "Added bad file", "'" + cur_name + "'"
                            
                            # parse the mac address  out of cur_name
                            mac_address = cur_name.split("_")[1]
                            
                            # remove the exist signal for this disciple
                            # so webapp can keep state
                            rm( os.path.join(SIGNALS_DIR,
                                             "exist_" + mac_address) )
                    
        if len(bad_files) == len(current_files) and len(current_files) != 0:
            print "No good files found!"
            
        # update symlink
        link_name = os.path.join(VIDEO_DIR, "sermon_symlink")
        prev_symlink = symbolic_link
        symbolic_link = update_symlink(link_name, symbolic_link, current_files,
                                       bad_files)
        
        # print symlink changes if it changed from the previous iteration
        if prev_symlink != symbolic_link:
            print "Symbolic link set to", symbolic_link
            print ""
        else:
            print "Symbolic link is", "'" + str(symbolic_link) + "'"
    
def update_symlink(link_name, cur_link, current_files, bad_files):
    """
    Update the current symlink to point to a known good file
    """
    # return this, stays the same if cur_link is not bad
    new_link = cur_link
    
    # as long as the symlink is to a bad file or does not exist
    if cur_link in bad_files or cur_link == None:
        # look through all the files and compare to the ones in bad_files
        for file_name, file_size in current_files:
            # set link to a file that is not bad
            if file_name not in bad_files:
                # we will return this
                new_link = file_name

                # remove old link if it exists
                rm(link_name)
                
                # create new symlink
                os.symlink(file_name, link_name)
                
                break
    
    return new_link

def rm(file):
    """
    Remove a file or directory, as long as it exists
    """
    if os.path.isfile(file) or os.path.islink(file):
        os.remove(file)
    elif os.path.isdir(file):
        os.rmdir(file)

def get_video_files(dir, prefix):
    """
    Get the names and sizes of all files in the given dir that match the prefix
    """
    video_files = []
    
    prefix = str(prefix)
    dir = str(dir)
    
    # get a list of strings representing files
    for file in os.listdir(dir):
        # make sure it's good, has a name with our prefix, and is not a dir
        if ( file.startswith(prefix) and not os.path.isdir(file) and
             not os.stat(os.path.join(dir, file)).st_size == 0 ):
            video_files.append(file)
    
    # get file sizes
    for i in range( len(video_files) ):
        # make each file into a tuple as (file name, file bytes)
        video_files[i] = ( video_files[i],
                           os.stat(os.path.join(dir, video_files[i])).st_size )
    
    return video_files

if __name__ == "__main__":
    main()
