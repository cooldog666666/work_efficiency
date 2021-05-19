#!/usr/bin/env python
# -*- coding: UTF-8 -*-

class ColorPrint():
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'    
    def __init__(self, msg, style=ENDC, noln=False):
        self.msg = msg
        self.style = style
        self.noln = noln
    def p(self):
        if self.noln:
            print('''%s%s%s''' % (self.style, self.msg, ColorPrint.ENDC), end=' ')
        else:
            print('''%s%s%s''' % (self.style, self.msg, ColorPrint.ENDC))
    def __str__(self):
        return '''%s%s%s''' % (self.style, self.msg, ColorPrint.ENDC)
    __repr__ = __str__