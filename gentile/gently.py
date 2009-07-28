#!/usr/bin/python

import subprocess
import time
import os
import urllib
import logging
import datetime

LOG_FILENAME = 'gently.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

devnull = open(os.devnull, 'w')

class WGet:
    def __init__(self, ip_addr, in_file, out_file, delay):
        self.ip_addr = ip_addr
        self.in_file = in_file
        self.out_file = out_file
        self.delay = delay
        self.url = urllib.urlopen(self.ip_addr + self.in_file)

        self.prev_time = 0
        self.wget_proc = None

    def terminate(self):
        if self.wget_proc is not None:
            self.wget_proc.terminate()
            self.wget_proc = None

    def download(self):
        if self.wget_proc is None or self.wget_proc.poll() is not None:
            # wget not running
            self.wget_proc = self.wget()

    def alive(self):
        if self.wget_proc is None:
            return False
        return True

    def old_next(self, restart=True):
        """
        An external force calls next() multiple times. next() only
        activates (does anything) if self.delay ms has passed since last
        call to next().

        next() will either start, terminate, or terminate then start a wget
        process:

        Returns True if we delete and start a new process, False otherwise.
        """
        if time.time() - self.prev_time > self.delay:
            if self.wget_proc != None:
                self.wget_proc.terminate()
                logging.debug(str(datetime.date.today()) + " terminated wget.")
            if restart:
                self.wget_proc = self.wget()
                logging.debug(str(datetime.date.today()) + " started wget.")
            self.prev_time = time.time()
            return True
        return False

    def wget(self):
        return subprocess.Popen(['wget', '-c', self.ip_addr + self.in_file],
                shell=False, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)

    def size(self):
        # time delay this request to like 5seconds per request or else it's
        # a DDOS attack
        #self.url = urllib.urlopen(self.ip_addr + self.in_file)
        return int(self.url.info().dict['content-length'])

"""
wget = WGet('http://elbenshira.com', '/d/file.ts', '', 5)
for i in wget.wget():
    print i
"""
