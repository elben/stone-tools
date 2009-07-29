#!/usr/bin/python

import subprocess
import time
import os
import urllib2
import logging
import logging.handlers
import time


devnull = open(os.devnull, 'w')

class WGet:
    """
    WGet is an intelligent wrapper around the wget process.
    Allows wgetting a growing file by restarting wget if it
    dies due to EOF. Also gives statistics of the download.
    """

    def __init__(self, extern_dir, extern_file, local_file=None,
            logger=None, delay_wget=1, delay_http=5, delay_log=5):

        # set up logging
        if logger is None:
            LOG_FILENAME = '/var/log/stone-gently.log'
            self.logger = logging.getLogger('stone-logger')
            self.logger.setLevel(logging.DEBUG)
            handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                    maxBytes=1000, backupCount=5)
            self.logger.addHandler(handler)
        else:
            self.logger = logger

        self.extern_dir = extern_dir
        self.extern_file = extern_file
        if local_file is None:
            self.local_file = self.extern_file
        else:
            self.local_file = local_file
        self.extern_file_size = 0

        self.wget_proc = None
        try:
            self.logger.debug("Attempting to open " + self.url() + ".")
            self.url = urllib2.urlopen(self.url(), timeout=5)
        except urllib2.URLError:
            msg = "Timeout attempting to open " + self.url() + "."
            self.logger.critical(msg)
            raise TimeoutException(msg)


        # create/update output file
        open(self.local_file, 'a').close()

        # set delay between HTTP requests
        self.delay_http = delay_http      # seconds
        self.delay_log = delay_log
        self.delay_wget = delay_wget
        self.prev_time_http = -delay_http # no delay on first run
        self.prev_time_log = -delay_log
        self.prev_time_wget = -delay_wget

    def wget(self):
        """
        Starts a wget process.
        User should never call this. Call download() instead.
        """
        return subprocess.Popen(['wget', '-c', self.url(),
            '-O', self.local_file], shell=False, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

    def download(self):
        """
        Starts wget process if none existed. Do nothing otherwise.
        """
        if (not self.alive() and
                time.time() - self.prev_time_wget >= self.delay_wget):
            # wget not running
            self.wget_proc = self.wget()
            self.prev_time_wget = time.time()

    def terminate(self):
        """
        Terminate wget process.
        """
        if self.alive():
            self.wget_proc.terminate()
            self.wget_proc = None

    def alive(self):
        if self.wget_proc is None or self.wget_proc.poll() is not None:
            return False
        return True

    def size_extern(self):
        # time delay this request to like 5seconds per request or else it's
        # a DDOS attack
        #self.url = urllib.urlopen(self.ip_addr + self.in_file)
        if time.time() - self.prev_time_http >= self.delay_http:
            self.extern_file_size = int(self.url.info().dict['content-length'])
            self.prev_time_http = time.time()
        return self.extern_file_size

    def size_local(self):
        return os.path.getsize(self.local_file)

    def progress(self):
        return float(self.size_local())/self.size_extern()

    def url(self):
        return self.extern_dir + self.extern_file

    def log(self):
        if time.time() - self.prev_time_log >= self.delay_log:
            self.logger.debug(self.time()+" "+str(self))
            self.prev_time_log = time.time()

    def time(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        s = "Wget Status: "
        if self.alive():
            s += "alive"
        else:
            s += "dead"
        s += "\n"
        s += "Current Size: " + str(self.size_local())
        s += "\n"
        s += "Incoming Size: " + str(self.size_extern())
        s += "\n"
        s += "Progress: {0:.2%}".format(self.progress())
        return s

    def old_next(self, restart=True):
        """
        An external force calls next() multiple times. next() only
        activates (does anything) if self.delay ms has passed since last
        call to next().

        next() will either start, terminate, or terminate then start a wget
        process:

        Returns True if we delete and start a new process, False otherwise.
        if time.time() - self.prev_time > self.delay:
            if self.wget_proc != None:
                self.wget_proc.terminate()
                logger.debug(str(datetime.date.today()) + " terminated wget.")
            if restart:
                self.wget_proc = self.wget()
                logger.debug(str(datetime.date.today()) + " started wget.")
            self.prev_time = time.time()
            return True
        return False
        """


"""
wget = WGet('http://elbenshira.com', '/d/file.ts', '', 5)
for i in wget.wget():
    print i
"""

class TimeoutException(Exception):
    pass
