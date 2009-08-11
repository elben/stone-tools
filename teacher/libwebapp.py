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
    
    def __init__(self, dir="/var/www"):
        self.dir = dir
        self.disciples = []     # unique identifier (e.g. MAC addr)
        self.states = []        # state of each disciple
    
    def verify_exist(self):
        """
        Finds and verifies the existence of disciples.

        Looks for 'exist' files, extracts the unique id, and
        adds that new disciple to the list of known disciples.
        """

        for file in self.search(prefix="exist_"):
            id = self.get_id(file)
            if id not in self.disciples:
                # found new disciple
                self.disciples.append(id)
                self.states.append(TeacherControl.STATE_EXIST_VERIFIED)
            else:
                # disciple's existence already known for some reason;
                # attempt to handle error
                i = self.disciples.index(id)
                self.states[i] |= TeacherControl.STATE_EXIST_VERIFIED
            # signal to disciple that webapp verified existence
            self.remove_file(file)

    def signal_arm(self, ids):
        """
        Signal given disciples (ids) to arm for the glorious battle.

        Creates 'arm' files and sets STATE_ARM_SENT.
        """
        self.create_signal(ids, prefix="arm_",
                state=TeacherControl.STATE_ARM_SENT)

    def verify_arm(self):
        """
        Verify armed disciples.

        If an arm signal was sent to a disciple, and the 'arm' file
        no longer exists, then disciple is armed, so set state to armed.
        """
        for i in range(len(self.disciples)):
            id = self.disciples[i]
            state = self.states[i]
            if self.arm_sent(state) and not self.file_exists('arm_'+id):
                # arm signal was sent, and now 'arm' file does not
                # exist; thus, disciple armed
                self.states[i] |= TeacherControl.STATE_ARM_VERIFIED
                self.remove_file('arm_'+id)

    def signal_record(self, ids):
        """
        Signal given disciples (ids) to start recording.
        """
        self.create_signal(ids, prefix="record_",
                state=TeacherControl.STATE_RECORD_SENT)

    def end_record(self, ids):
        """
        Signal given disciples (ids) to stop recording.

        Removes 'record' files.
        """
        for id in ids:
            self.remove_file('record_'+id)
            self.states[self.disciples.index(id)] |= TeacherControl.STATE_RECORD_END

    def create_signal(self, ids, prefix, state):
        for id in ids:
            if id not in self.disciples:
                raise Exception("TeacherControl: " +
                        "attempted to signal unknown id "+id)

            # touch/create signal file
            try: 
                open(os.path.join(self.dir, prefix+id), 'a').close()
            except:
                raise Exception("TeacherControl: " + 
                    "failed to create '"+prefix+"' file for " + id)

            # flag the state
            self.states[self.disciples.index(id)] |= state


    def search_id(self, prefix):
        return [self.get_id(file) for file in self.search(prefix)]

    def search(self, prefix):
        """
        Returns files in dir with prefix.
        """

        files = []
        
        # get a list of strings representing files
        for file in os.listdir(self.dir):
            if (file.startswith(prefix) and not os.path.isdir(file)):
                # valid prefix and not a directory
                files.append(os.path.join(self.dir, file))
        return files

    def reset(self, ids=None):
        """Reset state of disciple(s)."""

        if ids is None:
            # reset all disciples
            self.states = [0x0 * len(self.states)]
        elif type(ids) == str:
            # reset one disciple
            self.states[self.disciples.index(ids)] = 0x0
        elif type(ids) == list:
            # reset a list of disciples
            for id in ids:
                self.states[self.disciples.index(id)] = 0x0

    def remove_file(self, file):
        os.remove(os.path.join(self.dir, file))

    def file_exists(self, file):
        return os.path.isfile(os.path.join(self.dir, file))

    def valid(self):
        """Returns True if TeacherControl is still in a valid state."""
        return len(self.disciples) == len(self.states)

    def __str__(self):
        s = ""
        for id, state in zip(self.disciples, self.states):
            s += "id: " + id + "\n"
            s += "state: " + str(state) + "\n"
            if self.exist_verified(state):
                s += "    Existence verified.\n"
            if self.arm_sent(state):
                s += "    Arm sent.\n"
            if self.arm_verified(state):
                s += "    Arm verified.\n"
            if self.record_sent(state):
                s += "    Record sent.\n"
            if self.record_end(state):
                s += "    Record end.\n"
        return s

    @staticmethod
    def get_id(s, delim="_"):
        """
        Grabs the unique id from a string s.

        The unique id is defined as any text to the right of
        the last delim (defaults to '_')
        """

        s = str(s)
        id = ""     # the unique id stripped from s

        # iterate through string backwards
        for c in s[::-1]:
            if c != delim:
                # haven't found most-right delim
                id += c     # build id backwards
            else:
                # found most-right delim
                break
        # reverse string
        return id[::-1]

    @staticmethod
    def exist_verified(state):
        return state & TeacherControl.STATE_EXIST_VERIFIED != 0

    @staticmethod
    def arm_sent(state):
        return state & TeacherControl.STATE_ARM_SENT != 0

    @staticmethod
    def arm_verified(state):
        return state & TeacherControl.STATE_ARM_VERIFIED != 0

    @staticmethod
    def record_sent(state):
        return state & TeacherControl.STATE_RECORD_SENT != 0

    @staticmethod
    def record_end(state):
        return state & TeacherControl.STATE_RECORD_END != 0
