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
        returns empty string if no data downloaded.
        """

        try:
            if self.__response() is None:
                return ''
        except FileSizesEqualException, e:
            return ''

        return self.__response().read(int(chunk_size))

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

            info = self.__response_obj.info() # dict of HTTP headers

            # attempt to get new remote size
            if info.has_key("Content-Range"):
                self._remote_size = int(info.get("Content-Range").split('/')[1])
            elif info.has_key("Content-Length"):
                # we did not specify range
                self._remote_size = int(info.get("Content-Length"))

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
        remote_size = self.get_remote_size()
        if remote_size > 0:
            return float(self.get_local_size()) / self.get_remote_size()
        else:
            return 1.0
    
    def get_local_size(self):
        """
        Return the size of the locally downloaded file.
        """
        
        open(self.get_local_path(), "ab").close()
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
    
class Downloader(object):
    def __init__(self, remote_url, local_dir, local_file, redownload = False):
        self._thread_comm = ThreadCommunicator()
        self._thread = DownloadThread( self._thread_comm, remote_url,
                                       local_dir, local_file, redownload )
        
        # start the thread.  DOES NOT start the download, that's what 
        # the 'start()' method is for
        self._thread.start()
    
    def start(self):
        self._thread_comm.set_downloading(True)
    
    def stop(self):
        self._thread_comm.set_downloading(False)
    
    def get_download_rate(self):
        return self._thread_comm.get_download_rate()
    
    def get_percent_comlete(self):
        return self._thread_comm.get_percent_comlete()

class ThreadCommunicator(object):
    """
    Used as a communication interface between Downloader and DownloadThread.
    The threads use the 'get' and 'set' methods to perform the respecive
    actions on data in this object.

    Data is shared, but protected.  There are no race conditions.
    """
    
    def __init__(self):
        # used so only one thread can modifiy member variables at a time
        self._lock = threading.RLock()

        self._progress = 0.0
        self._download_rate = 0.0
        self._downloading = False
    
    def get_downloading(self):
        return self._downloading
    
    def set_downloading(self, new_value):
        with self._lock:
            self._downloading = new_value
    
    def get_download_rate(self):
        return self._download_rate
    
    def set_download_rate(self, rate):
        with self._lock:
            self._download_rate = rate

    def get_progress(self):
        return self._progress
    
    def set_progress(self, percent):
        with self._lock:
            self._progress = percent

class DownloaderThread(threading.Thread):
    """
    Downloads a file from a URL to a local directory.
    
    Similar to GNU wget, DownloaderThread continues a download if the file
    already exists locally. DownloaderThread also allows the file being
    downloaded to grow in size.
    """
    
    def __init__(self, comm, remote_url, local_dir, local_file,
                 redownload = False):
        
        self._remote_file = RemoteFile(remote_url, local_dir, local_file)
        self._local_file = os.path.join(local_dir, local_file) # join 'em up!
        
        # the communicator object we will transmit our status through
        self._thread_comm = comm
        
        self._calc_interval = 0.5 # time between rate calculations
        time_interval = 2.0 # interval over which we calculate rate
        
        # length of the queue of file sizes, must be at least 1 to prevent
        # divde-by-zero errors in rate calculation
        self._num_calcs = max(1, int(time_interval / self._calc_interval))
        
        # make sure the local file exists by 'touch'-ing it
        open(self._local_file(), "ab").close()
            
        # remove the old file if 'redownload' was specified
        if redownload:
            with open(self._local_file, "wb") as killed_file:
                killed_file.write("")
        
        # we need to call Thread's init method by convention
        threading.Thread.__init__(self)
        
    def run(self):
        # the list of previously calculated rates, used for calculating
        # average rate. fill with 0s so we can just queue/dequeue as needed
        rate_list = [0.0] * self._num_calcs
        
        # the last file size we got, used to calculate change in file size
        prev_file_size = self._get_file_size(self._local_file)
        
        # used to calculate the download rate every calc_interval seconds
        prev_time_update = -self._calc_interval
        while True:
            # FILE DOWNLOADING
            # only download if the communicator is telling us to.  this allows
            # us to stop/start the download at will
            if self._thread_comm.get_downloading():
                # open the file for binary appending
                with open(self._local_file, "ab") as f:
                    # how large a chunk we want to 'read' at a time, in bytes
                    f.write( self._remote_file.read() )
                
                # set the progress of our file
                self._thread_comm.set_progress( 
                    self._remote_file.get_progress() )

            # FILE SIZE CALCULATION
            # only update every self._time_interval seconds
            if enough_time(prev_time_update, self._calc_interval):
                prev_time_update = time.time()
                
                file_size = self.file_size()
                bytes_per_second = ( (file_size - prev_file_size) /
                                     float(self._calc_interval) )
                prev_file_size = file_size
                
                # queue the new rate into the list and dequeue the oldest one
                rate_list.append( bytes_per_second ) # queue
                rate_list.pop(0) # pop from the front, ie. dequeue
            
                # change the comm's rate to the average rate over our interval
                self._comm.set_download_rate( self._average_list(rate_list) )
            
    def _average_list(self, list):
        """Return the average of a list of numbers."""
        
        return float(sum(list)) / len(list)
    
    def _get_file_size(self, f):
        """Attempt to get the file size of the given file, else return -1."""
        
        try:
            return os.path.getsize(f)
        except OSError, ose: # file not found
            print ose
            print "File not found:", "'" + str(f) + "'"
            
            return -1
