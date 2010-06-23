#!/usr/bin/python
import os
import sys
import subprocess
from time import sleep
import re
import ConfigParser

def printNotify(action, proto, port, completed=True):
    """
    Send status to client.
    """
    sys.stdout.write("%s %s %d %d\n" % (action, proto, port, completed))
    sys.stdout.flush()
   
def getOpenPorts(app_pid):
    """
    List open ports for app_pid
    """
    ports_new = list(list())
    netstat = subprocess.Popen(["/bin/netstat", "-lnp"], stdout=subprocess.PIPE)
    netstat.wait()
    netstat_out = netstat.communicate()[0].split('\n')
    for line in netstat_out:
        info = re.match('(udp|tcp)( *[0-9]*){2} *(0.){3}0:([0-9]*) *([0-9]{1,3}.){3}[0-9]{1,3}:([*]|([0-9])*) *[A-Z]* *(%d)/' % app_pid, line)
        if info is not None:
            ports_new.append([info.group(1), int(info.group(4))])
    return ports_new

def updatePorts(app_pid, app_path):
    """
    Cycle
    """
    ports_new = getOpenPorts(app_pid)
    if ports_new is None:
        return
    for port in ports_new:
        if port not in allowed_apps[app_path]:
            ports_new.remove(port)
    if ports_new==[]:
        return
    to_open = subList(ports, ports_new)
    to_close = subList(ports_new, ports)
    if to_open==[] and to_close==[]:
        return
    updateFirewall(subList(ports, ports_new), subList(ports_new, ports))
       
def subList(list2, list1):
    """
    Subtract list2 from list1
    """
    list_new = list()
    for item in list1:
        if item not in list2:
            list_new.append(item)
    return list_new
    
def updateFirewall(open=None, close=None):
    """
    Update Firewall Rules
    """
    if open is not None:
        for port in open:
            iptables=subprocess.Popen("/usr/sbin/iptables -A INPUT -p %s --dport %d -j ACCEPT" % (port[0], port[1]), shell=True, stdout=subprocess.PIPE)
            iptables.wait()
            if iptables.poll() == 0:
                printNotify("open", port[0], port[1], True)
                ports.append(port)
            else:
                printNotify("open", port[0], port[1], False)
    if close is not None:
        for port in close:
            iptables=subprocess.Popen("/usr/sbin/iptables -D INPUT -p %s --dport %d -j ACCEPT" % (port[0], port[1]), shell=True, stdout=subprocess.PIPE)
            iptables.wait()
            if iptables.poll() == 0:
                printNotify("close", port[0], port[1], True)
                ports.remove(port)
            else:
                printNotify("close", port[0], port[1], False)

def main_function():
    """
    Main Thread
    """
    app_pid = int(sys.argv[1])
    proc_path = os.path.join("/proc", str(app_pid))
    app_path = os.path.realpath(os.path.join(proc_path, "exe"))
    try:
        while ports==[]:
            updatePorts(app_pid, app_path)
            sleep(2)
        while os.path.exists(proc_path):
            sleep(20)
            updatePorts(app_pid, app_path)
    finally:
        updateFirewall(close=ports[:])
        sys.exit(0)

if __name__ == "__main__":
    """ Begin Globals """
    allowed_apps = {}
    config = ConfigParser.RawConfigParser()
    config.read("/etc/punchfw.cfg")
    for program in config.sections():
        allowed_apps[program] = [ 
            [ port.split('/')[1], int (port.split('/')[0])] for port in config.get(program,"ports").split()
            ]
    ports = list(list())
    """ End Globals """
    main_function()
