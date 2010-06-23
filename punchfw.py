#!/usr/bin/python
import pynotify
import sys
import os
import subprocess
from time import sleep

def getAppPath():
    """
    Get the path to the application
    """
    return sys.argv[1]        

def getAppName():
    """
    Get the name of the application
    """
    return os.path.basename(sys.argv[1]).capitalize()

def getAppArgs():
    """
    Get application's arguments
    """
    app_args = list()
    for i in range(1, len(sys.argv)):
        app_args.append(sys.argv[i])
    return app_args

def printNotify(app, action, proto, port, completed=True):
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
    
def forkWatcher(app_pid, app_name):
    """
    Fork the watcher process and run the helper
    This does all of the actual work
    """
    watcher_pid = os.fork()
    if watcher_pid == 0:
        watcher = subprocess.Popen(["sudo", "/usr/local/sbin/punchfw-helper.py", str(app_pid)], executable="/usr/bin/sudo", stdout=subprocess.PIPE)
        #watcher = subprocess.Popen(["/bin/ping", "google.com"], stdout=subprocess.PIPE)
        #watcher = subprocess.Popen(["/home/steb/Desktop/punchfw-helper.py", str(app_pid)], stdout=subprocess.PIPE)
        try:
            while watcher.poll() is None:
                watcher_out = watcher.stdout.readline().split(' ')
                action = watcher_out[0]
                proto = watcher_out[1]
                port = int(watcher_out[2])
                completed = bool(watcher_out[3])
                printNotify(app_name, action, proto, port, completed)
        except KeyboardInterrupt:
            watcher_out = watcher.stdout.readlines()
            print watcher_out
            for line in watcher_out:
                parts = line.split(' ')
                action = parts[0]
                proto = parts[1]
                port = int(parts[2])
                completed = bool(parts[3])
                printNotify(app_name, action, proto, port, completed) 
            watcher.wait()
        sys.exit(0)
        return 0
    else:
        return watcher_pid

    
def runApp(app_path, app_args):
    """
    Run the Application
    """
    try:
        os.execvp(app_path, app_args)
    except:
        return False
def main_function():
    """
    Main Thread
    """
    pynotify.init("PunchFW")
    app_path = getAppPath()
    app_args = getAppArgs()
    app_name = getAppName()
    watcher_pid = forkWatcher(os.getpid(), app_name)
    if not runApp(app_path, app_args):
        os.kill(watcher_pid, 15)
    sys.exit(0)
    
if __name__ == "__main__":
    if not os.path.exists("/etc/punchfw.cfg"):
        print "You need to create a configuration file"
        exit(1)
    main_function()
