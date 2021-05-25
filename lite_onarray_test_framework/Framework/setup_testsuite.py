from Framework.host_storage_actions import *
from Framework.connection_and_logging import ExecuteLog

import configparser
import collections

##############################################################################
# Module Variable
##############################################################################

your_testsuite_testlog_dir = 'testlog/'
your_testsuite_testbed_dir = 'testbed/'
your_testsuite_testparam_dir = 'testparam/'
assert os.path.exists(your_testsuite_testlog_dir), \
    "[Assert Error] There must be a directory {} under your testsuite directory!".format(your_testsuite_testlog_dir)
assert os.path.exists(your_testsuite_testbed_dir), \
    "[Assert Error] There must be a directory {} under your testsuite directory!".format(your_testsuite_testbed_dir)
assert os.path.exists(your_testsuite_testparam_dir), \
    "[Assert Error] There must be a directory {} under your testsuite directory!".format(your_testsuite_testparam_dir)

# Define testlog
LOG_LEVEL = 'DEBUG'

testsuite_path = os.path.abspath('./')
testsuite_dirname = os.path.basename(testsuite_path)

testlog = your_testsuite_testlog_dir + testsuite_dirname + '_' + time.strftime('%Y%m%d_%H%M') + '.txt'
LOG = ExecuteLog('setup_testsuite', LOG_LEVEL, testlog)
assert os.path.exists(testlog), "[Assert Error] The testlog file {} dose not exist!".format(testlog)
assert isinstance(LOG, ExecuteLog), "[Assert Error] LOG should be a instance of class ExecuteLog!"

# import Framework.host_storage_actions
# Framework.host_storage_actions.Device_LOG = ExecuteLog('host_storage_actions', LOG_LEVEL, testlog)
# assert isinstance(LOG, ExecuteLog), "[Assert Error] LOG should be a instance of class ExecuteLog!"

# Define logging for basic module
ExecuteCommand.LOG = ExecuteLog('ExecuteCommand', LOG_LEVEL, your_testsuite_testlog_dir + 'ExecuteCommand')
HostExecuteCommand.LOG = ExecuteLog('HostExecuteCommand', LOG_LEVEL, your_testsuite_testlog_dir + 'HostExecuteCommand')
StorageExecuteCommand.LOG = ExecuteLog('StorageExecuteCommand', LOG_LEVEL, your_testsuite_testlog_dir + 'StorageExecuteCommand')
assert isinstance(ExecuteCommand.LOG, ExecuteLog), "[Assert Error] ExecuteCommand.LOG should be a instance of class ExecuteLog!"
assert isinstance(HostExecuteCommand.LOG, ExecuteLog), "[Assert Error] HostExecuteCommand.LOG should be a instance of class ExecuteLog!"
assert isinstance(StorageExecuteCommand.LOG, ExecuteLog), "[Assert Error] StorageExecuteCommand.LOG should be a instance of class ExecuteLog!"

# Print logging information
log_path = str(testlog)
if sys.platform.startswith('win'):
    log_path = log_path.replace("/", "\\")
print('\nCheck the test cases execution log here:\n{}'.format(testsuite_path + '\\' + log_path))

##############################################################################
# TestSuite Function
##############################################################################

def collect_testbed_testsuite_configurations(testbed_filename, testparam_filename):
    """
    :param testbed_filename: 'testbed_OB-H1651.cfg'
    :param testparam_filename: 'testparam_Block.cfg'
    :return: storage, io_host, uemcli_host, windows_host, d_testparam
    """

    global your_testsuite_testbed_dir
    global your_testsuite_testparam_dir

    # Define testbed and testparam config file
    testbed = your_testsuite_testbed_dir + testbed_filename
    testparam = your_testsuite_testparam_dir + testparam_filename
    assert os.path.exists(testbed), "[Assert Error] The given testbed config file {} dose not exist!".format(testbed)
    assert os.path.exists(testparam), "[Assert Error] The given testsuite config file {} dose not exist!".format(testparam)

    config_testbed = configparser.ConfigParser()
    config_testbed.read(testbed)

    config_testparam = configparser.ConfigParser()
    config_testparam.read(testparam)

    # Collect testbed and testsuite parameters
    storage, io_host, uemcli_host, windows_host = parse_testbed_parameters(testbed, config_testbed)
    d_testparam = parse_testsuite_parameters(testparam, config_testparam)

    return storage, io_host, uemcli_host, windows_host, d_testparam


def parse_testbed_parameters(testbed, config):

    LOG.print_log('INFO', 'Collect test devices from file {}...'.format(testbed))

    necessary_device = ['IO_HOST', 'STORAGE']
    for section in necessary_device:
        assert config.has_section(section), "[Assert Error] testbed.cfg must contain {} section!".format(section)

    #
    io_host = None
    if config.has_section('IO_HOST'):
        io_host_ip = config['IO_HOST']['host_ip']
        io_username = config['IO_HOST']['username']
        io_password = config['IO_HOST']['password']
        io_password = io_password.replace("'", "")
        io_host = LinuxHost(io_host_ip, io_username, io_password)

        for item in config.options('IO_HOST'):
            LOG.print_log('INFO', "[IO_HOST] section - Get item {} : {}".format(item, config['IO_HOST'][item]))

        for item in config.options('IO_HOST'):
            if item == 'iox_path':
                io_host.iox_path = config['IO_HOST'][item]
            elif item == 'vjtree_path':
                io_host.vjtree_path = config['IO_HOST'][item]
            elif item == 'vdbench_path':
                io_host.vdbench_path = config['IO_HOST'][item]

    #
    uemcli_host = None
    if config.has_section('UEMCLI_HOST'):
        uemcli_host_ip = config['UEMCLI_HOST']['host_ip']
        uemcli_username = config['UEMCLI_HOST']['username']
        uemcli_password = config['UEMCLI_HOST']['password']
        uemcli_host = LinuxHost(uemcli_host_ip, uemcli_username, uemcli_password)

        for item in config.options('UEMCLI_HOST'):
            LOG.print_log('INFO', "[UEMCLI_HOST] section - Get item {} : {}".format(item, config['UEMCLI_HOST'][item]))

    assert isinstance(uemcli_host, LinuxHost), \
        "[Assert Error] Variable uemcli_host - {} is not a instance of LinuxHost!".format(uemcli_host)

    #
    windows_host = None
    if config.has_section('POWERSHELL_HOST'):
        windows_host_ip = config['POWERSHELL_HOST']['host_ip']
        windows_username = config['POWERSHELL_HOST']['username']
        windows_password = config['POWERSHELL_HOST']['password']
        windows_port = config['POWERSHELL_HOST']['port']
        windows_host = WindowsHost(windows_host_ip, windows_username, windows_password, windows_port)

        for item in config.options('POWERSHELL_HOST'):
            LOG.print_log('INFO', "[POWERSHELL_HOST] section - Get item {} : {}".format(item, config['POWERSHELL_HOST'][item]))

        assert isinstance(windows_host, WindowsHost), \
            "[Assert Error] Variable windows_host - {} is not a instance of WindowsHost!".format(windows_host)

    #
    storage = None
    if config.has_section('STORAGE'):
        storage_name = config['STORAGE']['name']
        storage_spa_ip = config['STORAGE']['spa_ip']
        storage_spb_ip = config['STORAGE']['spb_ip']
        storage_mgmt_ip = config['STORAGE']['mgmt_ip']
        storage_username = config['STORAGE']['username']
        storage = Storage(storage_name, storage_spa_ip, storage_spb_ip, storage_mgmt_ip)

        for item in config.options('STORAGE'):
            LOG.print_log('INFO', "[STORAGE] section - Get item {} : {}".format(item, config['STORAGE'][item]))
            if item.startswith('port_'):
                storage.available_port.append(config['STORAGE'][item])
            elif item.startswith('ioip_'):
                storage.available_ioip.append(config['STORAGE'][item])
            elif item == 'gateway':
                storage.gateway = config['STORAGE'][item]
            elif item == 'netmask':
                storage.netmask = config['STORAGE'][item]
            elif item == 'vlan':
                storage.vlan = config['STORAGE'][item]

        if 'uemcli_host' in vars().keys() and uemcli_host is not None:
            storage.exec_host = uemcli_host

    #
    # TODO
    if config.has_section('VMWARE'):
        vcenter = config['VMWARE']['vcenter']
        esx_host = config['VMWARE']['esx_host']
        vm = config['VMWARE']['vm']

    # Assert necessary device before return
    assert isinstance(storage, Storage), "[Assert Error] Variable storage - {} is not a instance of Storage!".format(storage)
    assert isinstance(io_host, LinuxHost), "[Assert Error] Variable io_host - {} is not a instance of LinuxHost!".format(io_host)

    return storage, io_host, uemcli_host, windows_host


def parse_testsuite_parameters(testparam, config_testparam):

    LOG.print_log('INFO', 'Collect test parameters from file {}...'.format(testparam))

    options_restriction = collections.namedtuple('options_restriction', ['necessary_options', 'additional_options'])

    TEST_SUITE_COMMON = options_restriction(necessary_options=['logfile'],
                                            additional_options=['image', 'need_install'])
    POOL = options_restriction(necessary_options=['name', 'profile', 'dg', 'drive_number'],
                               additional_options=['type'])
    NASSERVER = options_restriction(necessary_options=['name', 'pool', 'sp'],
                                    additional_options=['sharing_protocol'])
    HOST = options_restriction(necessary_options=['name', 'ip', 'username', 'password'],
                               additional_options=[])
    CP = options_restriction(necessary_options=['name', 'pool', 'data_reduction', 'advanced_dedup'],
                             additional_options=[])
    VVOL_DATASTORE = options_restriction(necessary_options=['name', 'type', 'cp', 'size', 'host'],
                                         additional_options=[])
    VCENTER = options_restriction(necessary_options=['ip', 'username', 'password'],
                                  additional_options=[])
    ESXHOST = options_restriction(necessary_options=['ip', 'username', 'password'],
                                  additional_options=[])
    VM = options_restriction(necessary_options=['name', 'template'],
                             additional_options=['ip'])

    sections = config_testparam.sections()
    LOG.print_log('INFO', 'Get following sections from {}:'.format(testparam))
    LOG.print_plain_log('INFO', sections)

    #
    # def check_necessary_option_and_update(sec, opt):
    #     assert opt in config_testparam.options(sec), "[Assert Error] [{}] section must contain option - {}!".format(sec, opt)
    #     d_testparam[sec][opt] = config_testparam[sec][opt]
    #     LOG.print_log('INFO', "[{}] section - Get option {} : {}".format(sec, opt, d_testparam[sec][opt]))
    #
    # def check_additional_option_and_update(sec, opt):
    #     if opt in config_testparam.options(sec):
    #         d_testparam[sec][opt] = config_testparam[sec][opt]
    #         LOG.print_log('INFO', "[{}] section - Get option {} : {}".format(sec, opt, d_testparam[sec][opt]))

    def check_options_and_update(sec, options_restriction_obj):
        assert len(options_restriction_obj.necessary_options) > 0, "[Assert Error] [{}] section have no necessary option!".format(sec)
        d = {}
        for opt in options_restriction_obj.necessary_options:
            assert opt in config_testparam.options(sec), "[Assert Error] [{}] section must contain option - {}!".format(sec, opt)
            d[opt] = config_testparam[sec][opt]
            LOG.print_log('INFO', "[{}] section - Get option {} : {}".format(sec, opt, d[opt]))

        if len(options_restriction_obj.additional_options) > 0:
            for opt in options_restriction_obj.additional_options:
                if opt in config_testparam.options(sec):
                    d[opt] = config_testparam[sec][opt]
                    LOG.print_log('INFO', "[{}] section - Get option {} : {}".format(sec, opt, d[opt]))
        return d

    d_testparam = {}.fromkeys(sections, None)
    pool_section_exist = False
    for section in sections:
        LOG.print_log('INFO', "====== Find section [{}].".format(section))
        d = None
        if section.startswith('TEST_SUITE_COMMON'):
            d = check_options_and_update(section, TEST_SUITE_COMMON)
        elif section.startswith('POOL'):
            pool_section_exist = True
            d = check_options_and_update(section, POOL)
        elif section.startswith('LUN'):
            # TODO
            pass
        elif section.startswith('NASSERVER'):
            d = check_options_and_update(section, NASSERVER)
        elif section.startswith('FS'):
            # TODO
            pass
        elif section.startswith('HOST'):
            d = check_options_and_update(section, HOST)
        elif section.startswith('CP'):
            d = check_options_and_update(section, CP)
        elif section.startswith('VVOL_DATASTORE'):
            d = check_options_and_update(section, VVOL_DATASTORE)
        elif section.startswith('VCENTER'):
            d = check_options_and_update(section, VCENTER)
        elif section.startswith('ESXHOST'):
            d = check_options_and_update(section, ESXHOST)
        elif section.startswith('VM'):
            d = check_options_and_update(section, VM)

        if d is not None:
            d_testparam[section] = d
            LOG.print_log('INFO', 'Section [{}] parameters:'.format(section))
            LOG.print_plain_log('INFO', d_testparam[section])
        else:
            error_str = 'Section [{}] in {} cannot be recognized!'.format(section, testparam)
            LOG.print_log('ERROR', error_str)
            assert False, "[Assert Error] " + error_str

    assert pool_section_exist, "[Assert Error] {} must contain POOL section!".format(testparam)
    # for section in sections:
    #     print('### ', section)
    #     print(d_testparam[section])

    # Assert before return
    assert isinstance(d_testparam, dict), "[Assert Error] Variable d_testparam - {} is not a dict!".format(d_testparam)

    return d_testparam


##############################################################################
# Decorator Function
##############################################################################

def ts_symbol_printer(log_obj=LOG):
    def decorator(func):
        def wrapper(*args, **kwargs):
            log_obj.print_log('INFO', '##############################################################################')
            log_obj.print_log('INFO', '#                               Start Test Suite                             #')
            log_obj.print_log('INFO', '##############################################################################')

            func(*args, **kwargs)

            log_obj.print_log('INFO', '##############################################################################')
            log_obj.print_log('INFO', '#                               Passed Test Suite                            #')
            log_obj.print_log('INFO', '##############################################################################')
        return wrapper
    return decorator


def tc_symbol_printer(testcase_name, log_obj=LOG):
    def decorator(func):
        def wrapper(*args, **kwargs):
            log_obj.print_log('INFO', '============================ Start Test Case - {} ============================'.format(testcase_name))
            func(*args, **kwargs)
            log_obj.print_log('INFO', '============================ Passed Test Case - {} ===========================\n\n'.format(testcase_name))
        return wrapper
    return decorator


# def storage_setup_action_decorator(func):
#     def wrapper(*args, **kwargs):
#         step_str, output, return_code = func(*args, **kwargs)
#         if return_code != 0:
#             LOG.print_log('ERROR', 'Failed to {} !'.format(step_str))
#             assert False, "[Assert Error] Failed to {} !".format(step_str)
#     return wrapper

def ensure_action_succeed_decorator(func):
    def wrapper(*args, **kwargs):
        step_str, output, return_code, check_output = func(*args, **kwargs)

        # make sure it succeed
        if return_code != 0:
            LOG.print_log('ERROR', 'Failed to {} !'.format(step_str))
            assert False, "[Assert Error] Failed to {} !".format(step_str)

        # check output if needed
        if check_output and type(check_output) is str:
            m = re.search(check_output, output)
            assert m is not None, "[Assert Error] Failed to get {} in output!".format(check_output)
    return wrapper


##############################################################################
# Common Function
##############################################################################

def logging_and_assert_with_error(log_obj, err_msg):
    log_obj.print_log('ERROR', err_msg)
    assert False, "[Assert Error] " + err_msg

@ensure_action_succeed_decorator
def run_command_on_host(iohost_obj, command, step_str=None, check_output=None, background=False, log_obj=LOG):
    if step_str is None:
        step_str = 'Run command {}...'.format(command)
    log_obj.print_log('INFO', step_str)

    output, return_code = iohost_obj.HOST_EC.host_runcmd(command, background)
    log_obj.print_log('INFO', "output is:\n")
    log_obj.print_plain_log('INFO', output)
    log_obj.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


def run_uemcli_check_returncode(storage_obj, command, step_str=None, log_obj=LOG):
    if step_str is None:
        step_str = 'Run command {}...'.format(command)
    log_obj.print_log('INFO', step_str)

    output, return_code = storage_obj.run_uemcli(command)
    log_obj.print_log('INFO', "output is:\n")
    log_obj.print_plain_log('INFO', output)
    log_obj.print_log('INFO', "exit status is:{}.".format(return_code))

    assert return_code == 0, "[Assert Error] Failed to {} !".format(step_str)
    if ' show ' not in command:
        assert 'Operation completed successfully' in output, "[Assert Error] Failed to {} !".format(step_str)

    return output, return_code


def run_command_on_host_check_returncode(host_obj, command, step_str=None, log_obj=LOG):
    if step_str is None:
        step_str = 'Run command {}...'.format(command)
    log_obj.print_log('INFO', step_str)

    output, return_code = host_obj.HOST_EC.host_runcmd(command)
    log_obj.print_log('INFO', "output is:\n")
    log_obj.print_plain_log('INFO', output)
    log_obj.print_log('INFO', "exit status is:{}.".format(return_code))

    assert return_code == 0, "[Assert Error] Failed to {} !".format(step_str)

    return output, return_code


def run_command_on_host_without_check(host_obj, command, step_str=None, log_obj=LOG):
    if step_str is None:
        step_str = 'Run command {}...'.format(command)
    log_obj.print_log('INFO', step_str)

    output, return_code = host_obj.HOST_EC.host_runcmd(command)
    log_obj.print_log('INFO', "output is:\n")
    log_obj.print_plain_log('INFO', output)
    log_obj.print_log('INFO', "exit status is:{}.".format(return_code))

    return output, return_code


def run_command_on_storage_check_returncode(storage_obj, command, step_str=None, sp_owner='spa', log_obj=LOG):
    if step_str is None:
        step_str = 'Run command {}...'.format(command)
    log_obj.print_log('INFO', step_str)

    if sp_owner == 'spa':
        output, return_code = storage_obj.STORAGE_EC.spa_runcmd(command)
    elif sp_owner == 'spb':
        output, return_code = storage_obj.STORAGE_EC.spb_runcmd(command)

    log_obj.print_log('INFO', "output is:\n")
    log_obj.print_plain_log('INFO', output)
    log_obj.print_log('INFO', "exit status is:{}.".format(return_code))

    assert return_code == 0, "[Assert Error] Failed to {} !".format(step_str)

    return output, return_code

def run_command_on_storage_without_check(storage_obj, command, step_str=None, sp_owner='spa', log_obj=LOG):
    if step_str is None:
        step_str = 'Run command {}...'.format(command)
    log_obj.print_log('INFO', step_str)

    if sp_owner == 'spa':
        output, return_code = storage_obj.STORAGE_EC.spa_runcmd(command)
    elif sp_owner == 'spb':
        output, return_code = storage_obj.STORAGE_EC.spb_runcmd(command)

    log_obj.print_log('INFO', "output is:\n")
    log_obj.print_plain_log('INFO', output)
    log_obj.print_log('INFO', "exit status is:{}.".format(return_code))

    return output, return_code
