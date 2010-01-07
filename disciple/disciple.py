#!/usr/bin/python

import subprocess as sp
import os
import sys
import time
import random
import ConfigParser
from libdisciple import *

# parse config file
config_file = "../config/config.conf"
if len(sys.argv) >= 2 and sys.argv[1] != '':
    # passed in as first argument
    config_file = sys.argv[1]
configs = ConfigParser.ConfigParser()
configs.read(config_file)

TEACHER_IP = configs.get("disciple", "teacher_ip")
REMOTE_DIR = configs.get("disciple", "remote_dir")
VIDEO_DIR = configs.get("disciple", "video_dir")

HDPVR_DEVICE = configs.get("disciple", "hdpvr_device")
VIDEO_PREFIX = configs.get("disciple", "video_prefix")

EXIST_FILE = os.path.join(NFS_DIR, "exist_")
EXIST_VERIFIED_FILE = os.path.join(NFS_DIR, "exist_verified_")
ARM_FILE = os.path.join(NFS_DIR, "arm_")
ARM_VERIFIED_FILE = os.path.join(NFS_DIR, "arm_verified_")
RECORD_FILE = os.path.join(NFS_DIR, "record_")
RECORD_VERIFIED_FILE = os.path.join(NFS_DIR, "record_verified_")

# for simplified signal file removal
SIGNAL_FILES = [ EXIST_FILE,
                 EXIST_VERIFIED_FILE,
                 ARM_FILE,
                 ARM_VERIFIED_FILE,
                 RECORD_FILE,
                 RECORD_VERIFIED_FILE ]

# block size to read from the device
READ_SIZE = 1024 * 400 # 400Kb

class Disciple:
    TIME_DELAY = 0.1 # seconds

    def __init__(self, device, video_dir="/var/www"):
        self.__hdpvr = HDPVR(device)
        self.__video_dir = video_dir
        self.__mac_addr = self.__get_mac_address()

        self.__state = DiscipleState()
        self.__server = DiscipleServerThread(self.__state)

    def spawn_server(self):
        # TODO: find a way to kill this beast
        # probably no hope of doing this
        if not self.__server.is_alive():
            self.__server.run()

    def run(self):
        # create video dir if does not exist
        if not os.path.isdir(self.get_video_dir()):
            os.mkdir(self.get_video_dir())

        self.__state.set_exists(True)

        # wait for arm signal
        while not self.__state.command_arm_status():
            time.sleep(Disciple.TIME_DELAY)

        # TODO: arm!
        self.__state.command_arm_off()
        self.__hdpvr.open()     # don't forget to call __hdpvr.close()
        video_file = open(self.get_video_path(), "wb")

        # wait for record signal
        while not self.__state.command_disarm_status():
            self.__hdpvr.read() # to read is to arm

        
        self.__state.command_record_off()

        # wait for stop record signal
        while not self.__state.command_stop_recording_status():
            time.sleep(Disciple.TIME_DELAY)

        
        video_file.write(video_stream.read(READ_SIZE))
        
        # force the update of file attributes
        video_file.flush()
        os.fsync(video_file.fileno())
        

        # TODO: stop recording!
        self.__state.command_stop_recording_off()
        self.__hdpvr.close()

    @staticmethod
    def __get_mac_address():
        ifconfig = sp.Popen( ["ifconfig", "-a"], stdout = sp.PIPE )
        
        interfaces = ifconfig.communicate()[0]
        
        # make sure we have at least one mac address to use
        if interfaces.count("HWaddr") < 1:
            return None
        
        # TODO: could be replaced w/ regex?
        interfaces = interfaces.splitlines()
        for line in interfaces:
            if line.count( "HWaddr" ) > 0:
                mac_address = line.split("HWaddr ")
                mac_address = mac_address[1] # the part after 'HWaddr '
                mac_address = mac_address.replace(":", "") # remove colons
                mac_address = mac_address.strip() # strip whitespace from ends
                
                # make sure we've got a real mac address
                length = 12
                if len(mac_address) != length: # length with colons removed
                    continue
                
                return mac_address
        
        # none of the mac addresses were valid
        return None

    def get_video_path(self, vid_prefix):
        return os.path.join(self.get_video_dir(), vid_prefix +
                self.get_mac_address())

    def get_video_dir(self):
        return self.__video_dir

    def get_mac_address(self):
        return self.__mac_addr

def main():
    # flags
    removed_signal_files = False
    
    while True:
        # pause before continuing, at the top to prevent spamming messages
        time.sleep(0.5)
        
        # mount nfs
        if not nfs_mounted(TEACHER_IP):
            print "Mounting NFS share"
            sp.call( ["mount", TEACHER_IP + ":" + REMOTE_DIR, NFS_DIR] )
            
            continue
        else:
            print "NFS mounted"
        
        # look in /dev for video device
        if not hdpvr_device_exists(HDPVR_DEVICE):
            print ("Could not find '/dev/" + HDPVR_DEVICE +
                   "', reloading driver")
            sp.call( ["rmmod", "hdpvr"] )
            sp.call( ["modprobe", "hdpvr"] )
            
            continue
        
        # get the mac address and use it as the video file name
        mac_address = get_mac_address()
        if mac_address == None:
            print "No suitable MAC adress found, using random file name"
            mac_address = str( random.uniform(100000000000, 999999999999) )
        
        # append the mac address to each file, for easy removal
        for i in range( len(SIGNAL_FILES) ):
            SIGNAL_FILES[i] = SIGNAL_FILES[i] + mac_address
            
        # remove old signal files, if any
        if not removed_signal_files:
            removed_signal_files = True
            
            print "Removing old signal files..."
            for file in SIGNAL_FILES:
                rm(file)
            print "Signal files removed"
            
        # send 'exist' signal to let teacher know disciple exists
        send_signal(EXIST_FILE, mac_address)
        
        # wait for 'exist_verified' signal
        print "Waiting for 'exist verified' signal..."
        while not get_signal(EXIST_VERIFIED_FILE, mac_address):
            time.sleep(0.2)
        print "Existence confirmed"
        
        video_file_name = os.path.join(NFS_DIR, VIDEO_PREFIX + mac_address)
        
        # wait to be armed
        print "Waiting for 'arm' signal..."
        while not get_signal(ARM_FILE, mac_address):
            time.sleep(0.2)
        print "Got arm signal"
        
        # open device for reading and ready a file to save video to
        video_stream = open("/dev/" + HDPVR_DEVICE, "r")
        video_file = open(video_file_name, "w")
        
        # send 'arm_verified' signal
        send_signal(ARM_VERIFIED_FILE, mac_address)
        
        # if it's not go-time yet, throw data away but be ready
        print "Waiting for 'record' signal..."
        while not get_signal(RECORD_FILE, mac_address):
            try:
                video_stream.read(READ_SIZE)
            except:
                continue
                
        print "Got record signal"
            
        # it's go-time, send a 'record_verified' signal
        print
        send_signal(RECORD_VERIFIED_FILE, mac_address)
        
        # do the actual recording
        print "Recording to '" + video_file_name + "'..."
        while get_signal(RECORD_FILE, mac_address):
            # write data out to the file
            video_file.write(video_stream.read(READ_SIZE))
            
            # force the update of file attributes
            video_file.flush()
            os.fsync(video_file.fileno())
        
        # make sure that if we ever stop recording, we disarm too
        print "Disarming and stopping record..."
        
        # remove all leftover signals to reset state
        print "Removing any leftover signal files..."
        for file in SIGNAL_FILES:
            rm(file)
        
        # close the stream and file
        video_stream.close()
        video_file.close()
        
        print "Done recording!"
        print

def rm(file):
    """Remove a file or directory, as long as it exists"""
    if os.path.isfile(file) or os.path.islink(file):
        os.remove(file)
    elif os.path.isdir(file):
        os.rmdir(file)


def hdpvr_device_exists(device):
    dev_dir = os.listdir("/dev")
    
    if str(device) in dev_dir:
        return True
    return False

def nfs_mounted(ip):
    with open("/proc/mounts") as file:
        mounts = file.read()
    
    if mounts.count( str(ip) ) > 0:
        return True
    return False

def example_hdpvr():
    hdpvr = HDPVR("/dev/video0")
    while not hdpvr.exists():
        time.sleep(0.1)
    hdpvr.open()

    while get_data:
        data = hdpvr.read(bytes)
        # append data into /var/www/video.ts
    hdpvr.close()

if __name__ == "__main__":
    main()

