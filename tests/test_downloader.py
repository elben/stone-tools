import unittest
from downloader import *
 
class DownloaderTest(unittest.TestCase):
 
    def setUp(self):
        # make sure these files don't stay in this directory
        delete_these = [ 'testdl.txt', 'testdl2.txt', 'medical.txt', 
                         'empty.txt', 'nonexistent.txt' ]
        for f in delete_these:
            try:
                os.remove(f)
            except:
                pass
        
        self.d1 = Downloader('http://elbenshira.com/d/testdl.txt')
        self.d2 = Downloader('http://elbenshira.com/d/testdl2.txt')
        self.d3 = Downloader('http://elbenshira.com/d/medical.txt')
        self.d4 = Downloader('http://elbenshira.com/d/empty.txt')
        self.d5 = Downloader('http://elbenshira.com/d/nonexistent.txt')
 
    def tearDown(self):
        # make sure these files don't stay in this directory
        delete_these = [ 'testdl.txt', 'testdl2.txt', 'medical.txt', 
                         'empty.txt', 'medicallink' ]
        for f in delete_these:
            try:
                os.remove(f)
            except:
                pass
        
        # kill all the Downloaders and their threads
        del self.d1
        del self.d2
        del self.d3
        del self.d4
        del self.d5
        
    def test_download1(self):
        self.d1.start()
        
        while not self.d1.is_complete():
            time.sleep(0.01)
        
        self.d1.stop()
            
        str  = "1 this is a test download\n"
        str += "2 many lines are here\n"
        str += "3 well, mostly three\n"
        
        data = ""
        with open(self.d1.get_local_path()) as f:
            data = f.read()
        
        self.assert_(data == str)
 
    def test_download2(self):
        self.d2.start()
        
        while not self.d2.is_complete():
            time.sleep(0.01)
        
        self.d2.stop()
        
        str = "1234567890"
        
        data = ""
        with open(self.d2.get_local_path()) as f:
            data = f.read()
            
        self.assert_(data == str)
 
    def test_download3(self):
        self.d3.start()
        
        while not self.d3.is_complete():
            time.sleep(0.01)
        
        self.d3.stop()
            
        data = ""
        with open(self.d3.get_local_path()) as f:
            data = f.read()
            
            self.assert_(len(data) == 2490041)
    
    def test_download4(self):
        self.d4.start()
        
        while not self.d4.is_complete():
            time.sleep(0.01)
        
        self.d4.stop()
            
        data = None # something we're not asserting for
        with open(self.d4.get_local_path()) as f:
            data = f.read()
        
        self.assert_(data == "")
    
    def test_download5(self):
        self.d5.start()
        
        while not self.d5.is_complete():
            time.sleep(0.01)
        
        self.d5.stop()
            
        data = None # something that's not what we're asserting for
        with open(self.d5.get_local_path()) as f:
            data = f.read()
        
        self.assert_(data == "")
    
    def test_downloader_thread_kill(self):
        pass
    
    def test_downloader_thread_no_kill(self):
        pass
    
    def test_download_rate(self):
        # only tests whether it returns a float, can't think of a
        # reliable way to test whether it calculates the rate
        # correctly
        
        self.d3.start()
        
        # wait for the download to get going so we can check it
        while self.d3.get_progress() == 0.0:
            time.sleep(0.01)
        
        rate = self.d3.get_download_rate()
        
        self.assert_( type(rate) is type(0.0) and rate > 0.0)
        
        self.d3.stop()
 
    def test_download_resume(self):
        self.d3.start()
        time.sleep(0.01)
        self.d3.stop()
        time.sleep(0.01)
        self.d3.start()
        
        while not self.d3.is_complete():
            time.sleep(0.01)
        
        self.d3.stop()
            
        data = ""
        with open(self.d3.get_local_path()) as f:
            data = f.read()
            
        self.assert_(len(data) == 2490041)
 
    def test_download_comm_no_kill(self):
        # try to freak out the thread communication
        for i in xrange(100):
            self.d3.start()
            self.d3.stop(kill = False)
            
        self.d3.start()
        
        while not self.d3.is_complete():
            time.sleep(0.01)
        
        self.d3.stop()
            
        data = ""
        with open(self.d3.get_local_path()) as f:
            data = f.read()
            
        self.assert_(len(data) == 2490041)
 
    def test_download_comm_with_kill(self):
        # try to freak out the thread communication, but making threads takes
        # bit of time, we don't do as many
        for i in xrange(10):
            self.d3.start()
            self.d3.stop(kill = True)
            
        self.d3.start()
        
        while not self.d3.is_complete():
            time.sleep(0.01)
        
        self.d3.stop()
            
        data = ""
        with open(self.d3.get_local_path()) as f:
            data = f.read()
        
        self.assert_( len(data) == 2490041 )
 
    def test_remote_size(self):
        self.assert_( self.d3.get_remote_size() == 2490041 )
        
    def test_remote_size_no_remote_file(self):
        self.assert_( self.d5.get_remote_size() == -1 )
    
    def test_local_size_no_local_file(self):
        self.assert_(self.d3.get_local_size() == 0)
    
    def test_remote_url(self):
        self.assert_( self.d1.get_remote_url() == 
                      'http://elbenshira.com/d/testdl.txt' )
    
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(DownloaderTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
