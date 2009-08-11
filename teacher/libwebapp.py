import os

class TeacherControl:
    STATE_UNKNOWN = 0x0
    STATE_LET_RECORD= 0x01
    STATE_DONT_RECORD= 0x02

    STATE_EXIST_VERIFIED = 0x10
    STATE_ARM_SENT = 0x20
    STATE_ARM_VERIFIED = 0x40
    STATE_RECORD_SENT = 0x80
    STATE_RECORD_END = 0x100
    
    def __init__(self, dir="/var/www/"):
        self.dir = dir

        self.disciples = []     # unique identifier (e.g. MAC addr)
        self.states = []        # state of each disciple
    
    def verify_exist(self):
        pass
    def signal_arm(self):
        pass
    def verify_arm(self):
        pass
    def signal_record(self):
        pass
    def end_record(self):
        pass

    def search(self, prefix="exist_"):
        """
        Returns files in dir with prefix.
        """

        files = []
        
        # get a list of strings representing files
        for file in os.listdir(self.dir):
            if (file.startswith(prefix) and not os.path.isdir(file)):
                # valid prefix and not a directory
                files.append(self.dir + file)
        return files
            
    def get_id(self, s, delim="_"):
        """
        Grabs the unique id from a string s.

        The unique id is defined as any text to the right of
        the last delim (defaults to '_')
        """

        s = str(s)
        unique = ""     # the unique id stripped from s

        # iterate through string backwards
        for c in s[::-1]:
            if c != delim:
                # haven't found most-right delim
                unique += c     # build unique backwards
            else:
                # found most-right delim
                break
        # reverse string
        return unique[::-1]

