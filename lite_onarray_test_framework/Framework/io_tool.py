from Framework.setup_testsuite import *
from Framework.component import *

import re
import os

##############################################################################
# Module Variable
##############################################################################

LOG = ExecuteLog('io_tool', LOG_LEVEL, testlog)


##############################################################################
# Common Function
##############################################################################

# def ensure_action_succeed_decorator(func):
#     def wrapper(*args, **kwargs):
#         step_str, output, return_code, check_output = func(*args, **kwargs)
#
#         # make sure it succeed
#         if return_code != 0:
#             LOG.print_log('ERROR', 'Failed to {} !'.format(step_str))
#             assert False, "[Assert Error] Failed to {} !".format(step_str)
#
#         # check output if needed
#         if check_output and type(check_output) is str:
#             m = re.search(check_output, output)
#             assert m is not None, "[Assert Error] Failed to get {} in output!".format(check_output)
#
#     return wrapper


# @ensure_action_succeed_decorator
# def run_command_on_host(iohost_obj, command, step_str=None, check_output=None, background=False):
#     if step_str is None:
#         step_str = 'Run command {}...'.format(command)
#     LOG.print_log('INFO', step_str)
#
#     output, return_code = iohost_obj.HOST_EC.host_runcmd(command, background)
#     LOG.print_log('INFO', "output is:\n")
#     LOG.print_plain_log('INFO', output)
#     LOG.print_log('INFO', "exit status is:{}.".format(return_code))
#
#     return step_str, output, return_code, check_output


##############################################################################
# IO Tool Class
##############################################################################

class VDBench():

    def __init__(self, io_host, thread_name=None):
        assert type(io_host) is LinuxHost, "[Assert Error] IO host should be a Linux host!"
        assert type(io_host.vdbench_path) is str and len(io_host.vdbench_path) > 0, "[Assert Error] IO host vdbench path is invalid!"

        self.io_host = io_host
        if thread_name is None:
            self.LOG = LOG
        else:
            assert type(thread_name) is str and len(thread_name) > 0 and not thread_name.isspace(), \
                "[Assert Error] The input thread_name {} is invalid!".format(thread_name)
            self.LOG = ExecuteLog('io_tool', LOG_LEVEL, testlog, thread_name=thread_name)

        self.vdbench_rsh_log = 'vdbench_rsh.log'
        self.enter_vdbench_path = 'cd {}; '.format(self.io_host.vdbench_path)

    def vdbench_prepare_vdb_file_for_device(self, device_size, origin_vdb_file, updated_vdb_file):
        """
        :param device_size: int in GB
        :param origin_vdb_file: str
        :param updated_vdb_file: str
        :return:
        """
        assert type(device_size) is int, "[Assert Error] Input device_size:{} should be an int!".format(device_size)
        assert type(origin_vdb_file) is str, "[Assert Error] Input origin_vdb_file:{} should be a string!".format(origin_vdb_file)
        assert type(updated_vdb_file) is str, "[Assert Error] Input updated_vdb_file:{} should be a string!".format(updated_vdb_file)
        assert os.path.exists(origin_vdb_file), "[Assert Error] Input origin_vdb_file:{} does not exist!".format(origin_vdb_file)

        self.LOG.print_log('INFO', 'Find the device for disk which size is {}.'.format(device_size))
        device = None
        command = 'fdisk -lu'
        output, return_code = run_command_on_host_check_returncode(self.io_host, command, log_obj=self.LOG)
        m = re.findall(r'Disk\s+([/0-9a-z]+):\s+(\d+)\s+GiB', output)
        assert len(m) > 0, "[Assert Error] Failed to find any disk information!"

        for m_disk in m:
            if int(m_disk[1]) == device_size:
                device = str(m_disk[0])
                break
        assert device, "[Assert Error] Failed to find the disk with size {}!".format(device_size)

        self.LOG.print_log('INFO', 'Get the device {} for disk, update it into vdb file.'.format(device))
        with open(origin_vdb_file, 'r') as f:
            alllines = f.readlines()
        assert alllines and len(alllines) > 0, "[Assert Error] Failed to read the content of file {}!".format(origin_vdb_file)

        with open(updated_vdb_file, 'w+') as f:
            for line in alllines:
                self.LOG.print_log('INFO', 'Get line - {}'.format(line))
                newline = re.sub(r"(sd=workload.*,lun=)([/0-9a-z]+),", r"\1" + device + ',', line)
                self.LOG.print_log('INFO', 'Update this to new line - {}'.format(newline))
                f.writelines(newline)

        assert os.path.exists(updated_vdb_file), "[Assert Error] Updated updated_vdb_file:{} does not exist!".format(updated_vdb_file)
        return updated_vdb_file

    def vdbench_start_rsh_deamon(self):

        step_str = "Check vdbench rsh deamon on io host {}...".format(self.io_host.host_ip)
        self.LOG.print_log('INFO', step_str)

        def check_rsh_deamon():
            command = 'ps -ef | grep vdbench'
            output, return_code = run_command_on_host_check_returncode(self.io_host, command, log_obj=self.LOG)
            process = []
            m1 = re.search(r'root\s+(\d+).+vdbench rsh', output)
            m2 = re.search(r'root\s+(\d+).+java -client.+Vdbmain rsh', output)
            if m1 and m2:
                process.append(m1.group(1))
                process.append(m2.group(1))
                self.LOG.print_log('INFO', 'Get process {} and {} for vdbench daemon.'.format(process[0], process[1]))
            else:
                assert False, "[Assert Error] Need to start vdbench daemon process!"

            command = self.enter_vdbench_path + 'tail -1 {}'.format(self.vdbench_rsh_log)
            output, return_code = run_command_on_host_check_returncode(self.io_host, command, log_obj=self.LOG)
            m = re.search(r'(fail)|(error)', output, re.IGNORECASE)
            if m:
                self.LOG.print_log('INFO', 'Error or failure was found in {}, kill the current vdbench daemon process.'.format(self.vdbench_rsh_log))
                command = 'kill -9 {} {}'.format(process[0], process[1])
                run_command_on_host_check_returncode(self.io_host, command, log_obj=self.LOG)
                assert False, "[Assert Error] Need to start vdbench daemon process!"

        try:
            check_rsh_deamon()
        except AssertionError as err:
            if "Need to start vdbench daemon process" in str(err):
                command = self.enter_vdbench_path + 'nohup ./vdbench rsh > {} &'.format(self.vdbench_rsh_log)
                run_command_on_host(self.io_host, command, background=True, log_obj=self.LOG)
                check_rsh_deamon()
            else:
                assert False, str(err)

    def vdbench_send_workload_parameter_file(self, local_file_path, remote_file_path=None):
        if remote_file_path and type(remote_file_path) is str and len(remote_file_path) > 0:
            pass
        else:
            remote_file_path = self.io_host.vdbench_path + '/' + os.path.basename(local_file_path)

        step_str = "Send local vdb file {} to host {}:{}.".format(local_file_path, self.io_host.host_ip, remote_file_path)
        self.LOG.print_log('INFO', step_str)
        self.io_host.HOST_EC.host_scp_send(local_file_path, remote_file_path)

        step_str = "Change the access permission for file {}:{}.".format(self.io_host.host_ip, remote_file_path)
        self.LOG.print_log('INFO', step_str)
        command = 'chmod 755 ' + remote_file_path
        run_command_on_host(self.io_host, command, log_obj=self.LOG)

        return remote_file_path

    def vdbench_start_io_according_to_file(self, workload_parameter_file):

        step_str = "Start IO from host {} with following workload parameters:".format(self.io_host.host_ip)
        self.LOG.print_log('INFO', step_str)
        command = 'cat ' + workload_parameter_file
        run_command_on_host(self.io_host, command, log_obj=self.LOG)

        command = self.enter_vdbench_path + './vdbench -f ' + workload_parameter_file
        check_output = 'Vdbench execution completed successfully.'
        run_command_on_host(self.io_host, command, check_output=check_output, log_obj=self.LOG)

    def vdbench_init_and_start_io(self, updated_workload_parameter_file):

        self.vdbench_start_rsh_deamon()
        remote_workload_parameter_file = self.vdbench_send_workload_parameter_file(updated_workload_parameter_file)
        self.vdbench_start_io_according_to_file(remote_workload_parameter_file)


class CBFSIO():

    ALL_ZERO = '0x00000000'
    ALL_ONE = '0xFFFFFFFF'
    SECTORS_IN_BLOCK = 16

    start_cbfsio_tool = 'start_cbfsio.py'
    start_cbfsio_fullpath_local = './io_config_file/' + start_cbfsio_tool

    CBFSIO_LOG = ExecuteLog('CBFSIO', LOG_LEVEL, your_testsuite_testlog_dir + 'CBFSIO')
    assert isinstance(CBFSIO_LOG, ExecuteLog), "[Assert Error] CBFSIO_LOG should be a instance of class ExecuteLog!"

    def __init__(self, storage_obj, cbfs_obj, thread_name=None):
        assert type(storage_obj) is Storage, "[Assert Error] storage_obj {} should be a Storage!".format(storage_obj)
        assert type(cbfs_obj) is CBFS, "[Assert Error] cbfs_obj {} should be a CBFS!".format(cbfs_obj)

        self.storage_obj = storage_obj
        self.cbfs_obj = cbfs_obj
        self.fsid = self.cbfs_obj.fsid
        self.sp_owner = self.cbfs_obj.sp_owner

        self.pfdc_cmd = None

        if thread_name is None:
            self.LOG = LOG
            self.cbfsio_log = CBFSIO.CBFSIO_LOG
        else:
            assert type(thread_name) is str and len(thread_name) > 0 and not thread_name.isspace(), \
                "[Assert Error] The input thread_name {} is invalid!".format(thread_name)
            self.LOG = ExecuteLog('io_tool', LOG_LEVEL, testlog, thread_name=thread_name)
            self.cbfsio_log = ExecuteLog('CBFSIO', LOG_LEVEL, your_testsuite_testlog_dir + 'CBFSIO', thread_name=thread_name)

    def send_cbfsio_script_to_storage(self, local_file_path, storage_sp='both'):
        assert type(storage_sp) is str and storage_sp in ['spa', 'spb', 'both'], "[Assert Error] The input storage_sp must be spa or spb or both!"
        remote_file_path = './' + os.path.basename(local_file_path)

        def send_file_to_storage_sp(sp='spa'):
            assert type(sp) is str and sp in ['spa', 'spb'], "[Assert Error] The input sp must be spa or spb!"
            d_sp_ip = {'spa': self.storage_obj.spa_ip,
                       'spb': self.storage_obj.spb_ip}
            step_str = "Send cbfsio script {} to storage {} {}:{}.".format(local_file_path, sp, d_sp_ip[sp], remote_file_path)
            self.LOG.print_log('INFO', step_str)
            if sp == 'spa':
                self.storage_obj.STORAGE_EC.spa_scp_send(local_file_path, remote_file_path)
            elif sp == 'spb':
                self.storage_obj.STORAGE_EC.spb_scp_send(local_file_path, remote_file_path)

        if storage_sp == 'both':
            for sp in ['spa', 'spb']:
                send_file_to_storage_sp(sp)
        elif storage_sp == 'spa':
            send_file_to_storage_sp(sp='spa')
        elif storage_sp == 'spb':
            send_file_to_storage_sp(sp='spb')

        return remote_file_path

    def generate_cbfsio_cmd(self, inode_num, start_offset, end_offset, io_pattern):

        length = end_offset - start_offset + 1
        minOffset = self.SECTORS_IN_BLOCK * start_offset
        maxOffset = self.SECTORS_IN_BLOCK * (start_offset + length) - 1
        minLength = self.SECTORS_IN_BLOCK * length
        maxLength = minLength

        if io_pattern == self.ALL_ZERO or io_pattern == self.ALL_ONE:
            cbfsio_cmd = 'TestMluServiceApi.exe "cbfsio start fsid={} inum={} '.format(self.fsid, inode_num) + \
                         'minOffset={} maxOffset={} minLength={} maxLength={} '.format(minOffset, maxOffset, minLength,
                                                                                       maxLength) + \
                         'access=seq doIO=1 passes=1 isApiIO=1 operation=mfw ' + \
                         'time=0 numio=0 forcePatternWrite=1 usePatternFully=1 pattern={}"'.format(io_pattern)
        else:
            cbfsio_cmd = 'TestMluServiceApi.exe "cbfsio start fsid={} inum={} '.format(self.fsid, inode_num) + \
                         'minOffset={} maxOffset={} minLength={} maxLength={} '.format(minOffset, maxOffset, minLength,
                                                                                       maxLength) + \
                         'access=seq doIO=1 passes=1 isApiIO=1 operation=mfw ' + \
                         'minCompressWriteSpaceSavingPct=50 maxCompressWriteSpaceSavingPct=50 ' + \
                         'pattern={} pctDedup=100 dedupValidationPatterns=1"'.format(io_pattern)

        self.LOG.print_log('INFO', 'CBFSIO command is: {}'.format(cbfsio_cmd))
        return cbfsio_cmd

    def send_cbfsio(self, cbfsio_cmd):
        step_str = 'Send cbfsio...'
        output, return_code = run_command_on_storage_check_returncode(
            self.storage_obj, cbfsio_cmd, step_str=step_str, sp_owner=self.sp_owner, log_obj=self.cbfsio_log)
        assert "Command succeeded" in output, "[Assert Error] Failed to get Command succeeded when do cbfsio!"

    def generate_pfdc_cmd(self):
        pfdc_cmd = 'TestMluServiceApi.exe "pfdc_dl flush fsid={}"'.format(self.fsid)
        self.pfdc_cmd = pfdc_cmd

        self.LOG.print_log('INFO', 'PFDC command is: '.format(pfdc_cmd))
        return self.pfdc_cmd

    def flush_pfdc(self):
        step_str = 'Flush PFDC...'
        output, return_code = run_command_on_storage_check_returncode(
            self.storage_obj, self.pfdc_cmd, step_str=step_str, sp_owner=self.sp_owner, log_obj=self.cbfsio_log)
        assert "Command succeeded" in output, "[Assert Error] Failed to get Command succeeded when flush pfdc!"

    def start_cbfsio(self, inode_num, start=16, each_pt_length=8, ondisk_datasize_mb=4, start_io_pattern='10000000'):

        assert type(inode_num) is str and len(inode_num) > 0 and inode_num.isdigit(), \
            "[Assert Error] The input inode_num {} is invalid!".format(inode_num)
        assert type(start) is int and start > 0, \
            "[Assert Error] The input inode_num {} is invalid!".format(inode_num)
        assert type(each_pt_length) is int and each_pt_length > 0, \
            "[Assert Error] The input each_pt_length {} is invalid!".format(each_pt_length)
        assert type(ondisk_datasize_mb) is int and ondisk_datasize_mb > 0 and ondisk_datasize_mb % 4 == 0, \
            "[Assert Error] The input ondisk_datasize_mb {} is invalid!".format(ondisk_datasize_mb)
        assert type(start_io_pattern) is str and len(start_io_pattern) == 10 and re.match(r'[0-9A-Fa-fxX]+$', start_io_pattern), \
            "[Assert Error] The input start_io_pattern {} is invalid!".format(start_io_pattern)

        # with each 4MB data on-disk, there are 1024 ILC MP in leafIB
        mp_num = 1024 * ondisk_datasize_mb // 4
        pt_num = mp_num // each_pt_length

        self.LOG.print_log('INFO', 'Start CBFSIO to fsid = {}, inode_num = {}...'.format(self.fsid, inode_num))
        self.LOG.print_plain_log('INFO', 'Start offset: {}'.format(start))
        self.LOG.print_plain_log('INFO', 'Each pattern length: {}'.format(each_pt_length))
        self.LOG.print_plain_log('INFO', 'On disk datasize: {} MB'.format(ondisk_datasize_mb))
        self.LOG.print_plain_log('INFO', 'Total MP number: {}'.format(mp_num))
        self.LOG.print_plain_log('INFO', 'Total pattern number: {}'.format(pt_num))
        self.LOG.print_plain_log('INFO', 'Start IO pattern: 0x{}'.format(start_io_pattern))

        for i in range(0, pt_num):
            start_offset = start + i * each_pt_length
            end_offset = start_offset + each_pt_length - 1
            io_pattern = str(hex(int(start_io_pattern, 16) + i))

            self.LOG.print_log('INFO', 'Send CBFSIO with parameters fsid = {}, inode_num = {}, start_offset = {}, end_offset = {}, io_pattern = {}.'
                               .format(self.fsid, inode_num, start_offset, end_offset, io_pattern))
            cbfsio_cmd = self.generate_cbfsio_cmd(inode_num, start_offset, end_offset, io_pattern)
            self.send_cbfsio(cbfsio_cmd)

        self.LOG.print_log('INFO', 'Flush PFDC for fsid {}.'.format(self.fsid))
        self.flush_pfdc()

    def start_cbfsio_on_storage_sp(self, inode_num, start=16, each_pt_length=8, ondisk_datasize_mb=4, start_io_pattern='0x10000000'):

        assert type(inode_num) is str and len(inode_num) > 0 and inode_num.isdigit(), \
            "[Assert Error] The input inode_num {} is invalid!".format(inode_num)
        assert type(start) is int and start > 0, \
            "[Assert Error] The input inode_num {} is invalid!".format(inode_num)
        assert type(each_pt_length) is int and each_pt_length > 0, \
            "[Assert Error] The input each_pt_length {} is invalid!".format(each_pt_length)
        assert type(ondisk_datasize_mb) is int and ondisk_datasize_mb > 0 and ondisk_datasize_mb % 4 == 0, \
            "[Assert Error] The input ondisk_datasize_mb {} is invalid!".format(ondisk_datasize_mb)
        assert type(start_io_pattern) is str and len(start_io_pattern) == 10 and re.match(r'[0-9A-Fa-fxX]+$', start_io_pattern), \
            "[Assert Error] The input start_io_pattern {} is invalid!".format(start_io_pattern)

        def tool_exist_on_sp(sp='spa'):
            cmd = 'ls ' + self.start_cbfsio_tool
            try:
                run_command_on_storage_check_returncode(self.storage_obj, cmd, sp_owner=sp, log_obj=self.LOG)
            except AssertionError as err:
                self.LOG.print_log('WARNING', 'Run command - {} with error:\n{}'.format(cmd, str(err)))
                return False
            else:
                return True

        if not tool_exist_on_sp(sp=self.sp_owner):
            local_file_path = self.start_cbfsio_fullpath_local
            self.send_cbfsio_script_to_storage(local_file_path, storage_sp=self.sp_owner)
            assert tool_exist_on_sp(sp=self.sp_owner), "[Assert Error] Still failed to get {} on {}!".format(self.start_cbfsio_tool, self.sp_owner)

        prefix_cmd = 'python ' + self.start_cbfsio_tool + ' '
        args_cmd = '--fsid {} --inode_num {} --start {} --each_io_length {} --ondisk_datasize_mb {} --start_io_pattern {}' \
                   .format(self.fsid, inode_num, start, each_pt_length, ondisk_datasize_mb, start_io_pattern)
        start_cbfsio_cmd = prefix_cmd + args_cmd
        run_command_on_storage_check_returncode(self.storage_obj, start_cbfsio_cmd, sp_owner=self.sp_owner, log_obj=self.LOG)






