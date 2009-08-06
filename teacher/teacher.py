import subprocess as sp
import os
import time

video_dir = "/var/www/"
video_prefix = "disciple_"

def main():
    # initialize 
    current = []
    previous = []
    bad_files = []
    
    prev_symlink = None
    symbolic_link = None
    
    while True:
        # done at beginning to prevent spamming messages via 'continue'
        sleep_time = 10
        time.sleep(sleep_time)
        
        # keep previous sizes
        previous = []
        previous.extend(current)
        
        # get files and their sizes from the directory
        current = get_video_files(video_dir, video_prefix)
        
        if current == []:
            print "Waiting for video files..."
        
        # find bad files
        for file_i in current:
            for file_j in previous:
                # if files have the same name and the size has not grown
                # and that file is not already in bad_files
                if ( file_i[0] == file_j[0] and file_i[1] <= file_j[1] and
                     not file_i[0] in bad_files ):
                    
                    bad_files.append( file_i[0] )
                    
                    print "Added bad file" + file_i[0]
                    
                    print "Current bad files are:"
                    for f in bad_files:
                        print "  " + f
                    print ""
            
        if len(bad_files) == len(current) and len(current) != 0:
            print "No good files found!"
        
        # update symlink
        link_name = video_dir + "sermon_symlink"
        prev_symlink = symbolic_link
        symbolic_link = update_symlink(link_name, symbolic_link, current,
                                       bad_files)
        
        # print symlink changes if it changed from the previous iteration
        if prev_symlink != symbolic_link:
            print "Symbolic link set to", symbolic_link
            print ""
        
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
