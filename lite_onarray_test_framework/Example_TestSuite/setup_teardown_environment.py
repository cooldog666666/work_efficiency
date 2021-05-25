from Framework.component import *
from Framework.test_actions import *


##############################################################################
# Module Variable
##############################################################################

testcase_name = 'setup_teardown_environment'
LOG = ExecuteLog(testcase_name, LOG_LEVEL, testlog)

##############################################################################
# Setup Environment
##############################################################################

def setup_test_environment_block(storage, io_host, uemcli_host, windows_host, d_testparam):
    """
    :param storage:
    :param io_host:
    :param uemcli_host:
    :param windows_host:
    :param d_testparam:
    :return: d_storage_object
    """

    LOG.print_log('INFO', "Setup test environment...")
    d_storage_object = {}.fromkeys(d_testparam.keys(), None)

    ######
    LOG.print_step('Arrange test parameters.')
    #
    pool_name = d_testparam['POOL_1']['name']
    profile = d_testparam['POOL_1']['profile']
    dg = d_testparam['POOL_1']['dg']
    drive_number = d_testparam['POOL_1']['drive_number']
    pool_type = d_testparam['POOL_1']['type']
    #
    host_name = d_testparam['HOST_1']['name']
    host_ip = d_testparam['HOST_1']['name']

    ######
    LOG.print_step('Create a storage pool.')
    create_pool(storage, pool_name, profile, dg, drive_number, pool_type=pool_type)
    pool = Pool(storage, pool_name)
    pool.get_pool_profile()
    d_storage_object['POOL_1'] = pool

    ######
    LOG.print_step('Show port and IO ip address configured in testbed.')
    LOG.print_log('INFO', "storage available port: {}".format(storage.available_port))
    LOG.print_log('INFO', "storage available io ip: {}".format(storage.available_ioip))
    netmask = storage.netmask
    gateway = storage.gateway
    vlan = storage.vlan

    ######
    LOG.print_step('Create iscsi interfaces.')
    used_ip_list = []
    for _ in range(2):
        port = storage.available_port.pop()
        ioip = storage.available_ioip.pop()
        used_ip_list.append(ioip)
        create_iscsi_interface(storage, port, ioip, netmask, gateway, vlan)

    ######
    LOG.print_step('Create host.')
    create_host(storage, host_name, host_ip)
    host = Host(storage, io_host, host_name, host_ip)
    host.get_host_profile()
    host_iqn = host.get_host_iqn()
    host_id = host.profile['ID']
    d_storage_object['HOST_1'] = host

    ######
    LOG.print_step('Create host initiator.')
    create_initiator(storage, host_id, host_iqn, initiator_type='iscsi')

    ######
    LOG.print_step('Establish iscsi connection.')
    host.establish_iscsi_connection(ip_list=used_ip_list)
    host.check_host_initiator_state(state='OK')

    ######
    LOG.print_log('INFO', 'Setup test environment done. Get storage objects as following:')
    for k in d_storage_object.keys():
        LOG.print_plain_log('INFO', '{} : {}'.format(k, d_storage_object[k]))

    # Assert before return
    assert isinstance(d_storage_object, dict), "[Assert Error] Variable d_storage_object - {} is not a dict!".format(d_storage_object)

    return d_storage_object


def setup_test_environment_file(storage, io_host, uemcli_host, windows_host, d_testparam):
    """
    :param storage:
    :param io_host:
    :param uemcli_host:
    :param windows_host:
    :param d_testparam:
    :return: d_storage_object
    """

    LOG.print_log('INFO', "Setup test environment...")
    d_storage_object = {}.fromkeys(d_testparam.keys(), None)

    ######
    LOG.print_step('Arrange test parameters.')
    #
    pool_name = d_testparam['POOL_1']['name']
    profile = d_testparam['POOL_1']['profile']
    dg = d_testparam['POOL_1']['dg']
    drive_number = d_testparam['POOL_1']['drive_number']
    #
    host_name = d_testparam['HOST_1']['name']
    host_ip = d_testparam['HOST_1']['name']
    #
    nasserver_name = d_testparam['NASSERVER_1']['name']
    nasserver_pool = d_testparam['NASSERVER_1']['pool']
    nasserver_sp = d_testparam['NASSERVER_1']['sp']
    nasserver_sharing_protocol = d_testparam['NASSERVER_1']['sharing_protocol']

    ######
    LOG.print_step('Create a storage pool.')
    create_pool(storage, pool_name, profile, dg, drive_number)
    pool = Pool(storage, pool_name)
    pool.get_pool_profile()
    d_storage_object['POOL_1'] = pool

    ######
    LOG.print_step('Show port and IO ip address configured in testbed.')
    LOG.print_log('INFO', "storage available port: {}".format(storage.available_port))
    LOG.print_log('INFO', "storage available io ip: {}".format(storage.available_ioip))
    netmask = storage.netmask
    gateway = storage.gateway
    vlan = storage.vlan

    ######
    LOG.print_step('Create a nasserver.')

    LOG.print_log('INFO', "Create nas server {} in pool {}.".format(nasserver_name, pool_name))
    create_nasserver(storage, nasserver_name, pool_name, sp=nasserver_sp)
    nasserver = NasServer(storage, nasserver_name)
    nasserver.get_nasserver_profile()

    LOG.print_log('INFO', "Create nas interface.")
    LOG.print_log('INFO', "storage available port: {}".format(storage.available_port))
    LOG.print_log('INFO', "storage available io ip: {}".format(storage.available_ioip))
    port = storage.available_port.pop()
    ioip = storage.available_ioip.pop()
    create_nasserver_interface(storage, nasserver_name, port, ioip, netmask, gateway, vlan)

    LOG.print_log('INFO', "Create nas nfs.")
    nasserver.get_nasserver_nfs()
    nasserver_nfsid = nasserver.nfs_id
    set_nas_nfs_v3v4(storage, nasserver_nfsid)
    nasserver.get_nasserver_interface()
    nasserver_ifid = nasserver.interface_id
    LOG.print_log('INFO', "Get nasserver_ifid: {}".format(nasserver_ifid))

    d_storage_object['NASSERVER_1'] = nasserver

    ######
    LOG.print_step('Create host.')
    create_host(storage, host_name, host_ip)
    host = Host(storage, io_host, host_name, host_ip)
    host.get_host_profile()
    d_storage_object['HOST_1'] = host

    ######
    LOG.print_log('INFO', 'Setup test environment done. Get storage objects as following:')
    for k in d_storage_object.keys():
        LOG.print_plain_log('INFO', '{} : {}'.format(k, d_storage_object[k]))

    # Assert before return
    assert isinstance(d_storage_object, dict), "[Assert Error] Variable d_storage_object - {} is not a dict!".format(d_storage_object)

    return d_storage_object


##############################################################################
# Teardown Environment
##############################################################################

def teardown_test_environment_block(storage, io_host, uemcli_host, windows_host, d_testparam):
    """
    :param storage:
    :param io_host:
    :param uemcli_host:
    :param windows_host:
    :param d_testparam:
    """

    ######
    LOG.print_step('Arrange test parameters.')
    #
    pool_name = d_testparam['POOL_1']['name']
    profile = d_testparam['POOL_1']['profile']
    dg = d_testparam['POOL_1']['dg']
    drive_number = d_testparam['POOL_1']['drive_number']
    pool_type = d_testparam['POOL_1']['type']
    #
    host_name = d_testparam['HOST_1']['name']
    host_ip = d_testparam['HOST_1']['name']

    LOG.print_log('INFO', "Teardown test environment...")

    ### --------------- Storage Part --------------- ###
    ######
    LOG.print_step('Remove the iscsi interface.')
    # TODO

    ######
    LOG.print_step('Remove the pool.')
    # TODO

    ### --------------- Host Part --------------- ###
    LOG.print_step('Teardown iscsi connection from the host.')
    # TODO
    ###### Test Only ######
    # host = Host(storage, io_host, host_name, host_ip)
    # host.get_host_profile()
    # host.iscsi_ip_list = ['10.245.125.145', '10.245.125.146']
    # host.iscsi_iqn_list = ['iqn.1992-04.com.emc:cx.apm00182204089.a1', 'iqn.1992-04.com.emc:cx.apm00182204089.b1']
    # host.teardown_iscsi_connection()


def teardown_test_environment_file(storage, io_host, uemcli_host, windows_host, d_testparam):
    """
    :param storage:
    :param io_host:
    :param uemcli_host:
    :param windows_host:
    :param d_testparam:
    """

    LOG.print_log('INFO', "Teardown test environment...")

    ### --------------- Storage Part --------------- ###
    ######
    LOG.print_step('Remove the nasserver.')
    # TODO

    ######
    LOG.print_step('Remove the pool.')
    # TODO

