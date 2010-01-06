import unittest
from downloader import *

class DownloaderTest(unittest.TestCase):

    def setUp(self):
        self.d1 = Downloader('http://elbenshira.com/d/testdl.txt')
        self.d2 = Downloader('http://elbenshira.com/d/testdl2.txt')
        self.d3 = Downloader('http://elbenshira.com/d/medical.txt')
        self.d4 = Downloader('http://elbenshira.com/d/empty.txt')

    def tearDown(self):
        pass

    def test_download1(self):
        self.d1.start()
        time.sleep(1)
        with open(self.d1.get_local_path()) as f:
            print f.read()

if __name__ == '__main__':
    unittest.main()
