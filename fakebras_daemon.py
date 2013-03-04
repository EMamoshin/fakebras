#!/usr/bin/python

import sys
import time
import threading
import Queue
import os
#from signal import SIGTERM
sys.path.append("/opt/redis_methods")
from daemon import Daemon
from fakebras import FakeBras
from logger import BrasLogger

"""
create FakeBras
create_thread (count)
and ever 1 sec check on FakeBras
"""

class FakeBrasDaemon(Daemon):
    def run(self):
        fb = FakeBras(logger_handler=self.logger)
        while True:
            try:
                fb.check_ip_without_status()
                time.sleep(1)
            except KeyboardInterrupt:
                print 'Ctrl+C pushed! Process ...'
                fb.stop_threads()
                # killed process for debug
                import subprocess, signal
                p = subprocess.Popen(['ps', 'a'], stdout=subprocess.PIPE)
                out, err = p.communicate()
                for line in out.splitlines():
                    if 'fakebras_daemon.py' in line:
                        pid = int(line.split(None, 1)[0])
                        os.kill(pid, signal.SIGKILL)
    
if __name__ == "__main__":
    # Create logger object
    logger_handler = BrasLogger()
    # Create FakeBrasDaemon
    daemon = FakeBrasDaemon(pidfile='/tmp/daemon-fakebras.pid', logger_handler=logger_handler)
    
    # Options
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'fg' == sys.argv[1]:
            daemon.run()
        else:
            print "Unknown command"
            sys.exit(2)
        #sys.exit(0)
    else:
        print "usage: %s start|stop|restart|fg" % sys.argv[0]
        sys.exit(2)
