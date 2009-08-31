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
MPLAYER_STDOUT_FILE = "mplayer_stdout"
MPLAYER_STDERR_FILE = "mplayer_stderr"
MPLAYER_AV_DELAY = -.3

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
        curses.init_pair(1, curses.COLOR_YELLOW, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
    gui.s.nodelay(1)    # stop getch() from blocking
    gui.s.keypad(1)

def restore_screen():
    curses.nocbreak()
    curses.echo()
    curses.endwin()

def progress_bar(percent=0, row=0, col=0, color=0, width=70):
    if percent > 1:
        percent = 1
    elif percent < 0:
        percent = 0
    percent = int(percent*100)

    wait = "-"
    done = "|"
    tip = ">"
    num_done = int(percent*(float(width)/100))
    num_wait = width - num_done
    
    # build bar
    s = done*num_done
    s += wait*num_wait

    # top line
    gui.s.hline(row, col+1, curses.ACS_HLINE, width)
    gui.s.addch(row, col, curses.ACS_ULCORNER)
    gui.s.addch(row, col+width+1, curses.ACS_URCORNER)

    # bottom line
    gui.s.hline(row+2, col+1, curses.ACS_HLINE, width)
    gui.s.addch(row+2, col, curses.ACS_LLCORNER)
    gui.s.addch(row+2, col+width+1, curses.ACS_LRCORNER)

    # side lines
    gui.s.addch(row+1, col, curses.ACS_VLINE)
    gui.s.addch(row+1, col+width+1, curses.ACS_VLINE)

    if curses.has_colors():
        gui.s.addstr(row+1, col+1, s, curses.color_pair(color))
        gui.s.addstr(row+1, col + (width/2)-1, str(percent)+"%",
                curses.color_pair(color))
    else:
        gui.s.addstr(row+1, col+1, s)
        gui.s.addstr(row+1, col + (width/2)-2, str(percent)+" %")

def draw_title(title="Gentile Monitor", border=True):
    gui.s.border() # draw sweet border
    start_col = gui.w/2 - len(title)/2
    gui.s.addstr(1, start_col, title)
    if border:
        gui.s.hline(2, 1, curses.ACS_HLINE, gui.w-2)
        gui.s.addch(2, 0, curses.ACS_LTEE)
        gui.s.addch(2, gui.w-1, curses.ACS_RTEE)

def draw_status(status="press h for help"):
    gui.s.addstr(gui.h-2, 1, status.center(gui.w-2))

def find_video_ptrs():
    delay_time = 1  # seconds
    if time.time() - gui.ptr_delay >= delay_time:
        ptr_re = re.compile('"[^"]*\.' + FILE_EXT + '\"')
        ptr_files = []
        while True:
            try:
                paul_url = urllib2.urlopen(URL_PAUL)
                break
            except: 
                draw_status("Attempting to connect...")
                gui.s.refresh()
                time.sleep(delay_time)
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

def mplayer_status(file, seek=1024):
    """Returns string in HH:MM:SS format."""
    mp_status_re = re.compile(" +V: +[0-9]+\.[0-9]")
      
    with open(file, "r") as f:
        # find pos to seek to; make sure it is legal pos
        pos = max(os.path.getsize(file) - seek, 0)
        f.seek(pos)
        contents = f.read(seek)
        found = mp_status_re.findall(contents)
        if len(found) >= 1:
            last = found[-1]
            last = last.strip(" V:")
            return int(float(last))
        return 0

def secs2str(secs):
    secs = int(secs)
    hrs = secs / 3600
    secs -= hrs * 3600
    mins = secs / 60
    secs -= mins * 60
    return "{0}:{1:02}:{2:02}".format(hrs, mins, secs)
    #return str(hrs) + ":" + str(mins) + ":" + str(secs)

def bytes2secs(bytes):
    return float(bytes)/(float(VIDEO_BITRATE)/8.0)/1000

def secs2bytes(secs):
    return float(secs) * float(VIDEO_BITRATE) / 8.0 * 1000

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
    
    mplayer_stdout_file = open(MPLAYER_STDOUT_FILE, "w")
    mplayer_stderr_file = open(MPLAYER_STDERR_FILE, "w")
    
    download_file = False
    mplayer = None
    mplayer_size = secs2bytes(15)   # 15 second buffer
    mplayer_start = False           # wait for user to start mplayer
    a_v_diff = 0
    display_help = False
    while True:
        gui.s.erase()

        c = gui.s.getch()
        gui.s.addstr(21, 4, str(c))    # display key vals for debug
        if c == ord('q'):
            wget.terminate()
            if mplayer is not None:
                mplayer.terminate()
            break
        elif c == ord('d'):
            download_file = not download_file 
        elif c == ord('m'):
            mplayer_start = not mplayer_start
        elif c == ord('h'):
            display_help = not display_help
        elif c == 32:   # space bar
            if mplayer is not None:
                mplayer.stdin.write('p')    # pause
        elif c == ord('o'):
            if mplayer is not None:
                mplayer.stdin.write('o')    # toggle OSD display
        elif c == 260:  # left arrow
            if mplayer is not None:
                mplayer.stdin.write('h')    # short seek left
        elif c == 261:  # right arrow
            if mplayer is not None:
                mplayer.stdin.write('j')    # short seek right
        elif c == 44:   # ,
            if mplayer is not None:
                mplayer.stdin.write('g')    # medium seek left
        elif c == 46:   # .
            if mplayer is not None:
                mplayer.stdin.write('k')    # medium seek right
        elif c == 91:   # [
            if mplayer is not None:
                mplayer.stdin.write('f')    # long seek left
        elif c == 93:   # ]
            if mplayer is not None:
                mplayer.stdin.write('l')    # long seek right
        elif c == 45:   # -
            if mplayer is not None:
                mplayer.stdin.write('z')    # short sound sync left
                a_v_diff -= 5
        elif c == 61:   # =
            if mplayer is not None:
                mplayer.stdin.write('x')    # short sound sync right
                a_v_diff += 5
        elif c == 57:   # 9
            if mplayer is not None:
                mplayer.stdin.write('a')    # medium sound sync left
                a_v_diff -= 50
        elif c == 48:   # 0
            if mplayer is not None:
                mplayer.stdin.write('s')    # medium sound sync right
                a_v_diff += 50
        elif c == 55:   # 7
            if mplayer is not None:
                mplayer.stdin.write('q')    # long sound sync right
                a_v_diff -= 500
        elif c == 56:   # 8
            if mplayer is not None:
                mplayer.stdin.write('w')    # long sound sync right
                a_v_diff += 500

        # wget process
        if download_file:
            wget.download()
        else:
            wget.terminate()
        wget.log_status()

        # mplayer process
        if (mplayer_start and (mplayer == None or mplayer.poll() != None)
                and wget.size_local() > mplayer_size):
            # TODO: take out hardcoded delay
            mp_args = ["mplayer", "-osdlevel", "0", "-mc", "3",
                    "-framedrop", "-delay", str(MPLAYER_AV_DELAY), LOCAL_FILE]
            mplayer = sp.Popen(mp_args,
                    stdout=mplayer_stdout_file, stderr=mplayer_stderr_file,
                    stdin=sp.PIPE)
            a_v_diff = int(1000*MPLAYER_AV_DELAY)    # reset audio/video delay
        elif not mplayer_start and mplayer is not None:
            mplayer.terminate()
            mplayer = None

        # download and playback statistics
        time_local = bytes2secs(wget.size_local())
        time_remote = bytes2secs(wget.size_remote())
        time_playback = mplayer_status(MPLAYER_STDOUT_FILE)

        draw_title()

        # display download progress bar
        # color:   yellow (wget dead)      red (do not dl)       green (dling)
        bar_color = 1 if not wget.alive() else (2 if not download_file else 3)
        progress_bar(wget.progress(), 6, 4, bar_color)
        
        # display download stats
        gui.s.addstr(4, 2, 'Download Status', curses.A_UNDERLINE)
        gui.s.addstr(4, 18, '(' + str(gui.ptr_files[selected_ptr]) + ')')
        gui.s.addstr(9, 4, "Size: " +
                "{0:0.1f}".format(float(wget.size_local())/1024/1024) + " of " +
                "{0:0.1f}".format(float(wget.size_remote())/1024/1024) +
                " MB")
        gui.s.addstr(10, 4, "Time: " + secs2str(time_local) + " of " +
                secs2str(time_remote))
        gui.s.addstr(11, 4, "Rate: " + str(int(wget.rate())/1024/1024) +
                " MB/s")
        #gui.s.addstr(12, 4, "Time until catch-up: unimplemented")

        # display playback status
        gui.s.addstr(13, 2, 'Playback Status', curses.A_UNDERLINE)
        gui.s.addstr(18, 4, "Time: " + secs2str(time_playback)
                + " of " + secs2str(time_local))
        gui.s.addstr(19, 4, "Time Remaining: " +
                secs2str(time_local-time_playback))
        gui.s.addstr(20, 4, "A-V: " + str(a_v_diff) + " ms")

        # display playback progress bar
        try:
            playback_progress = time_playback / time_local
        except:
            playback_progress = 0
        bar_color = 3   # green
        if mplayer_start and mplayer is None:
            bar_color = 1   # yellow
        if not mplayer_start:
            bar_color = 2   # red
        progress_bar(playback_progress, 15, 4, bar_color)

        draw_status()
        if display_help:
            draw_help()
        gui.s.refresh()
        time.sleep(.1)          # to kill spinning

    # done playing! remove video file
    #if os.path.isfile(LOCAL_FILE):
    #    os.remove(LOCAL_FILE)

    mplayer_stdout_file.close()
    mplayer_stderr_file.close()
    restore_screen()

def draw_help(row=3, col=48):
    help = [
        " -----------main------------ ",
        " q       quit                ",
        " h       show/hide help      ",
        " d       start/stop download ",
        " m       start/stop mplayer  ",
        " [space] pause video         ",
        " o       show/hide OSD       ",
        "                             ",
        " -----------seek------------ ",
        "        left  right          ",
        " short: <--    -->           ",
        " medium: ,      .            ",
        " long:   [      ]            ",
        "                             ",
        " -------audio sync---------- ",
        "        left  right          ",
        " short:  -      =            ",
        " medium: 9      0            ",
        " long:   7      8            ",]
    for h in help:
        if curses.has_colors():
            gui.s.addstr(row, col, h, curses.color_pair(4))
        else:
            gui.s.addstr(row, col, h)
        row += 1

if __name__ == '__main__':
    try:
        main()
    except:
        restore_screen()
        traceback.print_exc()

