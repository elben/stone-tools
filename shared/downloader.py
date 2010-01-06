import urllib2
import threading
import os
import time

def enough_delay(prev_time, min_gap):
    """Returns True if enough time has passed since prev_time."""
    
    return time.time() - prev_time >= min_gap

class FileSizesEqualException(Exception):
    pass

class RemoteFile(object):
    """
    Creates a connection with a remote file via HTTP. RemoteFile reads data
    from a remote location. Ignores already-read data. Works with
    increasing remote file sizes.
    
    Use RemoteFile through Downloader.
    """
    
    def __init__(self, remote_url, local_dir = "", local_file = None):
        """
        Creates a RemoteFile with a specified URL to download from.
        
        remote_url: URL of file
        local_dir: directory to save file to
        local_file: name file will be saved as
        """
        
        self._remote_url = remote_url
        self._remote_file = os.path.basename(self._remote_url)
        self._local_dir = local_dir
        
        # defaults to using same file name as remote file
        self._local_file_name = self._remote_file if not local_file else local_file
        
        self._remote_size = 0
        
        self.__update_time_gap = 5.0 # seconds
        self.__prev_time_update = -self.__update_time_gap

        self.__response_obj = None
    
    def read(self, chunk_size=128):
        """
        Returns data downloaded from remote file;
        returns None if no data downloaded.
        """

        try:
            if self.__response() is None:
                return ''
        except FileSizesEqualException, e:
            return ''

        return self.__response().read(chunk_size)

        """
        self.touch_local_file()
        if self.get_local_size() == 0:
            flags = "wb"    # overwrite binary
        else:
            flags = "ab"    # append binary

        with open(self.get_local_path(), flags) as f:
            f.write(chunk)
        """

    def __response(self):
        self.__update()
        return self.__response_obj

    def __request(self):
        # http://en.wikipedia.org/wiki/List_of_HTTP_headers
        request = urllib2.Request(self.get_remote_url())
        # NOTE: Range header endpoints are inclusive. i.e. 0-1 gives 2
        # bytes.
        request.add_header("Range", "bytes=%s-" % (str(self.get_local_size())))
        return request

    def __update(self):
        """
        Connect to the remote URL, get a new response object, and update
        remote file info.
        """
        
        if enough_delay(self.__prev_time_update, self.__update_time_gap):
            self.__prev_time_update = time.time()
            try:
                self.__response_obj = urllib2.urlopen(self.__request())
            except urllib2.HTTPError, e:
                if str(e).count('416') > 0:
                    # invalid range request caused by "finished" download
                    raise FileSizesEqualException("Local size == remote size")
                else:
                    raise e

            info = self.__response_obj.info() # dict of http headers, HTTPMessage

            # headers contains full size of remote file; pulled out here
            headers_flat = ''.join(info.headers)
            self._remote_size = int(headers_flat.split("Content-Range: ")[1]
                .split()[1].split('/')[1])

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
            
    def get_progress(self):
        """Returns percentage (0.0 to 1.0) done."""
        remote_size = self.remote_size()
        if remote_size > 0:
            return float(self.get_local_size()) / self.get_remote_size()
        else:
            return 1.0
    
    def get_local_size(self):
        """
        Return the size of the locally downloaded file.
        """
        
        self.touch_local_file()
        return os.path.getsize(self.get_local_path())
    
    def get_remote_size(self):
        """Return the size of the remote file."""
        
        self.__update()
        return self._remote_size
    
    def get_local_path(self):
        """Returns the local file path including file name."""
        
        return os.path.join(self._local_dir, self._local_file_name)
    
    def get_remote_url(self):
        """Returns the remote URL including file name."""
        
        return self._remote_url
    
    def touch_local_file(self):
        """Similar to unix 'touch'."""
        if self.local_file_exists():
            open(self.get_local_path(), 'a').close() 
        else:
            open(self.get_local_path(), 'w').close()

    def local_file_exists(self):
        return os.path.exists(self.get_local_path())

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

        self.dler = RemoteFile()
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
