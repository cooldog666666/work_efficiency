import subprocess
import sys
import os
import re
import time
import logging
import socket
from ssh2.session import Session


class ExecuteLog():

    # Class attribute
    available_level = ['DEBUG', 'INFO']

    def __init__(self, session_name, level='INFO', log_file=None, thread_name=None):
        assert level in self.available_level, "[Assert Error] The input log level is not invalid!"
        self.pre_session_name = session_name
        self.session_name = session_name
        self.level = level
        self.step_num = 0
        self.thread_name = thread_name

        if log_file:
            self.log_file = log_file
        else:
            #self.log_file = session_name + '_' + time.strftime('%Y%m%d_%H%M')
            self.log_file = session_name

        # create logger
        if self.thread_name:
            self.session_name += " [{}]".format(self.thread_name)
        self.logger = logging.getLogger(self.session_name)
        self.logger.setLevel(logging.INFO)
        if self.level == 'DEBUG':
            self.logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        # self.ch = logging.StreamHandler()
        self.ch = logging.FileHandler(self.log_file, mode='a')
        self.ch.setLevel(logging.DEBUG)

        # create formatter
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] %(message)s')

        # add formatter to ch
        self.ch.setFormatter(self.formatter)

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
        if self.thread_name:
            self.plain_formatter = logging.Formatter('{} [{}]\n%(message)s'.format(self.pre_session_name, self.thread_name))
        else:
            self.plain_formatter = logging.Formatter('%(message)s')

        # add formatter to ch
        self.plain_ch.setFormatter(self.plain_formatter)

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

    def print_step(self, msg):
        self.step_num += 1
        msg = '### STEP_{} ### '.format(self.step_num) + msg
        self.print_log('INFO', msg)


class ExecuteCommand():

    # class attribute
    # LOG = ExecuteLog('ExecuteCommand', 'DEBUG')
    LOG = None

    def __init__(self):
        self.proc = None
        self.cmd = []
        self.output = ""
        self.error = ""
        self.return_code = None

    def execute_cmd(self, cmd):
        if type(cmd) is str:
            assert cmd != "" and not cmd.isspace(), "[Assert Error] Input cmd is str but invalid!"
            #if re.match(r'TestMluServiceApi', cmd):
            #    self.cmd = re.split(r'\s+', cmd, 1)
            #else:
            #    self.cmd = re.split(r'\s+', cmd)
            self.cmd = cmd
        elif type(cmd) is list:
            assert len(cmd) > 0, "[Assert Error] Input cmd is list but invalid!"
            self.cmd = cmd
        else:
            assert False, "[Assert Error] Input cmd only support str or list!"

        self.LOG.print_log('INFO', "In execute_cmd, cmd is: {}.".format(self.cmd))
        try:
            self.proc = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = self.proc.communicate()
            self.return_code = self.proc.returncode
        except:
            self.LOG.print_log('ERROR', "Failed to execute command - {}.".format(cmd))
            assert False
        else:
            self.output = out.decode('utf-8')
            if err is not None:
                assert False, "[Assert Error] Error should be in output!"

        self.LOG.print_log('INFO', "In execute_cmd, output is:\n")
        self.LOG.print_plain_log('INFO', self.output)
        self.LOG.print_log('INFO', "In execute_cmd, return code is:{}.\n".format(self.return_code))

        return self.output, self.return_code


class HostExecuteCommand():

    # class attribute
    # LOG = ExecuteLog('HostExecuteCommand', 'DEBUG')
    LOG = None
    OS_Support = ['Linux', 'Windows']

    def __init__(self, host_ip, username, password, port=22, operation_system='Linux'):
        self.host_ip = str(host_ip)
        self.port = int(port)
        self.username = str(username)
        self.password = str(password)
        assert operation_system in HostExecuteCommand.OS_Support, "[Assert Error] Invalid OS!"
        self.operation_system = str(operation_system)

    def host_runcmd(self, command, background=False, stdin_str=None):
        if self.operation_system == 'Linux':
            return self.linux_host_runcmd(command, background, stdin_str)
        elif self.operation_system == 'Windows':
            return self.windows_host_runcmd(command)
        else:
            assert False, "[Assert Error] Invalid OS is passed in!"

    def host_scp_send(self, local_file, remote_file):
        assert self.operation_system == 'Linux', "[Assert Error] Only Linux OS is supported!"
        file_stat = os.stat(local_file)

        # Make socket, connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host_ip, self.port))

        # Initialise
        session = Session()
        session.handshake(sock)
        userauth_list = session.userauth_list(self.username)
        self.LOG.print_log('DEBUG', "In host {}, user {} authentication list is: {}.".format(self.host_ip, self.username, userauth_list))
        session.userauth_password(self.username, self.password)

        # Channel initialise, exec and wait for end
        self.LOG.print_log('INFO', "Send local file {} to Host {} at {}.".format(local_file, self.host_ip, remote_file))
        try:
            channel = session.scp_send(remote_file, file_stat.st_mode & 777, file_stat.st_size)
            with open(local_file, 'rb') as local_fh:
                for data in local_fh:
                    channel.write(data)
            channel.send_eof()
            channel.wait_eof()
            channel.wait_closed()
        except Exception as err:
            self.LOG.print_log('ERROR', str(err))
            assert False, "[Assert Error] Something wrong during scp send!"

    def linux_host_runcmd(self, command, background=False, stdin_str=None):
        assert type(command) is str and command != "" and not command.isspace(),\
            "[Assert Error] Input command is invalid!"
        if stdin_str:
            assert background is False, "[Assert Error] Input background and stdin_str, you can only select one of them."
            assert type(stdin_str) is str, "[Assert Error] Input stdin_str must be a string!"

        auth_method = 'password'

        # Make socket, connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host_ip, self.port))

        # Initialise
        session = Session()
        session.handshake(sock)
        userauth_list = session.userauth_list(self.username)
        self.LOG.print_log('DEBUG', "In host {}, user {} authentication list is: {}.".format(self.host_ip, self.username, userauth_list))
        assert auth_method in userauth_list, "[Assert Error] The user in linux host must support {} authentication!".format(auth_method)
        session.userauth_password(self.username, self.password)

        # Channel initialise, exec and wait for end
        self.LOG.print_log('INFO', "Host {} - Run cmd: {}.".format(self.host_ip, command))
        channel = session.open_session()

        if background:
            channel.execute(command)
            time.sleep(5)
            channel.close()
        elif stdin_str:
            channel.execute(command)
            time.sleep(5)
            channel.write(stdin_str)
            channel.wait_eof()
            channel.close()
            channel.wait_closed()
        else:
            channel.execute(command)
            channel.wait_eof()
            channel.close()
            channel.wait_closed()

        # Get output
        output = b''
        size, data = channel.read()
        while size > 0:
            output += data
            size, data = channel.read()
        output = output.decode("utf-8").strip()

        # Get exit status
        return_code = channel.get_exit_status()

        self.LOG.print_log('INFO', "Command {} - output is:".format(command))
        self.LOG.print_plain_log('INFO', output)
        self.LOG.print_log('INFO', "Command {} - exit status is:{}.".format(command, return_code))

        return output, return_code

    def windows_host_runcmd(self, command):
        assert type(command) is str and command != "" and not command.isspace(),\
            "[Assert Error] Input command is invalid!"

        #BUFF_SIZE = 4096
        BUFF_SIZE = 8192
        TIMEOUT = 600
        OUTPUT_LINE = '\n====== OUTPUT ======\n'
        RETURN_CODE_LINE = '\n====== RETURN_CODE ======\n'
        EOP = b'\n====== This is the end of the packet ======\n'

        cmd = command
        received_data = str()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host_ip, self.port))
            s.setblocking(False)
            s.sendall(cmd.encode())
            data = bytearray()
            number = 0
            begin_time = time.time()
            while True:
                if len(data) == 0 and time.time() - begin_time > 3 * TIMEOUT:
                    self.LOG.print_log('INFO', "Nothing was received in {} seconds. Close this connection...".format(3 * TIMEOUT))
                    break
                elif len(data) > 0 and time.time() - begin_time > TIMEOUT:
                    self.LOG.print_log('INFO', "No data received in {} seconds. Close this connection...".format(TIMEOUT))
                    break

                new_data = b''
                try:
                    new_data = s.recv(BUFF_SIZE)
                except BlockingIOError:
                    time.sleep(0.1)
                    continue

                self.LOG.print_log('DEBUG', "Command {} - number {} Got new data:\n".format(cmd, number))
                self.LOG.print_plain_log('DEBUG', new_data)

                data.extend(new_data)
                begin_time = time.time()

                # get the end of the message
                if EOP in new_data:
                    self.LOG.print_log('INFO', "All data collected.")
                    break
                # connection was closed by server
                if not new_data:
                    self.LOG.print_log('INFO', "Server closed the connection. Exit...")
                    break

                time.sleep(0.1)
                number += 1

            received_data = data.decode()

            self.LOG.print_log('DEBUG', "Command {} - total received_data is:\n".format(cmd))
            self.LOG.print_plain_log('DEBUG', received_data)
            # for line in received_data.splitlines():
            #     self.LOG.print_plain_log('DEBUG', line)

        m = re.search(OUTPUT_LINE + r'(.*)' + RETURN_CODE_LINE + r'([\-]?\d+)', received_data, re.S)
        if m:
            output = str(m.group(1))
            return_code = int(m.group(2))
        else:
            assert False, "[Assert Error] Failed to find output and return code!"

        self.LOG.print_log('INFO', "Command {} - output is:".format(command))
        self.LOG.print_plain_log('INFO', output)
        self.LOG.print_log('INFO', "Command {} - exit status is:{}.".format(command, return_code))

        return output, return_code

    def linux_host_runshell(self, commands):
        assert type(commands) is list and len(commands) != 0, "[Assert Error] Input commands is not a list or it's empty!"
        auth_method = 'password'

        # Make socket, connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host_ip, self.port))

        # Initialise
        session = Session()
        session.handshake(sock)
        userauth_list = session.userauth_list(self.username)
        self.LOG.print_log('DEBUG', "In host {}, user {} authentication list is: {}.".format(self.host_ip, self.username, userauth_list))
        assert auth_method in userauth_list, "[Assert Error] The user in linux host must support {} authentication!".format(auth_method)
        session.userauth_password(self.username, self.password)

        # Channel initialise, exec and wait for end
        channel = session.open_session()
        channel.shell()

        for command in commands:
            self.LOG.print_log('INFO', "Run cmd: {}".format(command))
            channel.write(command + '\n')

        # check session is in non-blocking mode
        blocking_mode = session.get_blocking()
        self.LOG.print_log('INFO', 'Now the session is in blocking mode ? {}'.format(blocking_mode))
        if blocking_mode:
            self.LOG.print_log('INFO', "Set session blocking mode to False...")
            session.set_blocking(False)
            blocking_mode = session.get_blocking()
            self.LOG.print_log('INFO', 'Now the session is in blocking mode ? {}'.format(blocking_mode))

        # Get output
        round_num = 0
        timeout = 40
        begin_time = time.time()

        output = b''
        while True:
            if len(output) == 0 and time.time() - begin_time > timeout * 3:
                self.LOG.print_log('INFO', 'Nothing is received in {} seconds, exit.'.format(timeout * 3))
                break
            elif len(output) > 0 and time.time() - begin_time > timeout:
                self.LOG.print_log('INFO', 'No data is received in {} seconds, exit.'.format(timeout))
                break

            size, data = channel.read()
            if size > 0:
                self.LOG.print_log('DEBUG', "round_number {} Got new data:\n".format(round_num, data))
                self.LOG.print_plain_log('DEBUG', data)
                output += data
                begin_time = time.time()
            else:
                self.LOG.print_log('DEBUG', "round_number {} No new data.".format(round_num))
            time.sleep(0.5)
            round_num += 1

        channel.close()

        output = output.decode("utf-8").strip()
        return_code = channel.get_exit_status()

        self.LOG.print_log('INFO', "output is:\n")
        self.LOG.print_plain_log('INFO', output)
        self.LOG.print_log('INFO', "exit status is:{}.".format(return_code))

        return output, return_code


class StorageExecuteCommand():

    # class attribute
    # LOG = ExecuteLog('StorageExecuteCommand', 'DEBUG')
    LOG = None

    def __init__(self, spa_ip, spb_ip, username='root', port=22):
        self.spa_ip = str(spa_ip)
        self.spb_ip = str(spb_ip)
        self.port = int(port)
        self.username = str(username)
        self.private_key_file = '/c4shares/Public/ssh/id_rsa.root'
        if sys.platform.lower().startswith('win'):
            testsuite_path = os.path.abspath('./')
            m = re.search(r'(.+\\).+_TestSuite', testsuite_path)
            project_path = m.group(1)
            self.LOG.print_log('DEBUG', "Current testsuite_path is {}, project_path is {}".format(testsuite_path, project_path))
            self.private_key_file = project_path + 'storage_key/id_rsa.root'
        assert os.path.exists(self.private_key_file), \
            "[Assert Error] The private_key_file {} is not exist!".format(self.private_key_file)

    def spa_runcmd(self, command, background=False, stdin_str=None):
        return self.runcmd(self.spa_ip, command, background=background, stdin_str=stdin_str)

    def spb_runcmd(self, command, background=False, stdin_str=None):
        return self.runcmd(self.spb_ip, command, background=background, stdin_str=stdin_str)

    def spa_scp_send(self, local_file, remote_file):
        self.sp_scp_send(local_file, remote_file, self.spa_ip)

    def spb_scp_send(self, local_file, remote_file):
        self.sp_scp_send(local_file, remote_file, self.spb_ip)

    def runcmd(self, sp_ip, command, background=False, stdin_str=None):
        assert type(command) is str and command != "" and not command.isspace(), \
            "[Assert Error] Input command is invalid!"
        if stdin_str:
            assert background is False, "[Assert Error] Input background and stdin_str, you can only select one of them."
            assert type(stdin_str) is str, "[Assert Error] Input stdin_str must be a string!"

        auth_method = 'publickey'

        # Make socket, connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((sp_ip, self.port))

        # Initialise
        session = Session()
        session.handshake(sock)
        userauth_list = session.userauth_list(self.username)
        self.LOG.print_log('DEBUG', "In host {}, user {} authentication list is: {}.".format(sp_ip, self.username, userauth_list))
        assert auth_method in userauth_list, "[Assert Error] The user in storage must support {} authentication!".format(auth_method)
        session.userauth_publickey_fromfile(self.username, self.private_key_file)

        # Channel initialise, exec and wait for end
        self.LOG.print_log('INFO', "Run cmd: {}.".format(command))
        channel = session.open_session()
        # channel.execute(command)
        # channel.wait_eof()
        # channel.close()
        # channel.wait_closed()

        if background:
            channel.execute(command)
            time.sleep(5)
            channel.close()
        elif stdin_str:
            channel.execute(command)
            time.sleep(5)
            channel.write(stdin_str)
            channel.wait_eof()
            channel.close()
            channel.wait_closed()
        else:
            channel.execute(command)
            channel.wait_eof()
            channel.close()
            channel.wait_closed()

        # Get output
        output = b''
        size, data = channel.read()
        while size > 0:
            output += data
            size, data = channel.read()
        output = output.decode("utf-8").strip()

        # Get exit status
        return_code = channel.get_exit_status()

        self.LOG.print_log('INFO', "Command {} - output is:\n".format(command))
        self.LOG.print_plain_log('INFO', output)
        self.LOG.print_log('INFO', "Command {} - exit status is:{}.".format(command, return_code))

        return output, return_code

    def sp_scp_send(self, local_file, remote_file, sp_ip):
        auth_method = 'publickey'
        file_stat = os.stat(local_file)

        # Make socket, connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((sp_ip, self.port))

        # Initialise
        session = Session()
        session.handshake(sock)
        userauth_list = session.userauth_list(self.username)
        self.LOG.print_log('DEBUG', "In storage sp {}, user {} authentication list is: {}.".format(sp_ip, self.username, userauth_list))
        assert auth_method in userauth_list, "[Assert Error] The user in storage must support {} authentication!".format(auth_method)
        session.userauth_publickey_fromfile(self.username, self.private_key_file)

        # Channel initialise, exec and wait for end
        self.LOG.print_log('INFO', "Send local file {} to storage sp {} at {}.".format(local_file, sp_ip, remote_file))
        try:
            channel = session.scp_send(remote_file, file_stat.st_mode & 777, file_stat.st_size)
            with open(local_file, 'rb') as local_fh:
                for data in local_fh:
                    channel.write(data)
            channel.send_eof()
            channel.wait_eof()
            channel.wait_closed()
        except Exception as err:
            self.LOG.print_log('ERROR', str(err))
            assert False, "[Assert Error] Something wrong during storage sp scp send!"

