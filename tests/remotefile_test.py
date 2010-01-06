import unittest
from downloader import *

class DownloaderTest(unittest.TestCase):

    def setUp(self):
        self.rf1 = RemoteFile('http://elbenshira.com/d/testdl.txt')
        self.rf2 = RemoteFile('http://elbenshira.com/d/testdl2.txt')
        self.rf3 = RemoteFile('http://elbenshira.com/d/medical.txt')
        self.rf4 = RemoteFile('http://elbenshira.com/d/empty.txt')

    def tearDown(self):
        pass

    def test_read01(self):
        chunk = self.rf2.read(chunk_size=1)
        self.assertEqual(chunk, '1')

    def test_read02(self):
        chunk = self.rf2.read(chunk_size=0)
        self.assertEqual(chunk, '')

    def test_read03(self):
        chunk = self.rf2.read(chunk_size=99999999)
        self.assertEqual(chunk, '1234567890')

    def test_read04(self):
        chunk = self.rf2.read(chunk_size=99999999)
        chunk = self.rf2.read(chunk_size=99999999)
        self.assertEqual(chunk, '')

    def test_read05(self):
        chunk = self.rf2.read(chunk_size=99999999)
        chunk = self.rf2.read(chunk_size=99999999)
        chunk = self.rf2.read(chunk_size=99999999)
        self.assertEqual(chunk, '')

    def test_read06(self):
        data = ''
        chunk = None
        while chunk != '':
            chunk = self.rf2.read(chunk_size=1)
            data += chunk
        self.assertEqual(data, '1234567890')

    def test_read07(self):
        chunk = self.rf2.read(chunk_size=0)
        chunk = self.rf2.read(chunk_size=0)
        chunk = self.rf2.read(chunk_size=0)
        self.assertEqual(chunk, '')

    def test_read08(self):
        chunk = self.rf2.read(chunk_size=1)
        chunk = self.rf2.read(chunk_size=1)
        chunk = self.rf2.read(chunk_size=1)
        self.assertEqual(chunk, '3')

    def test_read09(self):
        chunk = self.rf4.read(chunk_size=1)
        self.assertEqual(chunk, '')
        
    def test_read10(self):
        chunk = self.rf4.read(chunk_size=0)
        self.assertEqual(chunk, '')

    def test_read11(self):
        chunk = self.rf4.read(chunk_size=1)
        chunk = self.rf4.read(chunk_size=0)
        chunk = self.rf4.read(chunk_size=1)
        self.assertEqual(chunk, '')

    def test_read12(self):
        chunk = self.rf2.read(chunk_size=1)
        chunk = self.rf2.read(chunk_size=4)
        chunk = self.rf2.read(chunk_size=1)
        self.assertEqual(chunk, '6')

    def test_read13(self):
        chunk = self.rf2.read(chunk_size=3.8)
        self.assertEqual(chunk, '123')

    def test_read14(self):
        chunk = self.rf2.read(chunk_size=99999999)
        self.assertEqual(chunk, '1234567890')
        rf2_copy = RemoteFile('http://elbenshira.com/d/testdl2.txt')
        self.assertEqual(rf2_copy.read(99999), '1234567890')
"""
    def testExample2(self):
        truths = [True, True, True]
        for i in truths:
            self.assert_(i)    # passes if argument is True

"""

if __name__ == '__main__':
    unittest.main()

