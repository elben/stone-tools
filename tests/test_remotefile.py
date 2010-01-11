import unittest
from downloader import RemoteFile

class TestSequence(unittest.TestCase):
    # base server directories we'll download from
    def setUp(self):
        self.elben = "http://elbenshira.com/d"
        
        # files on the servers we'll try to connect to
        self.url_dict = { "testdl.txt"  : self.elben + "/testdl.txt",
                          "testdl2.txt" : self.elben + "/testdl2.txt",
                          "medical.txt" : self.elben + "/medical.txt",
                          "empty.txt"   : self.elben + "/empty.txt",
                          
                          "invalidfile" : self.elben + "/dne_1A2B3C.invalid" }
        
        
    # these tests check to make sure intializing the RemoteFile works correctly
    def test_init_invalid_url_type(self):
        try:
            r = RemoteFile( True )
        except AssertionError, e:
            pass
        else:
            self.assert_(False)

    def test_init_invalid_url_text(self):
        try:
            r = RemoteFile( "htsdjlfh?\\sdj4888sdkfjhsa.sdjaskdhkjh%%$;" )
        except ValueError, e:
            pass
        else:
            self.assert_(False)

    def test_init_nonexistent_url(self):
        try:
            r = RemoteFile( "http://djflsakfjei34sdfajh.com/n0tthere.ntr" )
        except IOError, e:
            pass
        else:
            self.assert_(False)

    def test_init_correct_url(self):
        r = RemoteFile( self.url_dict["testdl.txt"] )

    def test_init_invalid_position_type(self):
        try:
            r = RemoteFile( self.url_dict["medical.txt"], position = 3.14 )
        except AssertionError, e:
            pass
        else:
            self.assert_(False)

    def test_init_invalid_position_value(self):
        try:
            r = RemoteFile( self.url_dict["medical.txt"], position = -1 )
        except ValueError, e:
            pass
        else:
            self.assert_(False)

    def test_init_incorrect_position(self):
        try:
            r = RemoteFile( self.url_dict["medical.txt"], 
                            position = 3000000 ) # actual length is 2490041
        except IOError, e:
            pass
        else:
            self.assert_(False)
        
    def test_init_correct_position(self):
        r = RemoteFile( self.url_dict["medical.txt"], position = 10000 )

    def test_init_invalid_timeout_type(self):
        try:
            r = RemoteFile(self.url_dict["empty.txt"], timeout = 10.0)
        except AssertionError, e:
            pass
        else:
            self.assert_(False)
    
    def test_init_invalid_timeout_value1(self):
        try:
            r = RemoteFile(self.url_dict["empty.txt"], timeout = 0)
        except ValueError, e:
            pass
        else:
            self.assert_(False)
    
    def test_init_invalid_timeout_value2(self):
        try:
            r = RemoteFile(self.url_dict["empty.txt"], timeout = -1)
        except ValueError, e:
            pass
        else:
            self.assert_(False)
    
    def test_init_correct_timeout(self):
        r = RemoteFile(self.url_dict["testdl.txt"], timeout = 10)
    
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSequence)
    unittest.TextTestRunner(verbosity=2).run(suite)
