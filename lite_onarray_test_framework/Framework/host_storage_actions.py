from Framework.connection_and_logging import *

##############################################################################
# Module Variable
##############################################################################

EC = ExecuteCommand()
Device_LOG = None

##############################################################################
# Common Function
##############################################################################

def isPingable(ip_addr, ping_attempts=3):
    cmd = "ping -{} {} {}".format('n' if sys.platform.lower().startswith('win') else 'c', ping_attempts, ip_addr)
    output, return_code = EC.execute_cmd(cmd)
    m1 = re.search(r'host unreachable', output, re.IGNORECASE)
    m2 = re.search(r'(\d+)%\s+(packet\s+)?loss', output)
    if return_code != 0:
        return False
    if m1:
        return False
    if m2 and int(m2.group(1)) != 0:
        return False
    return True

def check_pingable(ip_addr, timeout=60, host_type='Host', log_obj=None):

    start_time = time.time()
    while True:
        current_time = time.time()
        if current_time - start_time > timeout:
            break
        if isPingable(ip_addr) is True:
            if log_obj:
                log_obj.print_log('INFO', '{} {} is Ping-able.'.format(host_type, ip_addr))
            return
        if log_obj:
            log_obj.print_log('INFO', '{} {} is not Ping-able.'.format(host_type, ip_addr))
        time.sleep(5)

    assert False, "[Assert Error] {} {} is not Ping-able in {} seconds!".format(host_type, ip_addr, timeout)

def check_not_pingable(ip_addr, timeout=60, host_type='Host', log_obj=None):

    start_time = time.time()
    while True:
        current_time = time.time()
        if current_time - start_time > timeout:
            break
        if isPingable(ip_addr) is False:
            if log_obj:
                log_obj.print_log('INFO', '{} {} is not Ping-able.'.format(host_type, ip_addr))
            return
        if log_obj:
            log_obj.print_log('INFO', '{} {} is Ping-able.'.format(host_type, ip_addr))
        time.sleep(5)

    assert False, "[Assert Error] {} {} is still Ping-able in {} seconds!".format(host_type, ip_addr, timeout)

##############################################################################
# Host And Storage Class
##############################################################################

class LinuxHost():

    def __init__(self, host_ip, username, password, iox_path=None, vjtree_path=None, vdbench_path=None):
        self.host_ip = host_ip
        self.username = username
        self.password = password
        self.operation_system = 'Linux'
        self.HOST_EC = HostExecuteCommand(self.host_ip, username, password)
        #
        self.iox_path = iox_path
        self.vjtree_path = vjtree_path
        self.vdbench_path = vdbench_path

    def check_host_pingable(self, timeout=60):
        check_pingable(self.host_ip, timeout=timeout, host_type='LinuxHost')


class WindowsHost():

    def __init__(self, host_ip, username, password, port):
        self.host_ip = host_ip
        self.username = username
        self.password = password
        self.operation_system = 'Windows'
        self.port = str(port)
        self.HOST_EC = HostExecuteCommand(self.host_ip, username, password, self.port, self.operation_system)

    def check_host_pingable(self, timeout=60):
        check_pingable(self.host_ip, timeout=timeout, host_type='WindowsHost')


class Storage():

    def __init__(self, name, spa_ip, spb_ip, mgmt_ip, username='root'):
        self.name = str(name)
        self.spa_ip = str(spa_ip)
        self.spb_ip = str(spb_ip)
        self.mgmt_ip = str(mgmt_ip)
        self.username = username
        self.master_sp = None
        self.STORAGE_EC = StorageExecuteCommand(self.spa_ip, self.spb_ip)
        #
        self.available_port = []
        self.available_ioip = []
        self.gateway = None
        self.netmask = None
        self.vlan = None
        self.exec_host = None

    def check_bothsp_pingable(self, timeout=60, log_obj=None):
        self.check_sp_pingable(sp='spa', timeout=timeout, log_obj=log_obj)
        self.check_sp_pingable(sp='spb', timeout=timeout, log_obj=log_obj)

    def check_sp_pingable(self, sp, timeout=60, log_obj=None):
        assert sp in ['spa', 'spb'], "[Assert Error] Input sp must be spa or spb!"
        if sp == 'spa':
            check_pingable(self.spa_ip, timeout=timeout, host_type='Storage SPA', log_obj=log_obj)
        elif sp == 'spb':
            check_pingable(self.spb_ip, timeout=timeout, host_type='Storage SPB', log_obj=log_obj)

    def run_uemcli(self, cmd, stdin_str=None):
        prefix = 'uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d {} '.format(self.mgmt_ip)
        command = prefix + cmd

        if self.exec_host is not None:
            if stdin_str:
                output, return_code = self.exec_host.HOST_EC.host_runcmd(command, stdin_str=stdin_str)
            else:
                output, return_code = self.exec_host.HOST_EC.host_runcmd(command)
        else:
            if stdin_str:
                assert False, "[Assert Error] stdin for local execution is not support yet!"
                # TODO
                # output, return_code = EC.execute_cmd(command, stdin_str=stdin_str)
            else:
                output, return_code = EC.execute_cmd(command)

        return output, return_code

    def get_master_sp(self):
        sp_list = ['spa', 'spb']
        sp_ip_list = [self.spa_ip, self.spb_ip]
        command = 'ps -ef | grep ECOM'

        for i in range(0, len(sp_ip_list)):
            output, return_code = self.STORAGE_EC.runcmd(sp_ip_list[i], command)
            assert return_code == 0, "[Assert Error] Failed to run command - {}".format(command)
            m = re.search(r'ecom.+\s+ECOM -u ecom', output)
            if m:
                self.master_sp = sp_list[i]
                break

        assert type(self.master_sp) is str and self.master_sp in ['spa', 'spb'], \
            "[Assert Error] Failed to get master sp for storage {}!".format(self.name)
        return self.master_sp
