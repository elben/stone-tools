import unittest
from downloader import *

class DownloaderTest(unittest.TestCase):

    def setUp(self):
        #dl = Downloader()
        pass

    def tearDown(self):
        pass

    # A test case method starts with the word "test".
    def testExample1(self):
        waffle = None
        self.assertEqual(None, waffle)

    def testExample2(self):
        truths = [True, True, True]
        for i in truths:
            self.assert_(i)    # passes if argument is True

if __name__ == '__main__':
    unittest.main()

