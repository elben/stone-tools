from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import threading

# TODO: refactor configuration file loading to a static method.
config_file = "../config/config.conf"
if len(sys.argv) >= 2 and sys.argv[1] != '':
    # passed in as first argument
    config_file = sys.argv[1]
configs = ConfigParser.ConfigParser()
configs.read(config_file)

XMLRPC_IP = configs.get("disciple", "xmlrpcip")
XMLRPC_PORT = int(configs.get("disciple", "xmlrpcport"))

class DiscipleServerThread(threading.Thread):

    def __init__(self, discp_state, ip = "localhost", port = "8800"):
        threading.Thread.__init__()

        self.__ip = ip
        self.__port = port
        self.__discp_state = discp_state

        self.__server = SimpleXMLRPCServer((ip, port))
        self.__server.register_introspection_functions()
        self.__server.register_instance(self.__discp_state)

    def run(self):
        """Serve forever."""
        try:
            self.__server.serve_forever()
        finally:
            self.__server.server_close()

class HDPVRException(Exception):
    pass

class HDPVR:
    def __init__(self, device):
        self.__device = str(device)    # full path to device
        self.__stream = None

    def open(self):
        """
        Opens streaming HDPVR device for reading.
        Throws HDPVRException if failed to open.
        """
        if self.exists():
            self.__stream = open(self.get_device_name(), "r")
        else:
            except HDPVRException("Could not open HDPVR device " +
                    self.get_device_name() + ". Device does not exist.")

    def close(self):
        """
        User must manually close HDPVR object.
        """
        if self.exists():
            self.__stream.close()
        else:
            except HDPVRException("Could not close HDPVR device " +
                    self.get_device_name() + ". Device does not exist.")

    def read(self, bytes=1024*400):
        if self.__stream is None:
            except HDPVRException("HDPVR device " + self.get_device_name() +
                    " not open.")
        return self.__stream.read(bytes)

    def exists(self):
        """Returns True if OS detected HDPVR."""
        if os.path.exists(self.get_device_name()):
            return True
        return False

    def get_device_name(self):
        return self.__device

class IllegalStateException(Exception):
    pass

class DiscipleState:
    """
    DiscipleState used to communicate state of a disciple between the
    disciple and Teacher.

    Thread-safe (we hope).
    """

    # Consts to represent where a state is at.
    # For example, a disciple's 'recording' state can be in four different
    # states: OFF = not recording, OFF_ON = starting up recording, ON =
    # recording, ON_OFF = stopping recording
    OFF = 0
    OFF_ON = 1      # intermediate state when turning on
    ON = 2
    ON_OFF = 3      # intermediate state 
    
    def __init__(self, key_disciple='', key_teacher=''):
        # key idea: to prevent disciple and teacher from doing illegal
        # activities, we force them to pass in a key for every method call,
        # and we make sure that it is a legal call
        self.__key_disciple = key_disciple
        self.__key_teacher = key_teacher

        self.__exist_state = DiscipleState.OFF
        self.__arm_state = DiscipleState.OFF
        self.__record_state = DiscipleState.OFF

        self.__update_lock = threading.RLock()

    # get states

    def exists(self):
        return self.__exist_state == DiscipleState.ON
    def disarmed(self):
        return self.__arm_state == DiscipleState.OFF
    def arming(self):
        return self.__arm_state == DiscipleState.OFF_ON
    def armed(self):
        return self.__arm_state == DiscipleState.ON
    def disarming(self):
        return self.__arm_state = DiscipleState.ON_OFF

    def not_recording(self):
        return self.__record_state == DiscipleState.OFF
    def starting_recording(self):
        return self.__record_state == DiscipleState.OFF_ON
    def recording(self):
        return self.__record_state == DiscipleState.ON
    def stopping_recording(self):
        return self.__record_state = DiscipleState.ON_OFF

    # send commands

    def cmd_exist(self):
        with self.__update_lock:
            self.__exist_state = DiscipleState.ON

    def cmd_unexist(self):
        """
        Only call if disciple is about to die. Assume everything failed, so
        we assume that we are no longer armed or recording. That is, we
        bypass the ON_OFF state.
        """
        with self.__update_lock:
            self.__exist_state = DiscipleState.OFF
            self.__arm_state = DiscipleState.OFF
            self.__record_state = DiscipleState.OFF

    def cmd_arm(self):
        with self.__update_lock:
            if self.exists():
                self.__arm_state = DiscipleState.OFF_ON
                return True
            else:
                return False

    def cmd_armed(self):
        with self.__update_lock:
            if self.exists() and self.arming():
                self.__arm_state = DiscipleState.ON
                return True
            else:
                return False

    def cmd_disarm(self):
        with self.__update_lock:
            if self.exists():
                self.__arm_state = DiscipleState.ON_OFF
                self.cmd_stop_recording()
                return True
            else:
                return False

    def cmd_disarmed(self):
        with self.__update_lock:
            if self.exists():
                self.__arm_state = DiscipleState.OFF
                self.__record_state = DiscipleState.OFF
                return True
            else:
                return False

    def cmd_start_recording(self):
        with self.__update_lock:
            if self.exists() and self.armed():
                self.__record_state = DiscipleState.OFF_ON
                return True
            else:
                return False

    def cmd_recording(self):
        with self.__update_lock:
            if self.exists() and self.starting_recording():
                self.__record_state = DiscipleState.ON
                return True
            else:
                return False

    def cmd_stop_recording(self):
        with self.__update_lock:
            if self.exists() and self.armed():
                self.__record_state = DiscipleState.ON_OFF
                return True
            else:
                return False

    def cmd_stopped_recording(self):
        with self.__update_lock:
            if self.exists() and self.armed():
                self.__record_state = DiscipleState.OFF
                return True
            else:
                return False
