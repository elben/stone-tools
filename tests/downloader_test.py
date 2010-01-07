import unittest
from downloader import *

class DownloaderTest(unittest.TestCase):

    def setUp(self):
        self.d1 = Downloader('http://elbenshira.com/d/testdl.txt')
        self.d2 = Downloader('http://elbenshira.com/d/testdl2.txt')
        self.d3 = Downloader('http://elbenshira.com/d/medical.txt')
        self.d4 = Downloader('http://elbenshira.com/d/empty.txt')
        self.d5 = Downloader('http://elbenshira.com/d/invalid.inv')

    def tearDown(self):
        pass

    def test_download_rate(self):
        # only tests whether it returns a float, can't think of a
        # reliable way to test whether it calculates the rate
        # correctly
        self.d2.start()
        
        rate = self.d2.get_download_rate()
        
        self.assert_( type(rate) is type(0.0) )

    def test_download1(self):
        self.d1.start()
        
        while self.d1.get_progress() < 1.0:
            time.sleep(0.1)
        
        str  = "1 this is a test download\n"
        str += "2 many lines are here\n"
        str += "3 well, mostly three\n"
        
        data = ""
        with open(self.d1.get_local_path()) as f:
            data = f.read()
            
        self.assert_(data == str)

    def test_download2(self):
        self.d2.start()
        
        while self.d2.get_progress() < 1.0:
            time.sleep(0.1)
        
        str  = "1234567890"
        
        data = ""
        with open(self.d2.get_local_path()) as f:
            data = f.read()
        
        self.assert_(data == str)

    def test_download3(self):
        self.d3.start()
        
        while self.d3.get_progress() < 1.0:
            time.sleep(0.1)
        
        data = ""
        with open(self.d3.get_local_path()) as f:
            data = f.read()
            
            self.assert_( len(data) == 2490041 )

    def test_download4(self):
        self.d4.start()
        
        while self.d4.get_progress() < 1.0:
            time.sleep(0.1)
        
        data = None
        with open(self.d4.get_local_path()) as f:
            data = f.read()
            
        self.assert_( data == "" )

    def test_download5(self):
        self.d5.start()
        
        while self.d5.get_progress() < 1.0:
            time.sleep(0.1)
        
        data = None
        with open(self.d5.get_local_path()) as f:
            data = f.read()
            
        self.assert_( data == "" )

    def test_download_resume(self):
        self.d3.start()
        time.sleep(0.1)
        self.d3.stop()
        time.sleep(0.1)
        self.d3.start()
        
        while self.d3.get_progress() < 1.0:
            time.sleep(0.1)
        
        data = ""
        with open(self.d3.get_local_path()) as f:
            data = f.read()
            
        self.assert_( len(data) == 2490041 )

    def test_download_comm(self):
        # try to freak out the thread communication
        for i in xrange(1000):
            self.d3.start()
            self.d3.stop()
            
        self.d3.start()
        
        while self.d3.get_progress() < 1.0:
            time.sleep(0.1)
        
        data = ""
        with open(self.d3.get_local_path()) as f:
            data = f.read()
            
        self.assert_( len(data) == 2490041 )

if __name__ == '__main__':
    unittest.main()

