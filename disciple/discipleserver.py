from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import threading

from disciple import DiscipleState

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

