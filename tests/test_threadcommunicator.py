import unittest
from downloader import *

import threading

class DownloaderTest(unittest.TestCase):

    def setUp(self):
        self.tc = DownloadThreadCommunicator()

    def tearDown(self):
        pass
    
    def test_threadcomm1(self):
        self.tc.set_download_rate(25.0)
        self.assertEqual(self.tc.get_download_rate(), 25.0)

    def test_threadcomm3(self):
        self.tc.set_downloading(True)
        self.assertEqual(self.tc.get_downloading(), True)

    def test_threadcomm4(self):
        self.tc.set_download_rate(25.0)
        self.assertEqual(self.tc.get_download_rate(), 25.0)

        self.tc.set_download_rate(5.0)
        self.assertEqual(self.tc.get_download_rate(), 5.0)
        self.assertEqual(self.tc.get_download_rate(), 5.0)

    def test_threadcomm5(self):
        self.tc.set_downloading(True)
        self.assertEqual(self.tc.get_downloading(), True)

        self.tc.set_downloading(False)
        self.assertEqual(self.tc.get_downloading(), False)
        self.assertEqual(self.tc.get_downloading(), False)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(DownloaderTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
