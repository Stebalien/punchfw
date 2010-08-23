#!/usr/bin/python
"""
Runs a program and opens ports as needed and allowed by the
configuration file.
"""
import pynotify
import sys
import os
import subprocess

CONFIG_FILE = "/etc/punchfw.cfg"
SUDO_PATH = "/usr/bin/sudo"
HELPER_PATH = "/usr/local/sbin/punchfw_helper.py"


def get_app_path():
    """
    Get the path to the application
    """
    return sys.argv[1]        

def get_app_name():
    """
    Get the name of the application
    """
    return os.path.basename(sys.argv[1]).capitalize()

def get_app_args():
    """
    Get application's arguments
    """
    app_args = list()
    for i in range(1, len(sys.argv)):
        app_args.append(sys.argv[i])
    return app_args

def print_notify(app, action, proto, port, completed=True):
    """
    Send a notification to the notifications daemon of an opened/closed port
    """
    if completed:
        notice = "%s: %d/%s %sed" % (app, port, proto, action[0:4])
    else:
        notice = "%s: %d/%s NOT %sed" % (app, port, proto, action[0:4])
    notification = pynotify.Notification("Firewall", notice, "gufw_menu")
    notification.set_hint_string("x-canonical-append", "")
    notification.show()
    
def fork_watcher(app_pid, app_name):
    """
    Fork the watcher process and run the helper
    This does all of the actual work
    """
    watcher_pid = os.fork()
    if watcher_pid == 0:
        cmd = [SUDO_PATH, HELPER_PATH, str(app_pid)]
        watcher = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        try:
            while watcher.poll() is None:
                watcher_out = watcher.stdout.readline()[:-1].split(' ')
                if not watcher_out[0]:
                    break
                action = watcher_out[0]
                proto = watcher_out[1]
                port = int(watcher_out[2])
                completed = bool(watcher_out[3])
                print_notify(app_name, action, proto, port, completed)
        except KeyboardInterrupt:
            watcher_out = watcher.stdout.readlines()
            for line in watcher_out:
                parts = line.split(' ')
                action = parts[0]
                proto = parts[1]
                port = int(parts[2])
                completed = bool(parts[3])
                print_notify(app_name, action, proto, port, completed) 
            watcher.wait()
        sys.exit(0)
        return 0
    else:
        return watcher_pid

    
def run_app(app_path, app_args):
    """
    Run the Application
    """
    try:
        os.execvp(app_path, app_args)
    except OSError:
        return False
def main_function():
    """
    Main Thread
    """
    pynotify.init("PunchFW")
    app_path = get_app_path()
    app_args = get_app_args()
    app_name = get_app_name()
    watcher_pid = fork_watcher(os.getpid(), app_name)
    if not run_app(app_path, app_args):
        os.kill(watcher_pid, 15)
    sys.exit(0)
    
if __name__ == "__main__":
    if not os.path.exists(CONFIG_FILE):
        print "You need to create a configuration file"
        exit(1)
    main_function()
