# A crash course on Python unit testing.
# Read more here: http://docs.python.org/library/unittest.html

import unittest

class ExampleTest(unittest.TestCase):

    # This is a simple test example meant to get you up and running quickly.
    # You can read the unittest docs if you want more power over your tests.

    def setUp(self):
        # Called before each test case is executed.
        print "Let's start testing silly things!"

    def tearDown(self):
        # Called after each test is executed, even if the test throws an
        # Exception.
        print "Done testing silly things!"
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

