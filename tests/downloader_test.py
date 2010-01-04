import unittest
from downloader import *

class DownloaderTest(unittest.TestCase):

    def setUp(self):
        self.dl = Downloader('http://elbenshira.com/d/testdl.txt',
                local_file='test.txt')

    def tearDown(self):
        pass

    # A test case method starts with the word "test".
    def testExample1(self):
        self.dl.download_chunk(chunk_size=1)
        #self.assertEqual(None, waffle)

"""
    def testExample2(self):
        truths = [True, True, True]
        for i in truths:
            self.assert_(i)    # passes if argument is True

"""

if __name__ == '__main__':
    unittest.main()

