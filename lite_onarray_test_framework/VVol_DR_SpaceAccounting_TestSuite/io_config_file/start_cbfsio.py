import subprocess
import sys
import os
import re
import time
import logging
import argparse

##############################################################################
# Parse Arguments
##############################################################################

# Create the parser
my_parser = argparse.ArgumentParser()

# Add the arguments
my_parser.add_argument('--fsid', type=str, action='store', help='the fsid to do cbfsio')
my_parser.add_argument('--inode_num', type=str, action='store', help='the inode to do cbfsio')
my_parser.add_argument('--start', type=int, action='store', default=16, help='the start offset to do cbfsio')
my_parser.add_argument('--each_io_length', type=int, action='store', default=8, help='the length for each io')
my_parser.add_argument('--ondisk_datasize_mb', type=int, action='store', default=4, help='the expect on-disk in MB size base on 50% compression ratio')
my_parser.add_argument('--start_io_pattern', type=str, action='store', default='0xAAAA0000', help='the first io pattern to write')

# Execute parse_args()
args = my_parser.parse_args()

print('# Check input arguments...')
print(vars(args))

# Input Arguments
fsid = args.fsid
inode_num = args.inode_num
start = args.start
each_io_length = args.each_io_length
ondisk_datasize_mb = args.ondisk_datasize_mb
start_io_pattern = args.start_io_pattern


##############################################################################
# Common Function
##############################################################################

class ExecuteLog():

    # Class attribute
    available_level = ['DEBUG', 'INFO']

    def __init__(self, session_name, level='INFO', log_file=None):
        assert level in self.available_level, "[Assert Error] The input log level is not invalid!"
        self.session_name = session_name
        self.level = level
        if log_file:
            self.log_file = log_file
        else:
            self.log_file = session_name + '_' + time.strftime('%Y%m%d_%H%M')

        # create logger
        self.logger = logging.getLogger(self.session_name)
        self.logger.setLevel(logging.INFO)
        if self.level == 'DEBUG':
            self.logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        # self.ch = logging.StreamHandler()
        self.ch = logging.FileHandler(self.log_file, mode='a')
        self.ch.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] %(message)s')

        # add formatter to ch
        self.ch.setFormatter(formatter)

        # add ch to logger
        self.logger.addHandler(self.ch)

        # ---------------------------------------------------------------------------------------
        # create plain logger
        self.plain_logger = logging.getLogger(self.session_name + '_plain_log')
        self.plain_logger.setLevel(logging.INFO)
        if self.level == 'DEBUG':
            self.plain_logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        self.plain_ch = logging.FileHandler(self.log_file, mode='a')
        self.plain_ch.setLevel(logging.DEBUG)

        # create formatter
        plain_formatter = logging.Formatter('%(message)s')

        # add formatter to ch
        self.plain_ch.setFormatter(plain_formatter)

        # add ch to logger
        self.plain_logger.addHandler(self.plain_ch)

    def print_log(self, level, msg):
        if level == 'DEBUG':
            self.logger.debug(msg)
        elif level == 'INFO':
            self.logger.info(msg)
        elif level == 'WARNING':
            self.logger.warning(msg)
        elif level == 'ERROR':
            self.logger.error(msg)
        elif level == 'CRITICAL':
            self.logger.critical(msg)

    def print_plain_log(self, level, msg):
        if level == 'DEBUG':
            self.plain_logger.debug(msg)
        elif level == 'INFO':
            self.plain_logger.info(msg)


class ExecuteCommand():

    def __init__(self):
        self.proc = None
        self.cmd = []
        self.output = ""
        self.error = ""
        self.return_code = None

    def execute_cmd(self, cmd):
        if type(cmd) is str:
            assert cmd != "" and not cmd.isspace(), "[Assert Error] Input cmd is str but invalid!"
            self.cmd = cmd
        elif type(cmd) is list:
            assert len(cmd) > 0, "[Assert Error] Input cmd is list but invalid!"
            self.cmd = cmd
        else:
            assert False, "[Assert Error] Input cmd only support str or list!"

        print("In execute_cmd, cmd is:")
        print(self.cmd)
        try:
            self.proc = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = self.proc.communicate()
            self.return_code = self.proc.returncode
        except:
            print("Failed to execute command - {}.".format(cmd))
            assert False, "[Assert Error] Failed to execute command - {}!".format(cmd)
        else:
            self.output = out.decode('utf-8')
            if err is not None:
                self.error = err.decode('utf-8')

        return self.output, self.error, self.return_code


def generate_cbfsio_cmd(fsid, inode_num, start_offset, end_offset, io_pattern):
    """
    :return:
    """
    ALL_ZERO = '0x00000000'
    ALL_ONE = '0xFFFFFFFF'
    SECTORS_IN_BLOCK = 16

    length = end_offset - start_offset + 1
    minOffset = SECTORS_IN_BLOCK * start_offset
    maxOffset = SECTORS_IN_BLOCK * (start_offset + length) - 1
    minLength = SECTORS_IN_BLOCK * length
    maxLength = minLength

    if io_pattern == ALL_ZERO or io_pattern == ALL_ONE:
        cbfsio_cmd = 'TestMluServiceApi.exe "cbfsio start fsid={} inum={} '.format(fsid, inode_num) + \
                     'minOffset={} maxOffset={} minLength={} maxLength={} '.format(minOffset, maxOffset, minLength, maxLength) + \
                     'access=seq doIO=1 passes=1 isApiIO=1 operation=mfw ' + \
                     'time=0 numio=0 forcePatternWrite=1 usePatternFully=1 pattern={}"'.format(io_pattern)
    else:
        cbfsio_cmd = 'TestMluServiceApi.exe "cbfsio start fsid={} inum={} '.format(fsid, inode_num) + \
                     'minOffset={} maxOffset={} minLength={} maxLength={} '.format(minOffset, maxOffset, minLength, maxLength) + \
                     'access=seq doIO=1 passes=1 isApiIO=1 operation=mfw ' + \
                     'minCompressWriteSpaceSavingPct=50 maxCompressWriteSpaceSavingPct=50 ' + \
                     'pattern={} pctDedup=100 dedupValidationPatterns=1"'.format(io_pattern)

    return cbfsio_cmd


def generate_flush_pfdc_cmd(fsid):
    pfdc_cmd = 'TestMluServiceApi.exe "pfdc_dl flush fsid={}"'.format(fsid)
    return pfdc_cmd


if __name__ == '__main__':

    # log
    LOG_LEVEL = 'DEBUG'
    log_file = 'cbfsio_' + time.strftime('%Y%m%d')
    print('\nFind logs in this file: {}.'.format(log_file))
    LOG_CBFSIO = ExecuteLog('CBFSIO', LOG_LEVEL, log_file)
    # EXECUTE
    ec_obj = ExecuteCommand()

    # # Input Arguments
    # fsid = '1073741852'
    # inode_num = '9429'
    # start_io_pattern = '90900000'
    # start = 16
    # each_io_length = 8
    # ondisk_datasize_mb = 256

    # io pattern
    ALL_ZERO = '0x00000000'
    ALL_ONE = '0xFFFFFFFF'
    ILPD = False
    if start_io_pattern == ALL_ZERO or start_io_pattern == ALL_ONE:
        ILPD = True

    # with each 4MB data on-disk, there are 1024 ILC MP in leafIB when 50% compression
    mp_num = 1024 * ondisk_datasize_mb // 4
    pt_num = mp_num // each_io_length

    assert type(inode_num) is str and len(inode_num) > 0 and inode_num.isdigit(), \
        "[Assert Error] The input inode_num {} is invalid!".format(inode_num)
    assert type(start) is int and start > 0, \
        "[Assert Error] The input inode_num {} is invalid!".format(inode_num)
    assert type(each_io_length) is int and each_io_length > 0, \
        "[Assert Error] The input each_pt_length {} is invalid!".format(each_io_length)
    assert type(ondisk_datasize_mb) is int and ondisk_datasize_mb > 0 and ondisk_datasize_mb % 4 == 0, \
        "[Assert Error] The input ondisk_datasize_mb {} is invalid!".format(ondisk_datasize_mb)
    assert type(start_io_pattern) is str and len(start_io_pattern) == 10 and re.match(r'[0-9A-Fa-fxX]+$', start_io_pattern), \
        "[Assert Error] The input start_io_pattern {} is invalid!".format(start_io_pattern)

    print('-' * 100)
    print('# Start CBFSIO to fsid = {}, inode_num = {}...'.format(fsid, inode_num))
    print('Start offset: {}'.format(start))
    print('Each pattern length: {}'.format(each_io_length))
    print('On disk datasize: {} MB'.format(ondisk_datasize_mb))
    print('Total MP number: {}'.format(mp_num))
    print('Total pattern number: {}'.format(pt_num))
    print('Start IO pattern: 0x{}'.format(start_io_pattern))
    print('-' * 100)
    #
    # for i in range(0, pt_num):
    #     start_offset = start + i * each_io_length
    #     end_offset = start_offset + each_io_length -1
    #     if ILPD:
    #         io_pattern = start_io_pattern
    #     else:
    #         # io_pattern = '0x' + str(int(start_io_pattern) + i)
    #         io_pattern = str(hex(int(start_io_pattern, 16) + 1))
    #
    #     LOG_CBFSIO.print_log('INFO', 'Start IO with parameters fsid = {}, inode_num = {}, start_offset = {}, end_offset = {}, io_pattern = {}.'
    #                          .format(fsid, inode_num, start_offset, end_offset, io_pattern))
    #     cbfsio_cmd = generate_cbfsio_cmd(fsid, inode_num, start_offset, end_offset, io_pattern)
    #     cmd = str(cbfsio_cmd)
    #     LOG_CBFSIO.print_log('INFO', 'Run command - {}'.format(cmd))
    #     output, err, return_code = ec_obj.execute_cmd(cmd)
    #     LOG_CBFSIO.print_plain_log('INFO', output)
    #     assert "Command succeeded" in output, "[Assert Error] Failed to get Command succeeded when do cbfsio!"
    #
    # LOG_CBFSIO.print_log('INFO', 'Flush PFDC to fsid = {}.'.format(fsid))
    # pfdc_cmd = generate_flush_pfdc_cmd(fsid)
    # cmd = str(pfdc_cmd)
    # LOG_CBFSIO.print_log('INFO', 'Run command - {}'.format(cmd))
    # output, err, return_code = ec_obj.execute_cmd(cmd)
    # LOG_CBFSIO.print_plain_log('INFO', output)
    # assert "Command succeeded" in output, "[Assert Error] Failed to get Command succeeded when flush pfdc!"
