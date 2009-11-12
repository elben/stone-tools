import urllib2
import threading
import os
import time

# global download rate variable in bytes/second, updated by a thread
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
        
        # if file already exists, get size and start download there
        if os.path.exists(self.get_local_path()) and not force_redownload:
            # TODO: don't need to save _local_size here since we can call
            # get_local_size() later when we need it
            self._local_size = os.path.getsize( self.get_local_path() )
        else:
            self._local_size = 0
        
        self._remote_size = 0
        
        # Request object represents file and the range we want to dl
        # TODO: header might be Request-Range. Read up on Apache stuff.
        # TODO: move this into the run() method or download()
        self.request = urllib2.Request(self.remote(), headers = {"Range" :
            "bytes=%s-" % (str(self.get_local_size())) } )
        
        # rate to limit our download to, -1 == do not cap rate
        self.rate_limit = rate_limit
        
        self._update()
        self.__prev_time_update = time.time()
        self.__update_time_gap = 5 # seconds
    
    def run(self):
        pass
    
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
                self._remote_size = int( info["content-length"] )
            except Exception, e:
                # raise whatever Exception object we caught, so we
                # know how to deal with it in the future
                print "From '_update()' in Downloader:"
                raise e
            
    def get_download_rate(self):
        """Returns the current download rate in KB/s"""
        
        # makes sure that we are getting the global variable
        global global_download_rate
        
        return global_download_rate
    
    def get_progress(self):
        """Returns percentage (0.0 to 1.0) done."""
        
        if self._local_size < self._remote_size:
            return float(self.get_local_size()) / self.get_remote_size()
        else:
            return 1.0
    
    def get_local_size(self):
        """Return the size of the locally downloaded file."""
        
        # return the size if possible, else return 0
        try:
            return os.path.getsize(self.get_local_path())
        except OSError, e:
            print e
            return 0
    
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
    
    def __init__(self, file, calc_interval = 0.5, time_interval = 2):
        """
        Initialize the thread with several values.
        
        file: path to file we'll watch for size changes
        calc_interval: frequency of calculations, in seconds.
        time_interval: the period over which we should calculate the rate,
          also in seconds.
        """
        
        self._file = file
        self._calc_interval = calc_interval
        
        # length of the queue of file sizes, must be at least 1
        self._num_calcs = max(1, int(time_interval / calc_interval))
    
    def run(self):
        """Continuously calculate the download rate over an interval."""
        
        # the global download rate storage variable, used to communicate to
        # other objects the results of our calculations
        global global_download_rate

        # the list of previously calculated rates, used for calculating
        # average rate. fill with 0s so we can just append/pop as needed
        rate_list = [0] * self._num_calcs

        # creates a Lock() object, used to keep from breaking variable access
        # while using threading
        lock = threading.Lock()
        
        # the last file size we got, used to calculate change in file size
        prev_file_size = self.get_file_size()
        while True:
            # queue a new rate into the list and dequeue the oldest one
            file_size = self.get_file_size()
            bytes_per_second = ( (file_size - prev_file_size) /
                                 float(self._calc_interval) )
            prev_file_size = file_size
            
            rate_list.append( bytes_per_second ) # queue
            rate_list.pop(0) # pop from the front, ie. dequeue
            
            # change the global rate to the average rate over our interval
            # and do it while locked, to boot
            with lock:
                global_download_rate = self.average(rate_list)
            
            # wait a bit for the next calculation
            time.sleep(self._calc_interval)
        
    def average(self, list):
        """Return the avarage of a list of numbers."""
        
        return float(reduce(lambda x, y: x + y, list)) / len(list)
    
    def get_file_size(self):
        """Attempt to get the file size of the given file, else return 0."""
        try:
            return os.path.getsize(self._file)
        except OSError, ose: # file not found
            print ose
            print "File not found: '" + str(self._file) + "'"
            return 0

class DownloaderThread(threading.Thread):
    """NOTE: we can only overwrite __init__() and run()."""
    
