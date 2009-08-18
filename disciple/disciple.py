import subprocess as sp
import os
import time
import random

teacher_ip = "10.100.1.242"
remote_dir = "/var/www"
nfs_dir = "/teacher"

hdpvr_device = "video0"
video_prefix = "disciple_"

exist_file = os.path.join(nfs_dir, "exist_")
exist_verified_file = os.path.join(nfs_dir, "exist_verified_")
arm_file = os.path.join(nfs_dir, "arm_")
arm_verified_file = os.path.join(nfs_dir, "arm_verified_")
record_file = os.path.join(nfs_dir, "record_")
record_verified_file = os.path.join(nfs_dir, "record_verified_")

def main():
    while True:
        # pause before continuing, at the top to prevent spamming messages
        time.sleep(0.5)
        
        # mount nfs
        if not nfs_mounted(teacher_ip):
            print "Mounting NFS share"
            sp.call( ["mount", teacher_ip + ":" + remote_dir, nfs_dir] )
            
            continue
        else:
            print "NFS mounted"

        # look in /dev for video device
        if not hdpvr_device_exists(hdpvr_device):
            print ("Could not find '/dev/" + hdpvr_device +
                   "', reloading driver")
            sp.call( ["rmmod", "hdpvr"] )
            sp.call( ["modprobe", "hdpvr"] )
            
            continue
        
        # get the mac address and use it as the video file name
        mac_address = get_mac_address()
        if mac_address == None:
            print "No suitable MAC adress found, using random file name"
            mac_address = str( random.uniform(100000000000, 999999999999) )
        
        # send 'exist' signal to let Teacher know disciple exists
        open(exist_file + mac_address, "a").close()

        # wait for 'exist_verified' signal
        print "Waiting for 'exist_verified' signal..."
        while not os.path.isfile(exist_verified_file+mac_address):
            time.sleep(0.2)
        print "Existence confirmed."

        os.remove(exist_file + mac_address)  # remove 'exist' signal

        # open device for reading and ready a file to save video to
        video_stream = open("/dev/" + hdpvr_device, "r")
        video_file_name = os.path.join(nfs_dir, video_prefix + mac_address)
        video_file = open(video_file_name, "w")
        
        # wait to be armed
        armed = get_arm_signal(mac_address)
        while not armed:
            print "Waiting for 'arm' signal..."
            armed = get_arm_signal(mac_address)
            time.sleep(0.5)
        print "Got arm signal."
        # send 'arm_verified' signal
        open(arm_verified_file + mac_address, "a").close()
        
        # if it's not go-time yet, throw data away but be ready
        read_size = 1000
        while not received_record_signal(mac_address):
            print "Waiting for 'record' signal..."
            video_stream.read(read_size)
        
        # it's go-time, send a 'record_verified' signal
        open(record_verified_file + mac_address, "a").close()
        print "Recording to " + video_file_name + "'..."
        while received_record_signal(mac_address):
            # write data out to the file
            video_file.write(video_stream.read(read_size))
            
        # make sure that if we ever stop recording, we disarm too
        print "Disarming and stopping record..."
        armed = False
        # remove 'arm_verified' and 'record_verified' signals
        os.remove(arm_verified_file+mac_address)
        os.remove(record_verified_file+mac_address)
        
        # close the stream and file
        video_stream.close()
        video_file.close()
        
        print "Done recording."

def get_arm_signal(mac_address):
    """Returns True if 'arm' signal exists; False otherwise."""
    return os.path.isfile(arm_file + mac_address)

def received_record_signal(mac_address):
    """Returns True if 'record' signal exists, False otherwise."""
    return os.path.isfile(record_file + mac_address)

def get_mac_address():
    ifconfig = sp.Popen( ["ifconfig", "-a"], stdout = sp.PIPE )
    
    interfaces = ifconfig.communicate()[0]
    
    # make sure we have at least one mac address to use
    if interfaces.count("HWaddr") < 1:
        return None
    
    interfaces = interfaces.splitlines()
    for line in interfaces:
        if line.count( "HWaddr" ) > 0:
            mac_address = line.split("HWaddr ")
            mac_address = mac_address[1] # the part after HWaddr
            mac_address = mac_address.replace(":", "") # remove colons
            mac_address = mac_address.strip() # strip whitespace from ends
            
            # make sure we've got a real mac address
            if len(mac_address) != 12: # length with colons removed
                continue
            
            return mac_address
    
    # none of the mac addresses were valid
    return None

def hdpvr_device_exists(device):
    dev_dir = os.listdir("/dev")
    
    if str(device) in dev_dir:
        return True
    return False

# def hdpvr_attached(device_name):
#     lsusb = sp.Popen( ["lsusb"], stdout = sp.PIPE )
    
#     num_found = ( lsusb.communicate()[0] ).count( str(device_name) )
    
#     if num_found > 0:
#         return True
#     return False

def nfs_mounted(ip):
    with open("/proc/mounts") as file:
        mounts = file.read()
    
    if mounts.count( str(ip) ) > 0:
        return True
    return False

if __name__ == "__main__":
    main()
