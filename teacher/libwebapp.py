import os

class TeacherControl:
    UNKNOWN = 0x0
    LET_RECORD= 0x01
    DONT_RECORD= 0x02

    EXIST_VERIFIED = 0x10
    ARM_SENT = 0x20
    ARM_VERIFIED = 0x40
    RECORD_SENT = 0x80
    RECORD_VERIFIED = 0x100
    RECORD_END = 0x200
    
    def __init__(self, dir="/var/www"):
        self.dir = dir
        self.disciples = []     # unique identifier (e.g. MAC addr)
        self.states = []        # state of each disciple
        self.mine_signals()
    
    def verify_exist(self):
        """
        Finds and verifies the existence of disciples.

        Looks for 'exist' files, extracts the unique id, and
        adds that new disciple to the list of known disciples.
        Then, remove the 'exist' files and create 'exist_verified' files.
        """

        for file in self.search(prefix="exist_"):
            id = self.get_id(file)
            if id not in self.disciples:
                # found new disciple
                self.disciples.append(id)
                self.states.append(TeacherControl.EXIST_VERIFIED)
            else:
                # disciple's existence already known for some reason;
                # attempt to handle error
                i = self.disciples.index(id)
                self.states[i] |= TeacherControl.EXIST_VERIFIED
            # signal to disciple that webapp verified existence
            self.create_signal(id, prefix="exist_verified_")

    def signal_arm(self, ids):
        """
        Signal given disciples (ids) to arm for the glorious battle.

        Creates 'arm' files and sets ARM_SENT.
        """
        self.create_signals(ids, prefix="arm_",
                state=TeacherControl.ARM_SENT,
                precond=self.exist_verified)

    def verify_arm(self):
        """
        Verify armed disciples.

        If an arm signal was sent to a disciple and the 'arm_verified' file
        exists, then disciple is armed, so set state to armed.
        """
        for i in range(len(self.disciples)):
            id = self.disciples[i]
            state = self.states[i]
            if self.arm_sent(state) and self.file_exists('arm_verified_'+id):
                # disciple is armed
                self.states[i] |= TeacherControl.ARM_VERIFIED

                # remove 'arm' signal
                self.remove_signal('arm_'+id)

    def signal_record(self, ids):
        """
        Signal given disciples (ids) to start recording.
        """
        self.create_signals(ids, prefix="record_",
                state=TeacherControl.RECORD_SENT,
                precond=self.arm_verified)

    def verify_record(self):
        """
        Verify recording disciples.

        If webapp received 'arm_verified' and 'record_verified' signals,
        then disciple is recording.
        """
        for i in range(len(self.disciples)):
            id = self.disciples[i]
            state = self.states[i]
            if (self.arm_verified(state) and
                    self.file_exists('record_verified_'+id)):
                # disciple is recording
                self.states[i] |= TeacherControl.RECORD_VERIFIED

    def signal_end_record(self, ids):
        """
        Signal given disciples (ids) to stop recording by removing 'record'
        signals.
        """
        for id in ids:
            self.states[self.disciples.index(id)] |= TeacherControl.RECORD_END
            self.remove_signal('record_'+id)
            self.remove_signal('record_verified_'+id)

    def create_signals(self, ids, prefix, state=None, precond=None):
        """
        Creates a signal (i.e. file) for all ids and set their state.

        precond is a function each disciple needs to meet for a
        signal to be sent.
        """
        for id in ids:
            self.create_signal(id, prefix, state, precond)
    
    def create_signal(self, id, prefix, state=None, precond=None):
        """
        Creates a signal (i.e. file) for id and set its state.

        precond is a function that disciple needs to meet for a
        signal to be sent.
        """
        if id not in self.disciples:
            raise Exception("TeacherControl: " +
                    "attempted to signal unknown id "+id)

        i = self.disciples.index(id)
        if precond is not None and not precond(self.states[i]):
            # precondition not met, skip this id
            return

        # touch/create signal file
        try: 
            open(os.path.join(self.dir, prefix+id), 'a').close()
        except:
            raise Exception("TeacherControl: " + 
                "failed to create '"+prefix+"' file for " + id)

        if state is not None:
            # flag the state
            self.states[self.disciples.index(id)] |= state

    def mine_signals(self):
        """
        Search through self.dir for signals and set the states of disciples
        to signals received.

        WARNING: preconditions as specified in the protocol is not checked.
        For example, a 'arm_verified' signal may be present, but not a
        'exist_verified'. In this case, mine_signals() will still harvest
        the 'arm_verified' signal.
        """

        # reset disciples if need be
        if self.disciples != []:
            self.disciples = []
        if self.states != []:
            self.states = []

        for id in self.search_id(prefix='exist_verified_'):
            if id not in self.disciples:
                self.disciples.append(id)
                self.states.append(TeacherControl.EXIST_VERIFIED)
            else:
                i = self.disciples.index(id)
                self.states[i] |= TeacherControl.EXIST_VERIFIED

        for id in self.search_id(prefix='arm_verified_'):
            if id not in self.disciples:
                self.disciples.append(id)
                self.states.append(TeacherControl.ARM_VERIFIED)
            else:
                i = self.disciples.index(id)
                self.states[i] |= TeacherControl.ARM_VERIFIED

        for id in self.search_id(prefix='record_verified_'):
            if id not in self.disciples:
                self.disciples.append(id)
                self.states.append(TeacherControl.RECORD_VERIFIED)
            else:
                i = self.disciples.index(id)
                self.states[i] |= TeacherControl.RECORD_VERIFIED

    def search_id(self, prefix):
        """
        Return ids in dir with prefix.
        """
        return [self.get_id(file) for file in self.search(prefix)]

    def search(self, prefix):
        """
        Return files in dir with prefix.
        """

        files = []
        
        # get a list of strings representing files
        for file in os.listdir(self.dir):
            if (file.startswith(prefix) and not os.path.isdir(file)):
                # valid prefix and not a directory
                files.append(file)
        return files

    def reset(self, ids=None):
        """
        Reset state of disciples.

        ids can be a string or an iterable.
        """

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

    def remove_signal(self, file):
        os.remove(os.path.join(self.dir, file))

    def file_exists(self, file):
        return os.path.isfile(os.path.join(self.dir, file))

    def valid(self):
        """Returns True if TeacherControl is still in a valid state."""
        return len(self.disciples) == len(self.states)

    def status_str(self, id):
        s = ""
        try:
            i = self.disciples.index(id)
        except:
            return s
        state = self.states[i]
        
        s += id + ": "
        if self.exist_verified(state):
            s += "Existence verified. "
        if self.arm_sent(state):
            s += "Arm sent. "
        if self.arm_verified(state):
            s += "Arm verified. "
        if self.record_sent(state):
            s += "Record sent. "
        if self.record_verified(state):
            s += "Record verified. "
        if self.record_end(state):
            s += "Record end. "
        return s

    def __str__(self):
        s = ""
        for id, state in zip(self.disciples, self.states):
            s += id + ":"
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
        return state & TeacherControl.EXIST_VERIFIED != 0

    @staticmethod
    def arm_sent(state):
        return state & TeacherControl.ARM_SENT != 0

    @staticmethod
    def arm_verified(state):
        return state & TeacherControl.ARM_VERIFIED != 0

    @staticmethod
    def record_sent(state):
        return state & TeacherControl.RECORD_SENT != 0

    @staticmethod
    def record_verified(state):
        return state & TeacherControl.RECORD_VERIFIED != 0

    @staticmethod
    def record_end(state):
        return state & TeacherControl.RECORD_END != 0
