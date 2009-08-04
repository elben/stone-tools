#!/usr/bin/python

import subprocess
import time
import os
import os.path
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
            logger=None, log_file='logs/stone-gentile.log',
            delay_wget=2, delay_http=5, delay_log=1):

        # set up logging
        if logger is None:
            self.log_file = log_file
            # set hierarchy
            self.logger = logging.getLogger('stone.gentile')
            self.logger.setLevel(logging.DEBUG)
            handler = logging.handlers.RotatingFileHandler(self.log_file,
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

        # create/update output file
        open(self.local_file, 'a').close()

        # set delay between requests
        self.delay_http = delay_http      # seconds
        self.delay_log = delay_log
        self.delay_wget = delay_wget
        self.prev_time_http = -delay_http # no delay on first run
        self.prev_time_log = -delay_log
        self.prev_time_wget = -delay_wget

    def connect(self, timeout=5, attempts=3):
        """
        Connect to specified URL.
        
        Call this method before calling other methods.
        """
        self.wget_proc = None
        try:
            self.log("Attempting to open " + self.url() + ".")
            self.extern_url = urllib2.urlopen(self.url(), timeout=timeout)
        except urllib2.URLError:
            msg = "Timeout attempting to open " + self.url() + "."
            self.log(msg, logging.CRITICAL)
            raise TimeoutException(msg)
        self.log("Opened " + self.url() + ".")

    def download(self, autokill=True):
        """
        Starts wget process if none existed; do nothing otherwise.

        If autokill is True, then WGet will kill and restart the
        wget process every delay_wget seconds.
        """
        delayed = time.time() - self.prev_time_wget >= self.delay_wget
        if not self.alive() and delayed:
            # wget not running
            self.start()
            self.prev_time_wget = time.time()
        elif autokill and self.alive() and delayed:
            self.terminate()
            self.start()
            self.prev_time_wget = time.time()

    def terminate(self):
        """
        Terminate wget process.
        """
        if self.alive():
            self.wget_proc.terminate()
            self.wget_proc = None
            self.log("wget terminated.")

    def alive(self):
        """Returns True if wget process is alive."""
        if self.wget_proc is None or self.wget_proc.poll() is not None:
            return False
        return True

    def size_extern(self):
        """Returns size (bytes) of external file."""
        if time.time() - self.prev_time_http >= self.delay_http:
            # regrab data
            self.extern_url = urllib2.urlopen(self.url(), timeout=5)
            self.extern_file_size = int(self.extern_url.info().dict['content-length'])
            self.prev_time_http = time.time()
            self.log("grabbed external file size: " + str(self.extern_file_size))
        return self.extern_file_size

    def size_local(self):
        """Returns size (bytes) of local file."""
        return os.path.getsize(self.local_file)

    def progress(self):
        return float(self.size_local())/self.size_extern()

    def url(self):
        return os.path.join(self.extern_dir, self.extern_file)

    def log_status(self):
        if time.time() - self.prev_time_log >= self.delay_log:
            self.log("wget alive: " + str(self.alive()))
            self.log("external file size: " + str(self.size_extern()))
            self.log("local file size: " + str(self.size_local()))
            self.prev_time_log = time.time()

    def log(self, msg, lvl=logging.DEBUG):
        self.logger.log(lvl, self.time()+" "+str(msg))

    def time(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        s = "wget alive: " + str(self.alive()) + "\n"
        s += "external file size: " + str(self.size_extern()) + "\n"
        s += "local file size: " + str(self.size_local())
        return s

    def start(self):
        """
        Starts a wget process.

        User should never call this. Call download() instead.
        """
        self.wget_proc = subprocess.Popen(['wget', '-c', self.url(), '-O',
            self.local_file], shell=False, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        self.log("wget started.")

class TimeoutException(Exception):
    pass
