#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from .colorPrint import ColorPrint
import logging

class LogHelper():
    HEADER = ColorPrint.HEADER
    OKBLUE = ColorPrint.OKBLUE
    OKGREEN = ColorPrint.OKGREEN
    WARNING = ColorPrint.WARNING
    FAIL = ColorPrint.FAIL
    ENDC = ColorPrint.ENDC
    BOLD = ColorPrint.BOLD
    UNDERLINE = ColorPrint.UNDERLINE
    CRITICAL = logging.CRITICAL
    FATAL = logging.FATAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = logging.WARN
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET
    
    def __init__(self, logfilename=None, name='default', screenlevel=logging.INFO, filelevel=logging.DEBUG):
        self.logfilename = logfilename if logfilename else 'default.log'
        self.name = name
        self.screenlevel = screenlevel
        self.filelevel = filelevel
        # logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        # file handler
        self.fh = logging.FileHandler(self.logfilename)
        self.fh.setLevel(self.filelevel)
        self.fh.setFormatter(logging.Formatter('%(asctime)s|%(levelname)s|PID(%(process)d) - %(message)s'))
        # stream handler
        self.sh = logging.StreamHandler()
        self.sh.setLevel(self.screenlevel)
        self.sh.setFormatter(logging.Formatter('%(message)s'))
        
    def debugPrint(self, msg):
        # message for stream handler
        smsg = '[DEBUG] %s' % (msg)
        self.logger.addHandler(self.fh)
        self.logger.debug(msg)
        self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.sh)
        self.logger.debug(smsg)
        self.logger.removeHandler(self.sh)        

    def errorPrint(self, msg):
        # message for stream handler
        smsg = '%s %s' % (ColorPrint('[ERROR]', ColorPrint.FAIL), msg)
        self.logger.addHandler(self.fh)
        self.logger.error(msg)
        self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.sh)
        self.logger.error(smsg)
        self.logger.removeHandler(self.sh)

    def warnPrint(self, msg):
        # message for stream handler
        smsg = '%s %s' % (ColorPrint('[WARN]', ColorPrint.WARNING), msg)
        self.logger.addHandler(self.fh)
        self.logger.warn(msg)
        self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.sh)
        self.logger.warn(smsg)
        self.logger.removeHandler(self.sh)
            
    def infoPrint(self, msg, style=None):
        # message for stream handler
        smsg = '%s %s' % (ColorPrint('[INFO]', style), msg) if style else '[INFO] %s' % msg
        self.logger.addHandler(self.fh)
        self.logger.info(msg)
        self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.sh)
        self.logger.info(smsg)
        self.logger.removeHandler(self.sh)
        
    def p(self, msg, loglevel='DEBUG', noln=False):
        funcname = loglevel.lower() + 'Print'
        getattr(self, funcname)(msg)

