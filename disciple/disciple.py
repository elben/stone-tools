import subprocess as sp
import os
import time

teacher_ip = "192.168.1.100"
teacher_dir = "/disciple_vids"
teacher_local_dir = "/teacher"
nfs_dir = "/teacher"
hdpvr_device = "video0"
video_prefix = "disciple_"

def main():
    while True:
        # pause before continuing, at the top to prevent spamming messages
        time.sleep(1)
        
        # mount nfs
        if not nfs_mounted(teacher_ip):
            print "Mounting NFS share"
            sp.call( ["mount", teacher_ip + ":" + teacher_dir, nfs_dir] )
            
            continue
        else:
            print "NFS mounted"
        
        # check for usb device
        if not hdpvr_attached("Hauppauge"):
            print "Could not find the device in lsusb, reloading driver"
            sp.call( ["rmmod", "hdpvr"] )
            sp.call( ["modprobe", "hdpvr"] )
            
            continue
        
        # look in /dev for video device
        if not hdpvr_device_exists(hdpvr_device):
            print "Could not find '/dev/video0'"
            
            continue
        
        # get the mac address and use it as the video file name
        fname = get_mac_address()
        if fname == None:
            print "No suitable MAC adress found."
            
            continue
        
        fname = teacher_local_dir + "/" + video_prefix + fname
        
        # cat from device to the nfs mount
        print "Capturing video to", "'" + fname + "'"
        print "\nVIDEO CAPTURE FAILED!\n"
        
        # kill all current cat processes, makes sure we don't do anything dumb
        sp.call(["killall", "cat"], stdout = sp.PIPE, stderr = sp.STDOUT)
        
        # this will not release control until it is done or it fails
        cat_video("video0", fname)
    
def cat_video(device, out_file):
    cmd = "cat /dev/%(d)s >> %(of)s" % {"d": device, "of": out_file}
    
    return sp.call(cmd, shell = True, stdout = sp.PIPE, stderr = sp.PIPE)

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
            mac_address = mac_address.strip() # strip newlines/spaces from ends
            
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

def hdpvr_attached(device_name):
    lsusb = sp.Popen( ["lsusb"], stdout = sp.PIPE )
    
    num_found = ( lsusb.communicate()[0] ).count( str(device_name) )
    
    if num_found > 0:
        return True
    return False

def nfs_mounted(ip):
    with open("/proc/mounts") as file:
        mounts = file.read()
    
    if mounts.count( str(ip) ) > 0:
        return True
    return False

if __name__ == "__main__":
    main()
