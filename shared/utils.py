import urllib2
import threading
import os
import time

# global download rate variable, READ ONLY!
# if you write to this, you WILL break DownloadRateThread's execution
global_download_rate = 0.0

def enough_delay(prev_time, min_gap):
    """Returns True if enough time has passed since prev_time."""
    return time.time() - prev_time >= min_gap

class Downloader(object):
    """
    Downloads a file from a URL to a local directory.
    
    Similar to GNU wget, Downloader continues a download if the file already
    exists locally. Downloader also allows the file being downloaded to grow
    in size.
    """
    def __init__(self, remote_url, remote_file,
            local_dir = "", local_file = None,
            force_redownload = False, rate_limit = -1):
        """
        Creates a Downloader with a specified URL to download from.
        
        Args:
            remote_url: URL (including directory, excluding file name)
              of file
            remote_file: file to download
            local_dir: directory to save file to
            local_file: name file will be saved as
            force_redownload: force reset a download; will not continue
              previous download
            rate_limit: limit download at this rate
        """
        
        self._remote_url = remote_url
        self._remote_file = remote_file
        self._local_dir = local_dir
        # use same file name if user did not specify local_file name
        self._local_file = remote_file if not local_file else local_file
        
        if os.path.exists(self.local()) and not force_redownload:
            # file already existed, get size and start download there
            # TODO: don't need to save local_size here since we can call
            # get_local_size() later when we need it
            self._local_size = os.path.getsize( self.local() )
        else:
            self._local_size = 0
        
        self._remote_size = 0
        
        # Request object represents file and the range we want to dl
        # TODO: header might be Request-Range. Read up on Apache stuff.
        # TODO: move this into the run() method or download()
        self.request = urllib2.Request(self.remote(), headers = {"Range" :
            "bytes=%s-" % (str(self.get_local_size())) } )
        
        self.rate_limit = rate_limit        # -1 = do not cap rate
        self.rate = 0                       # current rate TODO: prob !need
        
        self._update()
        self.__prev_time_update = time.time()
        self.__update_time_gap = 5          # seconds
    
    def run(self):
        pass
    
    def get_download_rate(self):
        """Returns the current download rate in KB/s"""
        # makes sure that we are getting the global variable, not creating a
        # new, local one
        global global_download_rate
        
        return global_download_rate
    
    def _update(self):
        """Connect to the remote URL and update remote file info."""
        # TODO: implement time checking thing we do in gently.py's WGet
        # TODO: catch exceptions
        # apparently it could throw:
        #   urllib2.HTTPError - most likely, couldn't connect
        #   urllib2.URLError - if we use improper protocol "httpdfsk://..."
        #   httplib.BadStatusLine
        #   httplib.InvalidURL
        #   ValueError
        #   IOError
        if enough_delay(self.__prev_time_update, self.__update_time_gap):
            self.__prev_time_update = time.time()
            try:
                response = urllib2.urlopen(self.remote())
                info = response.info() # dict of http headers, HTTPMessage
                self._remote_size = int(info["content-length"])
            except Exception, e:
                # print out whatever Exception object we caught, so we
                # at least know what it was
                print e
            
    def get_progress(self):
        """Returns percentage (0.0 to 1.0) done."""
        if self._remote_size == 0:
            return 0.0
        return float( self.get_local_size() ) / self.remote_size()
    
    def get_local_size(self):
        """Return the size of the locally downloaded file."""
        return os.path.getsize(self.local())
    
    def get_remote_size(self):
        """Return the size of the remote file."""
        self._update()
        return self._remote_size
    
    def get_local_path(self):
        """Returns the local file path including file name."""
        return os.path.join(self._local_dir, self._local_file)
    
    def get_remote_url(self):
        """Returns the remote URL including file name."""
        return os.path.join(self._remote_url, self._remote_file)
    
class DownloadRateThread(threading.Thread):
    """Continuously calculate the download rate for accurate reporting."""
    
    def __init__(self, file, calc_interval = 0.5, time_interval = 3):
        """
        Initialize the thread with several values.
        file: path to file we'll watch for size changes
        calc_interval: frequency of calculations, in seconds.
        time_interval: the period over which we should calculate the rate,
          also in seconds.
        """
        
        self._file = file
        self._calc_interval = calc_interval
        self._time_interval = time_interval
    
    def run(self):
        """Continuously calculate the download rate over an interval."""
        
        # the global download rate storage variable, used to communicate to
        # other objects the results of our calculations
        global global_download_rate

        # calculate how many previous sizes we need to keep to hold to the
        # given time_interval, must be at least 1
        size_list_length = max(1,int(self._time_interval/self._calc_interval))
        
        # the list of previously calculated sizes, used for calculating rate
        # fill with 0 to begin with
        size_list = [0] * size_list_length

        while True:
            # push a new size onto the stack, and pop the oldest one off
            # since we initialized the stack to its max size, we don't have
            # to keep track of how many are on the stack as long as we always
            # push/pop at the same time (which we do)
            size_list.push( os.path.getsize(self._file) )
            size_list.pop()
            
            # TODO: implement locking on this variable (need 'Lock()' object)
            add = lambda x, y: x + y # function for adding up our size_list
            global_download_rate = ( reduce(add, size_list) /
                                     float(size_list_length) )
            
            # wait a bit for the next calculation
            time.sleep(_calc_interval)

class DownloaderThread(threading.Thread):
    """NOTE: we can only overwrite __init__() and run()."""
    
