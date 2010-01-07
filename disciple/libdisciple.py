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
    DISCIPLE_NONEXISTENT = 0
    DISCIPLE_EXISTS = 1
    DISCIPLE_EXISTS_ARMED = 2
    DISCIPLE_EXISTS_ARMED_RECORDING = 3

    def __init__(self, id = "", exists = False, armed = False, recording = False):
        self.__id = id
        self.__exists = exists
        self.__armed = armed
        self.__recording = recording

        self.__command_arm = False
        self.__command_disarm = False
        self.__command_record = False
        self.__command_stop_recording = False

    def get_id(self):
        return self.__id

    def current_state(self):
        if self.__exists and self.__armed and self.__recording:
            return DiscipleState.DISCIPLE_EXISTS_ARMED_RECORDING
        elif self.__exists and self.__armed:
            return DiscipleState.DISCIPLE_EXISTS_ARMED
        elif self.__exists:
            return DiscipleState.DISCIPLE_EXISTS

        return DiscipleState.DISCIPLE_NONEXISTENT
        
    def exists(self):
        return self.__exists
    
    def is_armed(self):
        return self.__armed

    def is_recording(self):
        return self.__recording

    def set_id(self, id):
        self.__id = id

    def set_exists(self, flag):
        if flag:
            self.__exists = True
        else:
            self.__exists = False
            self.set_armed(False)
            self.set_recording(False)
        return True
            
    def set_armed(self, flag):
        if flag and self.exists():
            self.__armed = True
        elif flag and not self.exists():
            return False
        else:
            self.__armed = False
            self.set_recording(False)
        return True

    def set_recording(self, flag):
        if flag and self.exists() and self.is_armed():
            self.__recording = True
        elif flag and not (self.exists() and self.is_armed()):
            return False
        else:
            self.__recording = False
        return True

    def command_arm_on(self):
        self.__command_arm = True
    def command_arm_off(self):
        self.__command_arm = False
    def command_disarm_on(self):
        self.__command_disarm = True
    def command_disarm_off(self):
        self.__command_disarm = True
    def command_record_on(self):
        self.__command_record = True
    def command_record_off(self):
        self.__command_record = False
    def command_stop_recording_on(self):
        self.__command_record = True
    def command_stop_recording_off(self):
        self.__command_record = False

    def command_arm_status(self):
        return self.__command_arm
    def command_disarm_status(self):
        return self.__command_disarm
    def command_record_status(self):
        return self.__command_record
    def command_stop_recording_status(self):
        return self.__command_stop_recording

