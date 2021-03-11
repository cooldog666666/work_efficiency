#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import base64
import sys
import logging
from functools import wraps
from queue import Queue
import subprocess
import shlex


class LogHelper(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __init__(self, log_file_name=None, name='default', screen_level=logging.INFO, file_level=logging.DEBUG,
                 file_handler=False):
        self.log_file_name = log_file_name if log_file_name else 'default.log'
        self.name = name
        self.screen_level = screen_level
        self.file_level = file_level
        self.fileHandler = file_handler
        # logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        if self.fileHandler:
            # file handler
            self.fh = logging.FileHandler(log_file_name)
            self.fh.setLevel(self.file_level)
            self.fh.setFormatter(logging.Formatter('*%(asctime)s|%(levelname)s|PID%(process)d - %(message)s'))
        # stream handler
        self.shout = logging.StreamHandler(stream=sys.stdout)
        self.shout.setLevel(self.screen_level)
        self.shout.setFormatter(logging.Formatter('%(message)s'))
        self.sherr = logging.StreamHandler()
        self.sherr.setLevel(self.screen_level)
        self.sherr.setFormatter(logging.Formatter('%(message)s'))

    def debug_print(self, msg):
        if type(msg) is bytes:
            msg = msg.decode()
        smsg = '[DEBUG] %s' % msg
        if self.fileHandler:
            self.logger.addHandler(self.fh)
            self.logger.debug(smsg)
            self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.shout)
        self.logger.debug(smsg)
        self.logger.removeHandler(self.shout)

    def error_print(self, msg):
        if type(msg) is bytes:
            msg = msg.decode()
        smsg = '{}[ERROR]{} {}'.format(LogHelper.FAIL, LogHelper.ENDC, msg)
        if self.fileHandler:
            self.logger.addHandler(self.fh)
            self.logger.error(smsg)
            self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.sherr)
        self.logger.error(smsg)
        self.logger.removeHandler(self.sherr)

    def warn_print(self, msg):
        if type(msg) is bytes:
            msg = msg.decode()
        smsg = '{}[WARN]{} {}'.format(LogHelper.WARNING, LogHelper.ENDC, msg)
        if self.fileHandler:
            self.logger.addHandler(self.fh)
            self.logger.warn(smsg)
            self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.shout)
        self.logger.warn(smsg)
        self.logger.removeHandler(self.shout)

    def info_print(self, msg, style=OKGREEN):
        if type(msg) is bytes:
            msg = msg.decode()
        smsg = '{}[INFO]{} {}'.format(style, LogHelper.ENDC, msg) if style else '[INFO] %s' % msg
        if self.fileHandler:
            self.logger.addHandler(self.fh)
            self.logger.info(smsg)
            self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.shout)
        self.logger.info(smsg)
        self.logger.removeHandler(self.shout)

    def p(self, msg, log_level='DEBUG'):
        func_name = log_level.lower() + '_print'
        getattr(self, func_name)(msg)

    def print(self, msg):
        if type(msg) is bytes:
            msg = msg.decode()
        smsg = '[PRINT] %s' % msg
        print(msg)
        if self.fileHandler:
            self.logger.addHandler(self.fh)
            self.logger.info(smsg)
            self.logger.removeHandler(self.fh)
# set default log instance
log = LogHelper()


def die(msg, ret=1):
    log.error_print(msg)
    sys.exit(ret)


class CommandString(object):
    def __init__(self, cmd=None, input_msg='', timeout=99999, check_return=True, return_content=''):
        self.cmd = cmd
        self.check_return = check_return
        self.return_content = return_content
        self.input_msg = input_msg
        self.timeout = timeout


def executor():
    def deco(func):
        @wraps(func)
        def wrapper(*arg, **args):
            f = func(*arg, **args)
            result_queue = Queue()
            result_queue.put(None)
            while True:
                result = result_queue.get()
                try:
                    # yield CommandString(<command string>) will generate an CommandString obj
                    cmd_str = f.send(result)
                    # if return_content is not None, deco will return the content directly
                    # only this way func can return something directly
                    if cmd_str.return_content:
                        return cmd_str.return_content
                    cmd = cmd_str.cmd
                    log.p('[RUN] {!r}'.format(cmd))
                    process = subprocess.Popen(shlex.split(cmd),
                                               stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)
                    process.stdin.write(cmd_str.input_msg.encode())
                    out, err = process.communicate(timeout=cmd_str.timeout)
                    ret = process.returncode
                    log.p('[RUN] {!r} complete ({})'.format(cmd, ret))
                    if cmd_str.check_return and ret != 0:
                        log.error_print(err)
                        sys.exit(ret)
                    result_queue.put((ret, out, err))
                except StopIteration:
                    break
        return wrapper
    return deco


@executor()
def main():
    hostname = 'eos2git.cec.lab.emc.com'
    artifactory_protocol = 'https'
    artifactory_host = 'amaas-mr-mw1.cec.lab.emc.com'

    try:
        user = os.environ['CORPUSER']
        passwd = os.environ['CORPPASSWD']
        passwd = base64.b64decode(passwd).decode()
        log.info_print('Try git login for %s ...' % user)
        yield CommandString('git credential approve',
                            input_msg='protocol=https\nhost={}\nusername={}\npassword={}\n\n'.format(
                                hostname, user, passwd
                            ))
        yield CommandString('git credential approve',
                            input_msg='protocol={}\nhost={}\nusername={}\npassword={}\n\n'.format(
                                artifactory_protocol, artifactory_host, user, passwd
                            ))
    except KeyError as err:
        die('Key {!r} unset.'.format(err.__context__.decode()))


if __name__ == '__main__':
    main()
