from Framework.setup_testsuite import *

import threading
import time
import random

##############################################################################
# Module Variable
##############################################################################

LOG = ExecuteLog('threads', LOG_LEVEL, testlog, thread_name='Main')

##############################################################################
# Thread Class
##############################################################################

class MyThread(threading.Thread):
    def __init__(self, task_function, task_args=(), is_daemon=False, name=None):
        self.task_function = task_function
        self.task_args = task_args
        self.is_daemon = is_daemon
        self.thread_name = None

        self.stop_thread = False
        self._stop_event = threading.Event()

        if name is not None:
            assert type(name) is str and len(name) > 0 and not name.isspace(), \
                "[Assert Error] The input thread name is invalid!"
            self.thread_name = "Thread-" + name

        if self.thread_name is None:
            threading.Thread.__init__(self, target=self.task_function, args=self.task_args, daemon=self.is_daemon)
            self.thread_name = self.name
        else:
            threading.Thread.__init__(self, target=self.task_function, args=self.task_args, daemon=self.is_daemon, name=self.thread_name)

        self.LOG = ExecuteLog('threads', LOG_LEVEL, testlog, thread_name=self.thread_name)
        self.LOG.print_log('INFO', "Thread name is :" + self.thread_name)

    def run(self):
        self.LOG.print_log('INFO', "Run thread {}...".format(self.thread_name))
        self.task_function(*self.task_args, self.thread_name)

    def join(self, timeout=None):
        self.LOG.print_log('INFO', "Thread {} is joined.".format(self.thread_name))
        threading.Thread.join(self, timeout)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def check_thread_alive(self):
        assert self.is_alive(), "[Assert Error] The thread {} is not alive!".format(self.thread_name)
        self.LOG.print_log('INFO', "Thread {} is alive.".format(self.thread_name))

    def check_thread_not_alive(self):
        assert not self.is_alive(), "[Assert Error] The thread {} is still alive!".format(self.thread_name)
        self.LOG.print_log('INFO', "Thread {} is not alive.".format(self.thread_name))


if __name__ == "__main__":
    pass
