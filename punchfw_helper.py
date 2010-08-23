#!/usr/bin/python
"""
Punches holes in the firewall for punchfw.
"""
import os
import sys
from subprocess import Popen, PIPE
from time import sleep
import re
import ConfigParser

CONFIG_FILE = "/etc/punchfw.cfg"
OPEN_CMD = "/usr/sbin/iptables -A INPUT -p {proto} --dport {dport} -j ACCEPT"
CLOSE_CMD = "/usr/sbin/iptables -D INPUT -p {proto} --dport {dport} -j ACCEPT"
NETSTAT_CMD = "/bin/netstat -lnp"
#LSOF_CMD = "lsof -p %d -a -i -Pln -FPn"
NETSTAT_PATTERN = r"""
(?P<proto>udp|tcp)              #*Match the protocol
(?:\ *[0-9]*){2}                # Match the Recv/Send-Q
\ *                             # Space before local address
(?:0\.){3}0                     # The local address must be 0.0.0.0
:                               # The colon before the port
(?P<port>[0-9]*)                #*The local port
\ *                             # Space before foreign address
(?:[0-9]{1,3}\.){3}[0-9]{1,3}   # The forign address
:                               # The colon before the port
(?:\*|[0-9]*)                   # The foreign port
\ *[A-Z]*                       # The connection state
\ *%d/                          #*The application PID
"""
def print_notify(action, proto, port, completed=True):
    """
    Send status to client.
    """
    sys.stdout.write("%s %s %d %d\n" % (action, proto, port, completed))
    sys.stdout.flush()
   
def get_open_ports(port_finder):
    """
    List open ports using the port_finder re.
    """
    ports_new = set ()
    netstat = Popen(NETSTAT_CMD.split(), stdout = PIPE)
    netstat.wait()
    netstat_ports = port_finder(netstat.communicate()[0])
    for port in netstat_ports:
        ports_new.add((port[0], int (port[1])))
    return ports_new

def update_ports(port_finder, app_path):
    """
    Cycle
    """
    ports_new = get_open_ports(port_finder)
    if not ports_new:
        return
    ports_new.intersection_update(ALLOWED_APPS[app_path])
    if not ports_new:
        return
    to_open = ports_new - PORTS
    to_close = PORTS - ports_new
    if to_open or to_close:
        update_firewall(to_open, to_close)
       
def sub_list(list2, list1):
    """
    Subtract list2 from list1
    """
    list_new = list()
    for item in list1:
        if item not in list2:
            list_new.append(item)
    return list_new
    
def update_firewall(to_open=None, to_close=None):
    """
    Update Firewall Rules
    """
    if to_open:
        for port in to_open:
            cmd = OPEN_CMD.format(proto = port[0], dport = port[1])
            iptables = Popen(cmd.split(), stdout = PIPE)
            iptables.wait()
            if iptables.poll() == 0:
                print_notify("open", port[0], port[1], True)
                PORTS.add(port)
            else:
                print_notify("open", port[0], port[1], False)
    if to_close:
        for port in to_close:
            cmd = CLOSE_CMD.format(proto = port[0], dport = port[1])
            iptables = Popen(cmd.split(), stdout = PIPE)
            iptables.wait()
            if iptables.poll() == 0:
                print_notify("close", port[0], port[1], True)
                PORTS.discard(port)
            else:
                print_notify("close", port[0], port[1], False)

def main_function():
    """
    Main Thread
    """
    app_pid = int(sys.argv[1])
    netstat_pattern = NETSTAT_PATTERN % app_pid
    port_finder = re.compile(netstat_pattern, re.VERBOSE).findall
    proc_path = os.path.join("/proc", str(app_pid))
    app_path = os.path.realpath(os.path.join(proc_path, "exe"))
    try:
        while not PORTS:
            update_ports(port_finder, app_path)
            sleep(2)
        while os.path.exists(proc_path):
            sleep(20)
            update_ports(port_finder, app_path)
    finally:
        update_firewall(to_close=PORTS.copy())
        sys.exit(0)

def parse_config():
    """
    Parse the configuration file and return a list of allowed applications.
    """
    allowed_apps = {}
    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)
    for program in config.sections():
        allowed_apps[program] = set ([ 
            tuple ([
                port.split('/')[1],
                int (port.split('/')[0])
            ]) for port in config.get(program,"ports").split()
        ])
    return allowed_apps

if __name__ == "__main__":
    ALLOWED_APPS = parse_config()
    PORTS = set ()
    main_function()
