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
LOCAL_FILE = "sermon.ts"
#URL_PAUL = "http://10.100.1.243"
URL_PAUL = "http://localhost:8888/"
FILE_EXT = "pt"

class gui:
    w = 80
    h = 24
    s = curses.initscr()
    s = curses.newwin(24, 80)
    ptr_delay = -2e10   # only check every x seconds, but skip first delay
    ptr_files = []      # list of pt files found

def init_curses():
    curses.noecho()      # no keyboard echo
    try:
        curses.curs_set(0)   # hide cursor
    except: pass
    curses.cbreak()      # no waiting until [Enter]
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
    gui.s.nodelay(1)    # stop getch() from blocking
    gui.s.keypad(1)

def restore_screen():
    curses.nocbreak()
    curses.echo()
    curses.endwin()

def progress_bar(percent=0, row=0, col=0, color=0):
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
    if curses.has_colors():
        gui.s.addstr(row+1, col, s, curses.color_pair(color))
    else:
        gui.s.addstr(row+1, col, s)
    gui.s.addstr(row+2, col, s_top)

def draw_title(title="Gentile Monitor", border=True):
    gui.s.border() # draw sweet border
    start_col = gui.w/2 - len(title)/2
    gui.s.addstr(1, start_col, title)
    if border:
        gui.s.hline(2, 1, curses.ACS_HLINE, gui.w-2)
        gui.s.addch(2, 0, curses.ACS_LTEE)
        gui.s.addch(2, gui.w-1, curses.ACS_RTEE)

def find_video_ptrs():
    if time.time() - gui.ptr_delay >= 1:
        ptr_re = re.compile('"[^"]*\.' + FILE_EXT + '\"')
        ptr_files = []
        paul_url = urllib2.urlopen(URL_PAUL)
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

def draw_selector(selection, selected_row=0):
    draw_title("Video Selection")
    #selection = find_video_ptrs()

    row_disp = 3
    for v in range(len(selection)):
        if selected_row%len(selection) == v:
            gui.s.addstr(row_disp, 1, str(selection[v]), curses.A_STANDOUT)
        else:
            gui.s.addstr(row_disp, 1, str(selection[v]))
        row_disp += 1

def bytes2secs(bytes):
    return float(bytes)/(float(VIDEO_BITRATE)/8.0)

def secs2bytes(secs):
    return float(secs) * float(VIDEO_BITRATE) / 8.0

def video_select():
    """Select a pt file from URL_PAUL directory."""
    c = 0   # keyboard input
    selected_ptr = 0
    selection = find_video_ptrs()
    while True:
        gui.s.erase()
        draw_selector(selection, selected_ptr)
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
    return selected_ptr

def main():
    init_curses()

    # select a pt file
    # will continue to ask for a selection if
    # the previous selection was invalid
    while True:
        # select pt file
        selected_ptr = video_select()

        # download pointer file
        ptr_file = gui.ptr_files[selected_ptr]
        try:
            ptr_wget = gently.WGet(URL_PAUL, ptr_file, delay_wget=5)
            ptr_wget.download()
        except: continue

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
                remote_dir = file_contents[0].strip()
                
                # second line is the sermon video location
                remote_file = file_contents[1].strip()
        except:
            continue
            print "Failed to parse download location from pointer file!"
            return 1
        break   # got all the way here, so everything works!
    
    # remove previously played file
    if os.path.isfile(ptr_file):
        os.remove(ptr_file)
    
    wget = gently.WGet(remote_dir, remote_file, LOCAL_FILE, delay_wget=5)
    
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
    mplayer_once = True             # only run mplayer once
    while True:
        gui.s.erase()
        c = gui.s.getch()
        gui.s.addstr(22, 10, str(c))
        if c == ord('q'):
            wget.terminate()
            if mplayer is not None:
                mplayer.terminate()
            break
        elif c == ord('d'):
            download_file = not download_file 
        elif c == 260:  # left arrow
            if mplayer is not None:
                mplayer.stdin.write('j')
                #mplayer.communicate('j')
        elif c == 261:  # right arrow
            if mplayer is not None:
                mplayer.stdin.write('k')
                #mplayer.communicate('k')

        draw_title()
        # print status
        gui.s.addstr(4, 2, 'Download Status', curses.A_UNDERLINE)
        gui.s.addstr(4, 18, '(' + str(gui.ptr_files[selected_ptr]) + ')')
        if download_file:
            wget.download()
        else:
            wget.terminate()
        wget.log_status()

        # start mplayer
        if (mplayer_once and (mplayer == None or mplayer.poll() != None)
                and wget.size_local() > mplayer_size):
            mplayer = sp.Popen(["mplayer", LOCAL_FILE],
                    stdout=mplayer_stdout_file, stderr=mplayer_stderr_file,
                    stdin=sp.PIPE)
            mplayer_once = False

        bar_color = 2   # green
        if not wget.alive():
            bar_color = 1   # red
        progress_bar(wget.progress(), 6, 4, bar_color)
        gui.s.addstr(9, 4, "Size: " + str(wget.size_local()/1024/1024) + "/" +
                str(wget.size_remote()/1024/1024) + " MB")
        gui.s.addstr(10, 4, "Time: " + str(bytes2secs(wget.size_local())) + "/" +
                str(bytes2secs(wget.size_remote())) + " sec")
        gui.s.addstr(11, 4, "Time until catch-up: " + str(wget.alive()))
        gui.s.addstr(21, 4, str(wget.size_remote()))

        gui.s.addstr(13, 2, 'Playback Status', curses.A_UNDERLINE)
        progress_bar(.3, 15, 4)
        gui.s.addstr(18, 4, "Time Played:    15 min")
        gui.s.addstr(19, 4, "Total Time:     30 min")
        gui.s.addstr(20, 4, "Time Remaining:  2 min")

        gui.s.refresh()
        time.sleep(.1)          # to kill spinning

    # done playing! remove video file
    if os.path.isfile(LOCAL_FILE):
        os.remove(LOCAL_FILE)
    mplayer_stdout_file.close()
    restore_screen()


if __name__ == '__main__':
    try:
        main()
    except:
        restore_screen()
        traceback.print_exc()
