#!/usr/bin/python
"""
Punches holes in the firewall for punchfw.
"""
import os
import sys
from subprocess import Popen, PIPE
from time import sleep
import configparser

CONFIG_FILE = "/etc/punchfw.cfg"
OPEN_CMD = "/usr/sbin/iptables -A INPUT -p {proto} --dport {dport} -j ACCEPT"
CLOSE_CMD = "/usr/sbin/iptables -D INPUT -p {proto} --dport {dport} -j ACCEPT"
LSOF_CMD = "lsof -p {pid} -a -i -Pln -FPn"

def print_notify(action, proto, port, completed=True):
    """
    Send status to client.
    """
    sys.stdout.write("%s %s %d %d\n" % (action, proto, port, completed))
    sys.stdout.flush()
   
def get_open_ports(lsof_cmd):
    """
    List open ports using the port_finder re.
    """
    ports_new = set()
    lsof = Popen(lsof_cmd.split(), stdout=PIPE, stderr=PIPE)
    lsof.wait()
    for line in lsof.communicate()[0].splitlines():
        if line[0] == 'P':
            proto = line[1:].lower()
        elif line[:2] == 'n*':
            try:
                port = int(line[3:])
            except ValueError:
                continue
            ports_new.add((proto, port))
    return ports_new

def update_ports(lsof_cmd, allowed_ports):
    """
    Cycle
    """
    ports_new = get_open_ports(lsof_cmd)
    if not ports_new:
        return
    ports_new.intersection_update(allowed_ports)
    if not ports_new:
        return
    to_open = ports_new - PORTS
    to_close = PORTS - ports_new

    for port in to_open:
        status = fw_open(port)
        print_notify("open", port[0], port[1], status)
    for port in to_close:
        status = fw_close(port)
        print_notify("close", port[0], port[1], status)

def fw_open(port):
    """
    Close a port
    """
    cmd = OPEN_CMD.format(proto = port[0], dport = port[1])
    iptables = Popen(cmd.split(), stdout = PIPE, stderr = PIPE)
    iptables.wait()
    if iptables.poll() == 0:
        PORTS.add(port)
        return True
    else:
        return False

def fw_close(port):
    """
    Close a port
    """
    cmd = CLOSE_CMD.format(proto = port[0], dport = port[1])
    iptables = Popen(cmd.split(), stdout = PIPE)
    iptables.wait()
    if iptables.poll() == 0:
        PORTS.discard(port)
        return True
    else:
        return False

def main_function():
    """
    Main Thread
    """
    app_pid = int(sys.argv[1])
    lsof_cmd = LSOF_CMD.format(pid=app_pid)
    proc_path = os.path.join("/proc", str(app_pid))
    app_path = os.path.realpath(os.path.join(proc_path, "exe"))
    allowed_ports = ALLOWED_APPS[app_path]
    try:
        while not PORTS:
            update_ports(lsof_cmd, allowed_ports)
            sleep(2)
        while os.path.exists(proc_path):
            sleep(20)
            update_ports(lsof_cmd, allowed_ports)
    finally:
        for port in PORTS.copy():
            status = fw_close(port)
            print_notify("close", port[0], port[1], status)
        sys.exit(0)

def parse_config():
    """
    Parse the configuration file and return a list of allowed applications.
    """
    allowed_apps = {}
    config = configparser.RawConfigParser()
    config.read(CONFIG_FILE)
    for program in config.sections():
        allowed_apps[program] = set([ 
            tuple([
                port.split('/')[1],
                int(port.split('/')[0])
            ]) for port in config.get(program,"ports").split()
        ])
    return allowed_apps

if __name__ == "__main__":
    ALLOWED_APPS = parse_config()
    PORTS = set()
    main_function()
