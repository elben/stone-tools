import curses
import sys
import traceback
import gently
import subprocess as sp
import os
import time
import urllib2
import re

VIDEO_BITRATE = 4500 # kbits / s
local_file = "sermon.ts"

class glob:
    dir = "http://localhost:8888/elbenshira/d/"
    #ip = "http://elbenshira.com/d/"
    #file = "elben_resume.pdf"
    out_file = ""
    URL_PAUL = "http://10.100.1.243"
    FILE_EXT = "pt"

class gui:
    w = 80
    h = 24
    s = curses.initscr()
    s = curses.newwin(24, 80)
    ptr_delay = time.time()
    ptr_files = []

def drawchar(chr, row, col, color=1):
    gui.s.addch(row, col, chr, curses.color_pair(1))

def init_screen():
    curses.noecho()      # no keyboard echo
    #curses.curs_set(0)  # hide cursor
    curses.cbreak()      # no waiting until [Enter]
    if curses.has_colors():
        curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)

def restore_screen():
    curses.nocbreak()
    curses.echo()
    curses.endwin()

def progress_bar(percent=0, row=0, col=0):
    if percent > 1:
        percent = 1
    elif percent < 0:
        percent = 0
    percent = int(percent*100)

    wait = "-"
    done = "|"
    tip = ">"
    num_done = percent/2
    num_wait = 50 - num_done

    # build bar
    s_top = '+' + '-'*48 + '+'
    s = done*num_done
    s += wait*num_wait

    gui.s.addstr(row, col, s_top)
    gui.s.addstr(row+1, col, s)
    gui.s.addstr(row+2, col, s_top)

def draw_title(title="Gentile Monitor", border=True):
    gui.s.border() # draw sweet border
    gui.s.addstr(1, 30, title)
    if border:
        gui.s.hline(2, 1, ord('_'), gui.w-2)

def find_video_ptrs():
    if time.time() - gui.ptr_delay >= 1:
        ptr_re = re.compile('"[^"]*\.' + glob.FILE_EXT + '\"')
        ptr_files = []
        paul_url = urllib2.urlopen(glob.URL_PAUL)
        for line in paul_url:
            search = ptr_re.search(line)
            if search is None:
                continue

            found = search.group(0)
            found = found.strip()
            found = found.strip('"')
            ptr_files.append(found)
        gui.ptr_files = ptr_files
    return gui.ptr_files

def draw_selector(selected_row=0):
    draw_title("Video Selection")
    videos = find_video_ptrs()

    row_disp = 3
    for v in range(len(videos)):
        if selected_row%len(videos) == v:
            gui.s.addstr(row_disp, 1, str(videos[v]), curses.A_STANDOUT)
        else:
            gui.s.addstr(row_disp, 1, str(videos[v]))
        row_disp += 1

def bytes2secs(bytes):
    return float(bytes)/(float(VIDEO_BITRATE)/8.0)

def secs2bytes(secs):
    return float(secs) * float(VIDEO_BITRATE) / 8.0

def main():
    init_screen()
    gui.s.nodelay(1)    # stop getch() from blocking
    gui.s.keypad(1)

    loop_delay = .1
    prev_loop_time = -loop_delay

    # for download "..."
    dots_delay = 0.5    # seconds
    prev_dots_time = -dots_delay
    dots_count = 0
    
    c = 0
    
    draw_time = time.time()
    selected_ptr = 0
    while True:
        gui.s.erase()

        draw_selector(selected_ptr)
        c = gui.s.getch()
        if c == curses.KEY_DOWN:
            selected_ptr += 1
        elif c == curses.KEY_UP:
            selected_ptr -= 1
        elif c == 10:
            # keypress ENTER
            break
        gui.s.addstr(20, 1, str(c))
        time.sleep(.001)
    selected_ptr %= len(gui.ptr_files) 

    # download pointer file
    ptr_file = gui.ptr_files[selected_ptr]
    ptr_wget = gently.WGet(glob.URL_PAUL, ptr_file, delay_wget=5)
    ptr_wget.download()

    # Wget setup
    # get the download location from the pointer file we were passed
    while not ptr_wget.finished():
        gui.s.addstr(20, 30, "Downloading...")
        time.sleep(.1)
    try:
        with open(ptr_file, "r") as file:
            # get data from pointer file
            file_contents = file.readlines()
            
            # first line is the server url and directory
            url = file_contents[0].strip()
            
            # second line is the sermon video location
            remote_file = file_contents[1].strip()
    except:
        print "Failed to parse download location from pointer file!"
        return 1
    
    # remove previously played file
    if os.path.isfile(ptr_file):
        os.remove(ptr_file)
    
    wget = gently.WGet(url, remote_file, local_file, delay_wget=5)
    
    if os.path.isfile("mplayer_stdout"):
        mplayer_stdout_file = open("mplayer_stdout", "rw")
    else:
        mplayer_stdout_file = open("mplayer_stdout", "a")

    if os.path.isfile("mplayer_stderr"):
        mplayer_stderr_file = open("mplayer_stderr", "rw")
    else:
        mplayer_stderr_file = open("mplayer_stderr", "a")
    
    download_file = False
    mplayer = None
    mplayer_size = secs2bytes(15)   # 15 second buffer
    mplayer_once = True
    
    while True:
        gui.s.erase()
        
        # handle input
        if c == ord('q'):
            wget.terminate()
            break
        elif c == ord('d'):
            download_file = not download_file 
        
        draw_title()
        
        # download status
        gui.s.addstr(4, 2, 'Download Status', curses.A_UNDERLINE)
        gui.s.addstr(4, 18, '(' + str(gui.ptr_files[selected_ptr]) + ')')
        if download_file:
            wget.download()
        else:
            wget.terminate()
        wget.log_status()
        
        if (mplayer_once and (mplayer == None or mplayer.poll() != None)
                and wget.size_local() > mplayer_size):
            mplayer = sp.Popen(["mplayer", local_file],
                    stdout=mplayer_stdout_file, stderr=mplayer_stderr_file,
                    stdin=sp.PIPE)
            mplayer_once = False
        progress_bar(wget.progress(), 6, 4)
        gui.s.addstr(9, 4, "Size: " + str(wget.size_local()/1024/1024) + "/" +
                str(wget.size_remote()/1024/1024) + " MB")
        gui.s.addstr(10, 4, "Time: " + str(bytes2secs(wget.size_local())) + "/" +
                str(bytes2secs(wget.size_remote())) + " sec")
        gui.s.addstr(11, 4, "Time until catch-up: 15 min")
        gui.s.addstr(21, 4, str(wget.size_remote()))
        
        # playback status
        gui.s.addstr(13, 2, 'Playback Status', curses.A_UNDERLINE)
        progress_bar(.3, 15, 4)
        gui.s.addstr(18, 4, "Time Played:    15 min")
        gui.s.addstr(19, 4, "Total Time:     30 min")
        gui.s.addstr(20, 4, "Time Remaining:  2 min")
        
        c = gui.s.getch()
        gui.s.refresh()
        time.sleep(.02)          # to kill spinning
    
    # done playing! remove video file
    if os.path.isfile(local_file):
        os.remove(local_file)
    mplayer_stdout_file.close()
    mplayer.terminate()
    restore_screen()

if __name__ == '__main__':
    try:
        main()
    except:
        restore_screen()
        traceback.print_exc()
