import os
import time

VIDEO_DIR = "/var/www/"
VIDEO_PREFIX = "video_"

def main():
    # initialize 
    current = []
    previous = []
    bad_files = []
    
    prev_symlink = None
    symbolic_link = None
    
    print "Starting program..."
    while True:
        # done at beginning to prevent spamming messages via 'continue'
        sleep_time = 2
        time.sleep(sleep_time)
        
        # keep previous sizes
        previous = []
        previous.extend(current)
        
        # get files and their sizes from the directory
        current = get_video_files(VIDEO_DIR, VIDEO_PREFIX)
        
        if current == []:
            print "Waiting for video files..."
        
        # find bad files
        for file_cur in current:
            for file_prev in previous:
                # if files have the same name and the size has not grown
                # and that file is not already in bad_files
                if ( file_cur[0] == file_prev[0] and
                     file_cur[1] <= file_prev[1] ):
                    
                    # don't add new recordings to bad_files
                    if file_cur[1] <= 0.5 * file_prev[1]:
                        # if it has shrunk drastically, it is no longer bad
                        print ""
                        print "New sermon found, removing from bad files"
                        
                        try:
                            bad_files.remove(file_cur[0])
                        except:
                            pass
                    else:
                        # add it to bad_files if it's not already there
                        if not file_cur[0] in bad_files:
                            bad_files.append( file_cur[0] )
                            
                            print "Added bad file" + file_cur[0]
                    
        if len(bad_files) == len(current) and len(current) != 0:
            print "No good files found!"
            
        # update symlink
        link_name = VIDEO_DIR + "sermon_symlink"
        prev_symlink = symbolic_link
        symbolic_link = update_symlink(link_name, symbolic_link, current,
                                       bad_files)
        
        # print symlink changes if it changed from the previous iteration
        if prev_symlink != symbolic_link:
            print "Symbolic link set to", symbolic_link
            print ""
        else:
            print "Symbolic link is", "'" + str(symbolic_link) + "'"
        
def update_symlink(link_name, cur_link, current_files, bad_files):
    if cur_link in bad_files or cur_link == None:
        for file in current_files:
            if file[0] not in bad_files:
                cur_link = file[0]
                
                # remove old link if it exists
                try:
                    os.remove(link_name)
                except:
                    pass
                
                # create new symlink
                os.symlink(cur_link, link_name)
                
                break
    
    return cur_link

def get_video_files(dir, prefix):
    video_files = []
    
    prefix = str(prefix)
    dir = str(dir)
    
    # get a list of strings representing files
    for file in os.listdir(dir):
        # make sure it's good, has a name with our prefix, and is not a dir
        if ( file.startswith(prefix) and not os.path.isdir(file) and
             not os.stat(dir + file).st_size == 0):
            video_files.append(dir + file)
    
    # get file sizes
    for i in range( len(video_files) ):
        # make each file into a tuple as (full file name, file bytes)
        video_files[i] = ( video_files[i],
                           os.stat(video_files[i]).st_size )
    
    return video_files

if __name__ == "__main__":
    main()
