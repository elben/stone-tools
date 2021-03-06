#!/usr/bin/python

import subprocess
import time
import os
import os.path
import urllib2
import logging
import logging.handlers
import time

class WGet:
    """
    WGet is an intelligent wrapper around the wget process.
    Allows wgetting a growing file by restarting wget if it
    dies due to EOF. Also gives statistics of the download.
    """

    def __init__(self, remote_dir, remote_file, local_file=None,
            logger=None, log_file='logs/stone-gentile.log',
            delay_wget=5, delay_http=5, delay_log=1):
        
        # make sure we have a log directory so we don't crash (UBER ANNOYING)
        try:
            os.mkdir("logs")
        except:
            pass
        
        self.wget_proc = None
        self.devnull = open(os.devnull, 'w')     # dump stdin/out to

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

        self.remote_dir = remote_dir
        self.remote_file = remote_file
        if local_file is None:
            self.local_file = self.remote_file
        else:
            self.local_file = local_file
        self.remote_file_size = 0

        # create/update output file
        open(self.local_file, 'a').close()

        # set delay between requests
        self.delay_http = delay_http      # seconds
        self.delay_log = delay_log
        self.delay_wget = delay_wget      # secs between wget restarts
        self.prev_time_http = -delay_http # no delay on first run
        self.prev_time_log = -delay_log
        self.prev_time_wget = -delay_wget

        self.delay_rate = .26   # seconds
        self.prev_time_rate = -self.delay_rate

        self.prev_sizes= []
        self.max_history = 10
        self.dl_rate = 0    # bytes/s

    def download(self, autokill=True):
        """
        Starts wget process if none existed; do nothing otherwise.

        If autokill is True, then WGet will kill and restart the
        wget process every delay_wget seconds.
        
        Calling download() does not guarantee that the file will download
        completely. Thus, the user should call download() continuously to
        download a file. Example:

            while not wget.finished():
                wget.download()
        """
        enough_delay = time.time() - self.prev_time_wget >= self.delay_wget
        if not self.alive() and enough_delay:
            # wget not running
            self.start()
            self.prev_time_wget = time.time()
        elif autokill and self.alive() and enough_delay:
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
            self.prev_time_wget = -self.delay_wget  # instant restart
            self.log("wget terminated.")

    def alive(self):
        """Returns True if wget process is alive."""
        if self.wget_proc is None or self.wget_proc.poll() is not None:
            return False
        return True

    def size_remote(self):
        """Returns size (bytes) of remote file."""
        if time.time() - self.prev_time_http >= self.delay_http:
            # regrab data
            self.connect(timeout=10)
            self.remote_file_size = int(self.remote_url.info().dict['content-length'])
            self.prev_time_http = time.time()
            self.log("grabbed remote file size: " + str(self.remote_file_size))
        return self.remote_file_size    # use old data

    def size_local(self):
        """Returns size (bytes) of local file."""
        return os.path.getsize(self.local_file)

    def rate(self):
        """
        Returns rate of download in bytes/sec.
        
        User must call rate continually to get an accurate rate.
        """

        if time.time() - self.prev_time_rate >= self.delay_rate:
            self.prev_time_rate = time.time()

            # save size
            if len(self.prev_sizes) >= self.max_history:
                del self.prev_sizes[0]
            self.prev_sizes.append(self.size_local())

            # calc new rate
            prev = 0
            total = 0
            for i in range(len(self.prev_sizes)-1):
                total += self.prev_sizes[i+1] - self.prev_sizes[i]
                
            self.dl_rate = total / self.delay_rate / len(self.prev_sizes) 
        return self.dl_rate

    def remote_file_exists(self):
        """Returns True if the remote file exists; False otherwise."""
        try:
            self.connect()
            return True
        except:
            return False
        
    def finished(self):
        return self.size_remote() == self.size_local()

    def progress(self):
        return float(self.size_local())/self.size_remote()

    def url(self):
        return os.path.join(self.remote_dir, self.remote_file)

    def log_status(self):
        if time.time() - self.prev_time_log >= self.delay_log:
            self.log("wget alive: " + str(self.alive()))
            self.log("remote file size: " + str(self.size_remote()))
            self.log("local file size: " + str(self.size_local()))
            self.prev_time_log = time.time()

    def log(self, msg, lvl=logging.DEBUG):
        self.logger.log(lvl, self.time()+" "+str(msg))

    def time(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        s = "wget alive: " + str(self.alive()) + "\n"
        s += "remote file size: " + str(self.size_remote()) + "\n"
        s += "local file size: " + str(self.size_local())
        return s

    def connect(self, timeout=5):
        """
        Attempt to connect to specified URL.

        User should not call this method.
        """
        try:
            self.remote_url = urllib2.urlopen(self.url(), timeout=timeout)
        except urllib2.URLError:
            msg = "Timeout attempting to open " + self.url() + "."
            self.log(msg, logging.CRITICAL)
            raise TimeoutException(msg)

    def start(self):
        """
        Starts a wget process.

        User should never call this. Call download() instead.
        """
        self.wget_proc = subprocess.Popen(['wget', '-c', self.url(), '-O',
            self.local_file], shell=False, stdout=self.devnull,
            stderr=self.devnull)
        self.log("wget started.")

class TimeoutException(Exception):
    pass
