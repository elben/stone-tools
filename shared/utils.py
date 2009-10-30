# Author: Elben Shira

import urllib2
import threading
import os

class Downloader(object):
    """
    Downloads a file from a URL to a local directory.
    
    Similar to GNU wget, Downloader continues a download if the file already
    exists locally. Downloader also allows the file being downloaded to grow
    in size.
    """
    def __init__(self, remote_url, remote_file,
            local_dir="", local_file=None,
            force_redl=True, rate_limit=-1):
        """
        Creates a Downloader with a specified URL to download from.

        Args:
            remote_url -- URL (including directory, excluding file name) of file
            remote_file -- file to download
            local_dir -- directory to save file to
            local_file -- name file will be saved as
            force_redl -- force reset a download; will not continue previous download
            rate_limit -- limit download at this rate
        """

        self.remote_url = remote_url
        self.remote_file = remote_file
        self.local_dir = local_dir
        # use same file name if user did not specify local_file name
        self.local_file = remote_file if not local_file else local_file
        
        if os.path.exists(self.local()) and not force_redl:
            # file already existed, get size and start download there
            self.size = os.path.getsize(self.local())
        else:
            self.size = 0

        # Request object represents file and the range we want to dl
        # TODO: header might be Request-Range. Read up on Apache stuff.
        self.request = urllib2.Request(self.remote(), headers={"Range",
            "bytes=%s-" % (str(self.size_local())))

        self.rate_limit = rate_limit        # -1 = do not cap rate
        self.rate = 0                       # current rate TODO: prob !need

    def _connect(self):
        """Connect to the remote URL and return response."""
        # TODO: implement time checking thing we do in gently.py's WGet
        # TODO: catch exceptions (HTTPError is one, but what if we are using
        # FTP or http protocol?)
        # response.info() returns the dict of http headers, HTTPMessage
        response = urllib2.urlopen(self.remote())
        return response

    def size_local(self):
        return self.size
    def size_remote(self):
        # TODO
        return 1
    def progress(self):
        """Returns percentage (0 to 1) done."""
        return self.size_local() / self.size_remote()
    def local(self):
        return os.path.join(self.local_dir, self.local_file)
    def remote(self):
        return os.path.join(self.remote_url, self.remote_file)

class DownloaderThread(threading.Thread):
    """NOTE: we can only overwrite __init__() and run()."""
