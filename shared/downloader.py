import urllib2
import threading
import os
import time

class Utils(object):
    @staticmethod
    def enough_delay(prev_time, min_gap):
        """
        Returns True if the given time has passed since the given previous time.
        """
        
        return time.time() - prev_time >= min_gap

    @staticmethod
    def get_file_size(f):
        """
        Return the size in bytes of the given file.  Returns '0' if the file does
        not exist.
        """
        
        try:
            return os.path.getsize( f )
        except OSError, ose: # file not found
            return 0
    
class FileSizesEqualException(Exception):
    pass

class RemoteFile(object):
    """
    Creates a connection with a remote file via HTTP. RemoteFile reads data
    from a remote location. Ignores already-read data. Works with
    increasing remote file sizes.
    
    Use RemoteFile through Downloader.
    
    Thread-safe.
    """
    
    def __init__(self, remote_url, local_dir = "", local_file = None):
        """
        Creates a RemoteFile with a specified URL to download from.
        
        remote_url: URL of file
        local_dir: directory to save file to
        local_file: name file will be saved as
        """
        
        # used for locking the __update method and such, since multiple threads
        # will be calling this (possibly) simultaneously
        self._update_lock = threading.RLock()
        
        self._remote_url = remote_url
        self._remote_file = os.path.basename(self._remote_url)
        self._local_dir = local_dir
        
        # defaults to using same file name as remote file
        if not local_file:
            self._local_file_name = self._remote_file
        else:
            self._local_file_name = local_file
        
        self._remote_size = 0
        
        self.__update_time_gap = 5.0 # seconds
        self.__prev_time_update = -self.__update_time_gap
        
        # used for making sure our response object is in sync
        self.__response_obj = None
    
    def read(self, chunk_size = 128):
        """
        Returns data downloaded from the remote file.
        Returns the empty string if no data downloaded.
        """
        
        try:
            if self.__response() is None:
                return ''
        except FileSizesEqualException, e:
            return ''

        return self.__response().read( int(chunk_size) )

    def __response(self):
        """Makes sure the response is up to date before returning it."""
        
        self.__update()
        
        return self.__response_obj

    def __request(self):
        """Makes sure the request object is up to date before returning it."""
        
        # http://en.wikipedia.org/wiki/List_of_HTTP_headers
        request = urllib2.Request( self.get_remote_url() )
        
        # NOTE: Range header endpoints are inclusive. i.e. 0-1 gives 2 bytes
        request.add_header( "Range", "bytes=%s-" % (str(self.get_local_size())) )
        
        return request

    def __update(self):
        """
        Connect to the remote URL, get a new response object, and update
        remote file info.
        """
        
        # lock everyone out until we're done, just to be safe
        self._update_lock.acquire()
        
        if Utils.enough_delay(self.__prev_time_update, self.__update_time_gap):
            self.__prev_time_update = time.time()
            
            # try to get the data from the remote server
            try:
                self.__response_obj = urllib2.urlopen(self.__request())
            except urllib2.HTTPError, e:
                # invalid range request caused by "finished" download
                if str(e).count('416') > 0:
                    raise FileSizesEqualException("Local size == remote size")
                else:
                    raise e
            
            # dict of HTTP headers
            info = self.__response_obj.info()

            # attempt to get new remote size from headers dict
            if info.has_key("Content-Range"):
                self._remote_size = int(info.get("Content-Range").split('/')[1])
            elif info.has_key("Content-Length"):
                # we did not specify range
                self._remote_size = int(info.get("Content-Length"))

            # whatever Exception object we caught will be raise so we know how
            # to deal with it in the future.
            # 
            # Possible (not complete) list of exceptions:
            #   urllib2.HTTPError - most likely, couldn't connect
            #   urllib2.URLError - if we use improper protocol "httpdfsk://..."
            #   httplib.BadStatusLine
            #   httplib.InvalidURL
            #   ValueError
            #   IOError
        
        # let everyone back in
        self._update_lock.release()
            
    def get_progress(self):
        """
        Returns the ratio of local file size to remote file size as a float
        from 0.0 to 1.0.
        """
        
        remote_size = self.get_remote_size()
        if remote_size > 0:
            return float( self.get_local_size() ) / remote_size
        else:
            return 1.0
    
    def get_remote_size(self):
        """Returns the size of the remote file. after updating it."""
        
        self.__update()
        return self._remote_size
    
    def get_local_path(self):
        """Returns the local file path including file name."""
        
        return os.path.join(self._local_dir, self._local_file_name)
    
    def get_remote_url(self):
        """Returns the full remote URL."""
        
        return self._remote_url
    
    def get_local_size(self):
        """Returns the file size of the local file."""
        
        return Utils.get_file_size( self.get_local_path() )

class Downloader(object):
    def __init__(self, remote_url, local_dir = "", local_file = None,
                 redownload = False):
        self._thread_comm = ThreadCommunicator()
        self._remote_file = RemoteFile(remote_url, local_dir, local_file)
        self._thread = DownloadThread( self._thread_comm, self._remote_file )
        
        # start the thread. DOES NOT start the download, that's what 
        # the 'start()' method is for
        self._thread.start()
    
    def start(self):
        """Tell the download thread to begin/continue downloading."""
        
        self._thread_comm.set_downloading(True)
    
    def stop(self):
        """
        Tell the dwwnload thread to stop/pause (they're equivalent)
        downloading.
        """
        self._thread_comm.set_downloading(False)
    
    def get_download_rate(self):
        """Return the download rate in bytes per second."""
        
        return self._thread_comm.get_download_rate()
    
    def get_progress(self):
        """Returns percentage (0.0 to 1.0) done."""
        
        return self._remote_file.get_progress()
    
    def get_remote_size(self):
        """Return the size of the file on the remote server."""
        
        return self._remote_file.get_remote_size()
    
    def get_local_size(self):
        """Return the current size of the locally downloaded file."""
        
        return self._remote_file.get_local_size()
    
    def get_local_path(self):
        """Return the path (including file name) of the local file."""
        
        return self._remote_file.get_local_path()
    
    def get_remote_url(self):
        """Return the remote URL we are downloading from."""
        
        return self._remote_file.get_remote_url()

class ThreadCommunicator(object):
    """
    Used as a communication interface between Downloader and DownloadThread.
    The threads use the 'get' and 'set' methods to perform the respecive
    actions on data in this object.

    Data is shared, but protected.  There are no race conditions.
    """
    
    def __init__(self):
        # used so only one thread can modifiy member variables at a time
        # use different ones so we can modify different resources simultaneuosly
        self._downloading_lock = threading.RLock()
        self._download_rate_lock = threading.RLock()

        self._download_rate = 0.0
        self._downloading = False
    
    def get_downloading(self):
        """Return the boolean status of the downloading variable."""
        return self._downloading
    
    def set_downloading(self, new_value):
        """
        Set the boolean status of the downloading variable.
        Thread-safe.
        """
        
        with self._downloading_lock:
            self._downloading = new_value
    
    def get_download_rate(self):
        """Return the last communicated download rate."""
        
        return self._download_rate
    
    def set_download_rate(self, rate):
        """Set the download rate.  Thread-safe."""
        
        with self._download_rate_lock:
            self._download_rate = rate
    
class DownloadThread(threading.Thread):
    """
    Downloads a file from a URL to a local directory.
    
    Similar to GNU wget, DownloaderThread continues a download if the file
    already exists locally. DownloaderThread also allows the file being
    downloaded to grow in size.
    """
    
    def __init__(self, comm, remote_file, redownload = False):
        
        self._remote_file = remote_file
        
        # the communicator object we will transmit our status through
        self._thread_comm = comm
        
        self._calc_interval = 0.5 # time between rate calculations
        time_interval = 2.0 # interval over which we calculate rate
        
        # length of the queue of file sizes, must be at least 1 to prevent
        # divde-by-zero errors in rate calculation
        self._num_calcs = max(1, int(time_interval / self._calc_interval))
        
        # make sure the local file exists by 'touch'-ing it
        open(self._remote_file.get_local_path(), "ab").close()
            
        # remove the old file if 'redownload' was specified
        if redownload:
            with open(self._remote_file.get_local_path(), "wb") as killed_file:
                killed_file.write("")
        
        # we need to call Thread's init method by convention
        threading.Thread.__init__(self)
        
    def run(self):
        # the list of previously calculated rates, used for calculating
        # average rate. fill with 0s so we can just queue/dequeue as needed
        rate_list = [0.0] * self._num_calcs
        
        # the last file size we got, used to calculate change in file size
        prev_file_size = Utils.get_file_size(self._remote_file.get_local_path())
        
        # used to calculate the download rate every calc_interval seconds
        prev_time_update = -self._calc_interval
        while True:
            # FILE DOWNLOADING
            # only download if the communicator is telling us to.  this allows
            # us to stop/start the download at will
            if self._thread_comm.get_downloading():
                # open the file for binary appending
                with open(self._remote_file.get_local_path(), "ab") as f:
                    # how large a chunk we want to 'read' at a time, in bytes
                    f.write( self._remote_file.read() )
            else:
                # anti-spin precautions
                time.sleep(0.1)
                
            # FILE SIZE CALCULATION
            # only update every self._time_interval seconds
            if Utils.enough_delay(prev_time_update, self._calc_interval):
                prev_time_update = time.time()
                
                file_size = Utils.get_file_size( 
                    self._remote_file.get_local_path() )
                bytes_per_second = ( (file_size - prev_file_size) /
                                     float(self._calc_interval) )
                prev_file_size = file_size
                
                # queue the new rate into the list and dequeue the oldest one
                rate_list.append( bytes_per_second ) # queue
                rate_list.pop(0) # pop from the front, ie. dequeue
            
                # change the comm's rate to the average rate over our interval
                ave = lambda lst: float( sum(lst) ) / len(lst)
                self._thread_comm.set_download_rate( ave(rate_list) )
