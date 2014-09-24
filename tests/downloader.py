import urllib2
import threading
import os
import time
from types import *
 
# class DownloadCompleteException(Exception):
#     pass
 
# class FileNotFoundException(Exception):
#     pass

# class RemoteFile(object):
#     """
#     Creates a connection with a remote file via HTTP. RemoteFile reads data
#     from a remote location. Ignores already-read data. Works with
#     increasing remote file sizes.
    
#     Use RemoteFile through Downloader. Thread-safe.
#     """
    
#     def __init__(self, remote_url, local_dir = "", local_file = None):
#         """
#         Creates a RemoteFile with a specified URL to download from.
        
#         remote_url: URL of file
#         local_dir: directory to save file to
#         local_file: name file will be saved as
#         """
        
#         # used for locking the __update method and such, since multiple
#         # threads will be calling this (possibly) simultaneously
#         self._update_lock = threading.RLock()
        
#         self._remote_url = remote_url
#         self._remote_file = os.path.basename(self._remote_url)
#         self._local_dir = local_dir
        
#         # defaults to using same file name as remote file
#         if not local_file:
#             self._local_file_name = self._remote_file
#         else:
#             self._local_file_name = local_file
        
#         self._remote_size = 0
        
#         self._update_interval = 5.0 # seconds
#         self._prev_update_time = -self._update_interval
        
#         # used for making sure our response object is in sync
#         self._response_obj = None
    
#     def read(self, chunk_size = 128):
#         """
#         Returns data downloaded from the remote file.
#         Returns the empty string if no data downloaded.
#         """
        
#         try:
#             if self._response() is None:
#                 return ''
#         except DownloadCompleteException, e:
#             return ''
#         except FileNotFoundException, e:
#             # throw it up the chain of command
#             raise e
#         except Exception, e:
#             # make it obvious so we can deal with whatever this is :(
#             for x in xrange(10):
#                 print "!"            
            
#             print e
 
#             # find the rest we will have missed
#             raise e
        
#         try:
#             return self._response().read( int(chunk_size) )
#         except:
#             # we already dealt with any errors we needed to
#             return ''
 
#     def _response(self):
#         """Makes sure the response is up to date before returning it."""
        
#         try:
#             self._update()
#             return self._response_obj
#         except DownloadCompleteException, e:
#             # don't care if the files sizes are the same, return the response
#             return self._response_obj
#         except FileNotFoundException, e:
#             raise e
#         except Exception, e:
#             # make it obvious so we can deal with whatever this is :(
#             for x in xrange(10):
#                 print "!"
            
#             raise e
 
#     def _request(self):
#         """
#         Makes sure the request object is up to date before returning it.
#         """
        
#         # http://en.wikipedia.org/wiki/List_of_HTTP_headers
#         request = urllib2.Request( self.get_remote_url() )
        
#         # NOTE: Range header endpoints are inclusive. i.e. 0-1 gives 2 bytes
#         request.add_header( "Range", 
#                             "bytes=%s-" % ( str(self.get_local_size()) ) )
        
#         return request
 
#     def _update(self):
#         """
#         Connect to the remote URL, get a new response object, and update
#         remote file info.
#         """
        
#         # lock everyone out until we're done, just to be safe
#         with self._update_lock:
#             if self._enough_delay( self._prev_update_time,
#                                    self._update_interval ):
#                 self._prev_update_time = time.time()
                
#                 # try to get the data from the remote server
#                 try:
#                     self._response_obj = urllib2.urlopen(self._request())
#                 except urllib2.HTTPError, e:
#                     # invalid range request caused by "finished" download
#                     if str(e).count('416') > 0:
#                         raise DownloadCompleteException( 
#                             "Local size == remote size" )
#                     elif str(e).count('404') > 0:
#                         raise FileNotFoundException( 
#                             "File not found on server: '" + 
#                             str( self.get_remote_url() ) + "'")
#                     else:
#                         raise e
            
#                 # dict of HTTP headers
#                 info = self._response_obj.info()
    
#                 # attempt to get new remote size from headers dict
#                 if info.has_key("Content-Range"):
#                     rsize = int(info.get("Content-Range").split('/')[1])
#                     self._remote_size = rsize
#                 elif info.has_key("Content-Length"):
#                     # we did not specify range
#                     self._remote_size = int( info.get("Content-Length") )
    
#                 # whatever Exception object we caught will be raise so we 
#                 # how to deal with it in the future.
#                 # 
#                 # Possible (not complete) list of exceptions:
#                 #   urllib2.HTTPError - most likely, couldn't connect
#                 #   urllib2.URLError - if we use improper protocol "dfsk://..."
#                 #   httplib.BadStatusLine
#                 #   httplib.InvalidURL
#                 #   ValueError
#                 #   IOError
    
#     def get_progress(self):
#         """
#         Returns the ratio of local file size to remote file size as a float
#         from 0.0 to 1.0.
#         """
        
#         # prevent divide by zero errors
#         if self._remote_size > 0:
#             return float( self.get_local_size() ) / self._remote_size
#         else:
#             # return 1.0 since returning 0.0 could lead the user to believe
#             # that nothing has happened yet or the request has stalled
#             return 1.0
    
#     def is_complete(self):
#         """
#         An easy way to check whether the download is complete or not.
#         """
        
#         try:
#             return self.get_local_size() >= self._remote_size
#         except:
#             # any errors would obviously mean nothing has happened yet
#             return False
    
#     def get_remote_size(self):
#         """Returns the size of the remote file. after updating it."""
        
#         try:
#             self._update()
#         except DownloadCompleteException, e:
#             # at least return the last size we found
#             return self._remote_size
#         except FileNotFoundException, e:
#             raise e
#         except Exception, e:
#             # make it obvious so we can deal with whatever this is :(
#             for x in xrange(10):
#                 print "!"
            
#             print e
            
#             raise e
    
#     def get_local_path(self):
#         """Returns the local file path including file name."""
        
#         return os.path.join(self._local_dir, self._local_file_name)
    
#     def get_remote_url(self):
#         """Returns the full remote URL."""
        
#         return self._remote_url
    
#     def get_local_size(self):
#         """Returns the file size of the local file."""
        
#         try:
#             return os.path.getsize( self.get_local_path() )
#         except OSError, ose: # file not found
#             return 0
    
#     def _enough_delay(self, prev_time, min_gap):
#         """
#         Returns True if the given time has passed since the given
#         previous time.
#         """
        
#         return time.time() - prev_time >= min_gap

class RemoteFile(object):
    def __init__(self, url, position = 0, timeout = None):
        """
        'Opens' a server's remote file, ie. initiates a connection and 
        prepares for reading it.  Can optionally specify a byte position to 
        open the file at, defaulting to 0.  Timeout tells how long (maximum)
        in seconds to wait for the server to respond, otherwise it defaults to
        the global timeout settings.
        
        If we fail to open the file (make a connection), an IOError is raised.
        If the url is invalid, a ValueError is raised.
        """
        

        # programmer error handling
        assert type(url) is StringType
        assert type(position) is IntType or type(position) is LongType
        assert ( type(timeout) is IntType or type(timeout) is LongType or 
                 type(timeout) is NoneType )
        
        # user error handling
        if position < 0:
            raise ValueError("position must be greater than or equal to 0: " +
                             "position = " + str(position) )
        
        if timeout is not None and timeout <= 0:
            raise ValueError( "timeout must be greater than 0: timeout = " + 
                              str(timeout) )
        
        # 
        # real '__init__()' code starts here
        # 
        
        # TODO: catch specific errors and translate them into file-like errors;
        # do so for the entire '__init__()' method
        
        self._url = url
        
        # build the request object we will use in 'urlopen()'
        r = urllib2.Request(url)
        
        # add a range header if an initial position was specified
        if position != 0:
            r.add_header("Range", "bytes=" + str(position) + "-")

        # make sure that range was good and everything else is ok
        try:
            self._response = urllib2.urlopen(r)
        except urllib2.HTTPError, e:
            raise IOError( str(e) )
        
        # populate initial variables
        response_info = self._response.info()
        
        # file-like public variables we implement
        self.closed = False # we open on creation and close on del-etion
        self.mode = "rb" # the file mode, binary reading only!
        self.newline = None # None since we're binary
        self.softspace = False # if a space needs to be printed before values
        
        # we populate this one as the filename on the server
        self.name = url.rstrip("/").split("/")[-1]
    
    def __del__(self):
        """
        Close this RemoteFile on deletion so it can't be read from anymore.
        """
        
        self.close()
    
    def close(self):
        """
        Close this RemoteFile, following Python's file-like implementation.
        Has no effect other than making methods like 'read' and fail with a 
        ValueError.
        """
        
        self.closed = True
        
    def read(self, num_bytes = None):
        """
        Read (ie. download) some number of bytes from the RemoteFile.  If a 
        number of bytes greater than the size of the file has been specified 
        or completely omitted, simply read the entire file.
        """
        
        assert ( type(num_bytes) is IntType or type(num_bytes) is LongType or
                 type(num_bytes) is NoneType )
        
        if self.closed:
            raise ValueError("Reading a closed RemoteFile is not permitted.")
        
        if num_bytes is not None and num_bytes <= 0:
            raise ValueError( "num_bytes must be greater than 0: " + 
                              "num_bytes = " + str(num_bytes) )
        
        # TODO: catch errors and translate them into file-like errors
        if num_bytes is not None:
            return self._resonse.read(num_bytes)
        else:
            return self._resonse.read()
    
    def next(self):
        """
        An iterator of sorts.  Reads (ie. downloads) and returns the next byte 
        from the server's file, in order.
        """
        
        if self.closed:
            raise ValueError("Reading a closed RemoteFile is not permitted.")
        
        # TODO: catch errors and translate them into file-like errors
        return self._response.read(1)
 
class Downloader(object):
    def __init__(self, remote_url, local_dir = "", local_file = None,
                 redownload = False):
        self._thread_comm = DownloadThreadCommunicator()
        self._remote_file = RemoteFile(remote_url, local_dir, local_file)
        self._thread = DownloadThread(self._thread_comm, self._remote_file)
        
        # start the thread. DOES NOT start the download, that's what 
        # the 'start()' method is for
        self._thread.start()
    
    def __del__(self):
        """
        Kill and remove the thread we spawned as soon as this Downloader
        is garbage collected or deleted.
        """
        
        #print "Downloader: __del__ method was called"
        self.stop(kill = True)
        #print "Downloader: __del__ method finished"
    
    def start(self):
        """
        Tell the download thread to begin/continue downloading.
        Will recreate the thread if it has been killed by 'stop()'.
        """
        
        #print "Downloader: start method called"
 
        # (re)create the thread if it was killed
        if not self._thread.is_alive():
            self._thread_comm = DownloadThreadCommunicator()
            self._thread = DownloadThread(self._thread_comm, self._remote_file)
            self._thread.start()
        
        self._thread_comm.set_downloading(True)
    
    def stop(self, kill = True):
        """
        Pause or kill the download thread, depending on the argument.
        A subsequent call to 'start()' will recreate it if necessary.
        Has no effect if the download is already stopped.
        """
        
        #print "Downloader: stop method called"
 
        # don't bother doing any work if the thread is already dead
        if not self._thread.is_alive():
            return
        
        # turn off downloading so there is no unexpected behavior
        self._thread_comm.set_downloading(False)
        
        # kill the thread if specified
        if kill:
            #print "Downloader: calling set_kill on DownloadThreadCommunicator"
            self._thread_comm.set_kill(True)
            
            # block until the thread is dead
            #print "Downloader: waiting for DownloadThread to die"
            while self._thread.is_alive():
                time.sleep(0.001)
            
            #print "Downloader: calling set_kill on DownloadThreadCommunicator"
            self._thread_comm.set_kill(False)
    
    def is_complete(self):
        """
        An easy way to check whether the download is complete or not.  Use 
        this instead of 'get_progress()' to check whether the download is 
        complete or not.  See 'get_progress()' for more details.
        """
        
        return self._remote_file.is_complete()
    
    def get_download_rate(self):
        """Return the download rate in bytes per second."""
        
        return self._thread_comm.get_download_rate()
    
    def get_progress(self):
        """
        Returns percentage (0.0 to 1.0) done.  
        
        DO NOT use this to check whether a download is complete, use 
        'is_complete() instead.
        
        If you use code such as:
        
          | d = Downloader(...)
          | d.start()
          | 
          | while r.get_progress() < 1.0:
          |   time.sleep(1)
          | 
          | d.stop()
        
        it can lead to problems when the remote file size is 0.  If it really
        is 0 or that file doesn't exist on the server, the RemoteFile object's
        remote size is 0!  In that case, the above code would fall through
        immediately without allowing time for the thread to make a connection
        and download the file.
        """
        
        return self._remote_file.get_progress()
    
    def get_remote_size(self):
        """
        Return the size of the file on the remote server, or -1 if it doesn't
        exist.
        """
        
        try:
            return self._remote_file.get_remote_size()
        except FileNotFoundException, e:
            return -1
    
    def get_local_size(self):
        """Return the current size of the locally downloaded file."""
        
        return self._remote_file.get_local_size()
    
    def get_local_path(self):
        """Return the path (including file name) of the local file."""
        
        return self._remote_file.get_local_path()
    
    def get_remote_url(self):
        """Return the remote URL we are downloading from."""
        
        return self._remote_file.get_remote_url()
 
class DownloadThreadCommunicator(object):
    """
    Used as a communication interface between Downloader and
    DownloadThread. The threads use the 'get' and 'set' methods to
    perform the respecive actions on data in this object.
 
    Data is shared, but protected.  There are no race conditions.
    """
    
    def __init__(self):
        # used so only one thread can modifiy member variables at a time
        # use different ones so we can modify different resources simultaneuosly
        self._downloading_lock = threading.RLock()
        self._download_rate_lock = threading.RLock()
        self._kill_lock = threading.RLock()
 
        self._download_rate = 0.0
        self._downloading = False
        self._kill = False
    
    def set_kill(self, new_value):
        """Tell the download thread to terminate."""
        
        #print "DownloadThreadCommunicator: setting kill to", new_value
        with self._kill_lock:
            self._kill = new_value
        
    def get_kill(self):
        """
        Return the status of the kill variable. Thread-safe.
        """
        
        return self._kill
        
    def get_downloading(self):
        """Return the boolean status of the downloading variable."""
        
        return self._downloading
    
    def set_downloading(self, new_value):
        """
        Set the boolean status of the downloading variable. Thread-safe.
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
        # we need to call Thread's init method FIRST by convention
        threading.Thread.__init__(self)
        
        # the base RemoteFile object that does the actual downloading
        self._remote_file = remote_file
        
        # the communicator object we will transmit our status through
        self._thread_comm = comm
 
        # variables for download rate calculation
        self._calc_interval = 0.5 # time between rate calculations
        time_interval = 2.0 # interval over which we calculate rate
        self._prev_time_update = -self._calc_interval
        self._prev_file_size = self._remote_file.get_local_size()
        # the list of previously calculated rates, used for calculating
        # average rate. fill with 0.0s so we can just queue/dequeue as needed.
        # we multiply by length of the queue of file sizes, which must be at 
        # least 1 to prevent divide-by-zero errors in rate calculation.
        self._rate_list = [0.0]*max(1, int(time_interval/self._calc_interval))
 
        # make sure the local file exists by 'touch'-ing it
        open(self._remote_file.get_local_path(), "ab").close()
            
        # overwrite the old file if 'redownload' was specified
        if redownload:
            with open(self._remote_file.get_local_path(), "wb") as killed:
                killed.write("")
        
    def run(self):
        # continue to run while we haven't been told to die
        while not self._thread_comm.get_kill():
            # only download if the communicator is telling us to. this allows
            # us to pause/unpause the download at will
            if self._thread_comm.get_downloading():
                # open the file for binary appending
                with open(self._remote_file.get_local_path(), "ab") as f:
                    try:
                        f.write( self._remote_file.read() )
                    except DownloadCompleteException, e:
                        # we're 'finished' downloading, at least for now
                        pass
                    except FileNotFoundException, e:
                        # we failed to find a file, so we're done
                        return
            else:
                # download rate should be 0.0 if we are paused
                if self._thread_comm.get_download_rate() != 0.0:
                    self._thread_comm.set_download_rate(0.0)
                
                # anti-spin precautions
                time.sleep(0.01)
 
            # update the download rate
            self._calculate_download_rate()
        else:
            # remove any empty files we might have left behind
            if self._remote_file.get_local_size() == 0:
                try:
                    os.path.remove(self._remote_file.get_local_path())
                except:
                    # ignore errors, we either removed it or we didn't
                    pass
            
            # die by exiting this 'run()' method
            return
 
    def _calculate_download_rate(self):
        """
        Return the current rate of the download.  Will only calculate as
        frequently as has been specified.
        """
        
        if self._enough_delay(self._prev_time_update, self._calc_interval):
            self._prev_time_update = time.time()
            
            file_size = self._remote_file.get_local_size()
            bytes_per_second = ( (file_size - self._prev_file_size) /
                                 float(self._calc_interval) )
            self._prev_file_size = file_size
            
            # queue the new rate into the list and dequeue the oldest one
            self._rate_list.append( bytes_per_second ) # queue
            self._rate_list.pop(0) # pop from the front, ie. dequeue
            
            # change the comm's rate to the average rate over our interval
            ave = lambda lst: float( sum(lst) ) / len(lst)
            self._thread_comm.set_download_rate( ave(self._rate_list) )
 
    def _enough_delay(self, prev_time, min_gap):
        """
        Returns True if the given time has passed since the given previous
        time.
        """
        
        return time.time() - prev_time >= min_gap
