import urllib2
import threading
import os
import time

def enough_delay(prev_time, min_gap):
    """Returns True if enough time has passed since prev_time."""
    
    return time.time() - prev_time >= min_gap

class Downloader(object):
    """
    Downloads a file from a URL to a local directory.
    
    Similar to GNU wget, Downloader continues a download if the file already
    exists locally. Downloader also allows the file being downloaded to grow
    in size.

    Use Downloader through DownloaderThread.
    """
    
    def __init__(self, remote_url,
            local_dir = "", local_file = None,
            reset_download = False, rate_limit = -1):
        """
        Creates a Downloader with a specified URL to download from.
        
        remote_url: URL of file
        local_dir: directory to save file to
        local_file: name file will be saved as
        reset_download: force to reset a download; will not continue
          previous download
        rate_limit: limit download at this rate

        """
        
        # TODO: implement reset_download
        # TODO: implement rate_limit

        self._remote_url = remote_url
        self._remote_file = os.path.basename(self._remote_url)
        self._local_dir = local_dir
        
        # defaults to using same file name as remote file
        self._local_file_name = self._remote_file if not local_file else local_file
        
        self._remote_size = 0
        self._rate_limit = rate_limit        # -1 means 'do not cap rate'
        
        self.__update_time_gap = 5.0 # seconds
        self.__prev_time_update = -self.__update_time_gap

        self.__response_obj = None
        #self.__update()

        if not os.path.exists(self.local_path()):
            open(self.local_path(), 'w').close() 
    
    def download_chunk(self, chunk_size=100):
        if self.__response() is None: return
        chunk = self.__response().read(chunk_size)
        if not chunk:
            raise Exception("no chunk gotten!")
            return

        # TODO: we need reset_download logic here, but don't implement
        # until we know how reset_download flag will work
        if self.local_size() == 0:
            flags = "wb"    # overwrite binary
        else:
            flags = "ab"    # append binary

        with open(self.local_path(), flags) as f:
            f.write(chunk)
    
    def __response(self):
        self.__update()
        return self.__response_obj

    def __request(self):
        # http://en.wikipedia.org/wiki/List_of_HTTP_headers
        request = urllib2.Request(self.remote_url())
        request.add_header("Range", "bytes=%s-" % (str(self.local_size())))
        return request

    def __update(self):
        """
        Connect to the remote URL, get a new response object, and update
        remote file info.
        """
        
        if enough_delay(self.__prev_time_update, self.__update_time_gap):
            self.__prev_time_update = time.time()
            #try:
            self.__response_obj = urllib2.urlopen(self.__request())
            info = self.__response_obj.info() # dict of http headers, HTTPMessage
            self._remote_size = int( info["content-length"] )
            #except Exception, e:
                # raise whatever Exception object we caught, so we
                # know how to deal with it in the future
                # Possible (not complete) list of exceptions:
                #   urllib2.HTTPError - most likely, couldn't connect
                #   urllib2.URLError - if we use improper protocol "httpdfsk://..."
                #   httplib.BadStatusLine
                #   httplib.InvalidURL
                #   ValueError
                #   IOError
                # print "Exception thrown from __update()" #in ", self.__name__
            #    raise e
            
    def finished(self):
        """Returns True if download is finished."""
        return self.remote_size() == self.local_size()

    def progress(self):
        """Returns percentage (0.0 to 1.0) done."""
        remote_size = self.remote_size()
        if remote_size > 0:
            return float(self.local_size()) / self.remote_size()
        else:
            return 1.0
    
    def local_size(self):
        """
        Return the size of the locally downloaded file.
        Returns -1 if size check failed.
        """
        
        try:
            return os.path.getsize(self.local_path())
        except OSError, e:
            #print "Error thrown from local_size() in", self.__name__
            print e
            return -1
    
    def remote_size(self):
        """Return the size of the remote file."""
        
        self.__update()
        return self._remote_size
    
    def local_path(self):
        """Returns the local file path including file name."""
        
        return os.path.join(self._local_dir, self._local_file_name)
    
    def remote_url(self):
        """Returns the remote URL including file name."""
        
        return self._remote_url
    
class DownloaderThread(threading.Thread):
    """
    Downloads a file from a URL to a local directory.
    
    Similar to GNU wget, DownloaderThread continues a download if the file
    already exists locally. DownloaderThread also allows the file being
    downloaded to grow in size.
    """
    
    def __init__(self, file_url, calc_interval = 0.5, time_interval = 2,
            reset = False, paused = True):
        """
        Initialize the thread.
        
        file_url: url to file we want to download
        calc_interval: frequency of calculations, in seconds.
        time_interval: the period over which we should calculate the rate,
          also in seconds.
        """

        self.dler = Downloader()
        self._file = file
        self._calc_interval = calc_interval
        self._download_rate = 0.0

        self._reset = reset     # if True, ignore existing downloaded file
        self._paused = pause
        
        # length of the queue of file sizes, must be at least 1 to prevent
        # divde-by-zero errors in rate calculation
        self._num_calcs = max(1, int(time_interval / calc_interval))
    
        # we need to call Thread's init method by convention
        threading.Thread.__init__(self)


        
    def run(self):
        # the list of previously calculated rates, used for calculating
        # average rate. fill with 0s so we can just queue/dequeue as needed
        rate_list = [0.0] * self._num_calcs
        
        # the last file size we got, used to calculate change in file size
        prev_file_size = self.file_size()
        while True:
            # queue a new rate into the list and dequeue the oldest one
            file_size = self.file_size()
            bytes_per_second = ( (file_size - prev_file_size) /
                                 float(self._calc_interval) )
            prev_file_size = file_size
            
            rate_list.append( bytes_per_second ) # queue
            rate_list.pop(0) # pop from the front, ie. dequeue
            
            # change the global rate to the average rate over our interval
            self._download_rate = self._average_list(rate_list)
            
            # wait a bit for the next calculation
            # TODO: needs to change on implementing actual downloading
            time.sleep(self._calc_interval)
        
    def _average_list(self, list):
        """Return the average of a list of numbers."""
        
        return float(sum(list)) / len(list)
    
    def file_size(self):
        """Attempt to get the file size of the given file, else return -1."""
        
        try:
            return os.path.getsize(self._file)
        except OSError, ose: # file not found
            #print "Error throw from file_size() in", self.__name__
            print ose
            print "File not found:", "'" + str(self._file) + "'"
            
            return -1
