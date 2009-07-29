import curses
import sys
import traceback
import gently
import subprocess
import os

class file:
    ip = "http://localhost:8888/elbenshira/d/"
    file = "rangers.mp3"
    #ip = "http://elbenshira.com/d/"
    #file = "elben_resume.pdf"
    out_file = ""

class gui:
    w = 80
    h = 24
    s = curses.initscr()
    s = curses.newwin(24, 80)

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
    if percent > 100:
        percent = 100
    elif percent <= 1 and percent > 0:
        percent *= 100
    elif percent < 0:
        percent = 0
    percent = int(percent)

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

def main():
    init_screen()
    gui.s.nodelay(1)    # stop getch() from blocking

    delay=32

    wget = None
    try:
        wget = gently.WGet(file.ip, file.file)
    except gently.TimeoutException:
        sys.exit()

    download_file = False
    dl_dots = 0
    c = 0
    while True:
        gui.s.erase()
        if c == ord('q'):
            wget.terminate()
            break
        elif c == ord('d'):
            download_file = not download_file 

        gui.s.border() # draw sweet border
        gui.s.addstr(1, 30, "Gentile Monitor")
        gui.s.hline(2, 1, ord('_'), gui.w-2)
        # print status
        gui.s.addstr(5, 1, 'Status:')
        if download_file:
            wget.download()
            gui.s.addstr(5, 9, 'Downloading' + ('.'*(dl_dots/delay)))
            if dl_dots >= delay*4:
                dl_dots = 0
            else:
                dl_dots += 1
        else:
            wget.terminate()

        wget.log()
        gui.s.addstr(9, 1, 'Wget Alive: \t' + str(wget.alive()))
        gui.s.addstr(6, 1, 'File Size: \t' + str(wget.size_extern()))
        gui.s.addstr(7, 1, 'Current Size: \t' + str(wget.size_local()))
        gui.s.addstr(8, 1, 'Progress: \t{0:.2%}'.format(wget.progress()))

        # bar not chnging?
        progress_bar(wget.progress(), 10, 1)

        c = gui.s.getch()
    restore_screen()


if __name__ == '__main__':
    try:
        main()
    except:
        restore_screen()
        traceback.print_exc()
