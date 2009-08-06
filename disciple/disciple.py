import subprocess as sp
import os
import time
import random

teacher_ip = "192.168.1.100"
remote_dir = "/var/www"
nfs_dir = "/teacher"

hdpvr_device = "video1"
video_prefix = "disciple_"

arm_file = nfs_dir + "/arm"
record_file = nfs_dir + "/record"

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
        
        # create an "exist" file and wait for it to be removed as
        # confirmation from teacher that things will start happening
        print "Waiting for comfirmation of existence from teacher..."
        try:
            # create the "exist" file if we can
            exist_file_name = nfs_dir + "/exist_" + mac_address
            with open(exist_file_name, "w") as f:
                f.write("Hello world!")
        except:
            # we assume it is already there
            pass
        
        # wait for the file we made to dissappear
        while True:
            try:
                os.stat(exist_file_name)
            except:
                print "Existence confirmed"
                break
        
        # open device for reading and ready a file to save video to
        video_stream = open("/dev/" + device, "r")
        video_file = open(video_file_name, "w")
        video_file_name = nfs_dir + "/" + video_prefix + mac
        
        armed = get_arm_signal(mac_address)
        record = False
        
        # deal with armed/record states
        read_size = 1000
        
        # wait to be armed
        while not armed:
            print "Waiting for arm signal..."
            armed = get_arm_signal(mac_address)
            time.sleep(0.5)
        
        print "Got arm signal"
        
        # if armed, wait to be told to record
        while armed:
            # if it's not go-time yet, throw data away but be ready
            if not record:
                record = get_record_signal(mac_address)
                video_stream.read(read_size)
            else: # if it's go-time, write that data out to the file
                video_file.write(video_stream.read(read_size))
            
            # make sure that if we ever stop recording, we disarm too
            if not record:
                "Disarming and stopping record..."
                armed = False
        
        # close the stream and file
        video_stream.close()
        video_file.close()
        
        print "Done recording"

def get_arm_signal(mac_address):
    try: # try to remove it and return true
        os.remove(arm_file + mac_address)
        return True
    except: # otherwise it hasn't come in yet, so return false
        return False

def get_record_signal(mac_address):
    try: # try to remove it and return true
        os.remove(record_file + mac_address)
        return True
    except: # otherwise it hasn't come in yet, so return false
        return False

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
