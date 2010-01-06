import unittest
from downloader import *

class DownloaderTest(unittest.TestCase):

    def setUp(self):
        self.rf1 = RemoteFile('http://elbenshira.com/d/testdl.txt')
        self.rf2 = RemoteFile('http://elbenshira.com/d/testdl2.txt')
        self.rf3 = RemoteFile('http://elbenshira.com/d/medical.txt')

    def tearDown(self):
        pass

    def test_read1(self):
        chunk = self.rf2.read(chunk_size=1)
        self.assertEqual(chunk, '1')

    def test_read2(self):
        chunk = self.rf2.read(chunk_size=0)
        self.assertEqual(chunk, '')

    def test_read3(self):
        chunk = self.rf2.read(chunk_size=99999999)
        self.assertEqual(chunk, '1234567890')

    def test_read4(self):
        chunk = self.rf2.read(chunk_size=99999999)
        chunk = self.rf2.read(chunk_size=99999999)
        self.assertEqual(chunk, '')

    def test_read5(self):
        chunk = self.rf2.read(chunk_size=99999999)
        chunk = self.rf2.read(chunk_size=99999999)
        chunk = self.rf2.read(chunk_size=99999999)
        self.assertEqual(chunk, '')

    def test_read6(self):
        data = ''
        chunk = None
        while chunk != '':
            chunk = self.rf2.read(chunk_size=1)
            data += chunk
        self.assertEqual(chunk, '1234567890')

    def test_read7(self):
        chunk = self.rf2.read(chunk_size=0)
        chunk = self.rf2.read(chunk_size=0)
        chunk = self.rf2.read(chunk_size=0)
        self.assertEqual(chunk, '')

    def test_read1(self):
        chunk = self.rf2.read(chunk_size=1)
        self.assertEqual(chunk, '1')

"""
    def testExample2(self):
        truths = [True, True, True]
        for i in truths:
            self.assert_(i)    # passes if argument is True

"""

if __name__ == '__main__':
    unittest.main()

