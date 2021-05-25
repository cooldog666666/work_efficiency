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

def setup_test_environment_vvoldr(storage, io_host, uemcli_host, windows_host, d_testparam):
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
    pool_name = d_testparam['POOL_1']['name']
    profile = d_testparam['POOL_1']['profile']
    dg = d_testparam['POOL_1']['dg']
    drive_number = d_testparam['POOL_1']['drive_number']

    nasserver_name = d_testparam['NASSERVER_1']['name']
    nasserver_pool = d_testparam['NASSERVER_1']['pool']
    nasserver_sp = d_testparam['NASSERVER_1']['sp']
    nasserver_sharing_protocol = d_testparam['NASSERVER_1']['sharing_protocol']

    # cp_params = [
    #     {
    #         'name': d_testparam['CP_1']['name'],
    #         'pool': d_testparam['CP_1']['pool'],
    #         'data_reduction': d_testparam['CP_1']['data_reduction'],
    #         'advanced_dedup': d_testparam['CP_1']['advanced_dedup'],
    #     },
    #     {
    #         'name': d_testparam['CP_2']['name'],
    #         'pool': d_testparam['CP_2']['pool'],
    #         'data_reduction': d_testparam['CP_2']['data_reduction'],
    #         'advanced_dedup': d_testparam['CP_2']['advanced_dedup'],
    #     },
    # ]

    datastore1_name = d_testparam['VVOL_DATASTORE_1']['name'] + storage.name
    datastore1_type = d_testparam['VVOL_DATASTORE_1']['type']
    datastore1_cp = str(d_testparam['VVOL_DATASTORE_1']['cp']).split(',')
    datastore1_size = str(d_testparam['VVOL_DATASTORE_1']['size']).split(',')
    datastore1_host = d_testparam['VVOL_DATASTORE_1']['host']

    datastore2_name = d_testparam['VVOL_DATASTORE_2']['name'] + storage.name
    datastore2_type = d_testparam['VVOL_DATASTORE_2']['type']
    datastore2_cp = str(d_testparam['VVOL_DATASTORE_2']['cp']).split(',')
    datastore2_size = str(d_testparam['VVOL_DATASTORE_2']['size']).split(',')
    datastore2_host = d_testparam['VVOL_DATASTORE_2']['host']

    datastore3_name = d_testparam['VVOL_DATASTORE_3']['name'] + storage.name
    datastore3_type = d_testparam['VVOL_DATASTORE_3']['type']
    datastore3_cp = str(d_testparam['VVOL_DATASTORE_3']['cp']).split(',')
    datastore3_size = str(d_testparam['VVOL_DATASTORE_3']['size']).split(',')
    datastore3_host = d_testparam['VVOL_DATASTORE_3']['host']

    datastore4_name = d_testparam['VVOL_DATASTORE_4']['name'] + storage.name
    datastore4_type = d_testparam['VVOL_DATASTORE_4']['type']
    datastore4_cp = str(d_testparam['VVOL_DATASTORE_4']['cp']).split(',')
    datastore4_size = str(d_testparam['VVOL_DATASTORE_4']['size']).split(',')
    datastore4_host = d_testparam['VVOL_DATASTORE_4']['host']

    vcenter_ip = d_testparam['VCENTER_1']['ip']
    vcenter_username = d_testparam['VCENTER_1']['username']
    vcenter_password = d_testparam['VCENTER_1']['password']
    esxhost_ip = d_testparam['ESXHOST_1']['ip']

    ######
    LOG.print_step('Create a storage pool.')
    create_pool(storage, pool_name, profile, dg, drive_number)
    pool = Pool(storage, pool_name)
    pool.get_pool_profile()
    d_storage_object['POOL_1'] = pool

    ######
    LOG.print_step('Create iscsi interfaces.')
    LOG.print_log('INFO', "storage available port: {}".format(storage.available_port))
    LOG.print_log('INFO', "storage available io ip: {}".format(storage.available_ioip))
    netmask = storage.netmask
    gateway = storage.gateway
    vlan = storage.vlan
    for _ in range(2):
        port = storage.available_port.pop()
        ioip = storage.available_ioip.pop()
        create_iscsi_interface(storage, port, ioip, netmask, gateway, vlan)

    #####
    LOG.print_step('Add vCenter and ESXi Host.')

    LOG.print_log('INFO', "Add vCenter {} to the storage.".format(vcenter_ip))
    add_vcenter(storage, vcenter_ip, vcenter_username, vcenter_password, register_vasa_provider='yes')
    vcenter = VCenter(storage, vcenter_ip, vcenter_username, vcenter_password)
    vcenter.get_vcenter_profile()
    vcenter_id = vcenter.profile['ID']
    LOG.print_log('INFO', "Get vcenter_id: {}".format(vcenter_id))
    d_storage_object['VCENTER_1'] = vcenter

    LOG.print_log('INFO', "Add ESXi host {} to the storage.".format(vcenter_ip))
    add_esxhost(storage, esxhost_ip, vcenter_id)
    esxhost = ESXHost(storage, esxhost_ip)
    esxhost.get_esxhost_profile()
    esxhost_id = esxhost.profile['ID']
    LOG.print_log('INFO', "Get esxhost_id: {}".format(esxhost_id))
    d_storage_object['ESXHOST_1'] = esxhost

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

    LOG.print_log('INFO', "Create nas nfs vmware pe.")
    create_nas_vmware_pe(storage, nasserver_name, nasserver_ifid)

    d_storage_object['NASSERVER_1'] = nasserver

    ######
    LOG.print_step('Create capability profiles.')
    # TODO: uemcli not support now.
    print('Please create the capability profiles in 5 mins!!!')
    timeout = 300
    while timeout > 0:
        print('There are {} munites left...'.format(int(timeout / 60)))
        timeout -= 60
        time.sleep(60)

    cp_names = [d_testparam['CP_1']['name'], d_testparam['CP_2']['name']]
    cp_objs = []
    for cp_name in cp_names:
        cp = CapabilityProfile(storage, cp_name)
        cp.get_cp_profile()
        cp_objs.append(cp)

    d_storage_object['CP_1'] = cp_objs[0]
    d_storage_object['CP_2'] = cp_objs[1]

    #esxhost_id = 'Host_1'
    ######
    LOG.print_step('Create a compression_off block datastore.')
    d_cp = dict(zip([cp_objs[0].profile['ID']], datastore1_size))
    create_vvol_ds(storage, datastore1_name, datastore1_type, esxhost_id, d_cp)
    datastore = Datastore(storage, datastore1_name)
    datastore.get_ds_profile()
    d_storage_object['VVOL_DATASTORE_1'] = datastore

    ######
    LOG.print_step('Create a compression_and_dedup block datastore.')
    d_cp = dict(zip([_.profile['ID'] for _ in cp_objs], datastore2_size))
    create_vvol_ds(storage, datastore2_name, datastore2_type, esxhost_id, d_cp)
    datastore = Datastore(storage, datastore2_name)
    datastore.get_ds_profile()
    d_storage_object['VVOL_DATASTORE_2'] = datastore

    # ######
    # LOG.print_step('Create a compression_off file datastore.')
    # d_cp = dict(zip([cp_objs[0].profile['ID']], datastore3_size))
    # create_vvol_ds(storage, datastore3_name, datastore3_type, esxhost_id, d_cp)
    # datastore = Datastore(storage, datastore3_name)
    # d_storage_object['VVOL_DATASTORE_3'] = datastore
    #
    # ######
    # LOG.print_step('Create a compression_and_dedup file datastore.')
    # d_cp = dict(zip([_.profile['ID'] for _ in cp_objs], datastore4_size))
    # create_vvol_ds(storage, datastore4_name, datastore4_type, esxhost_id, d_cp)
    # datastore = Datastore(storage, datastore4_name)
    # d_storage_object['VVOL_DATASTORE_4'] = datastore

    ######
    LOG.print_step('Create a virtual machine from template.')

    vm_name = d_testparam['VM']['name']
    template_name = d_testparam['VM']['template']
    ds_name = d_testparam['VVOL_DATASTORE_1']['name'] + storage.name
    create_vm(vm_name, template_name, ds_name, esxhost_ip, windows_host)

    LOG.print_log('INFO', 'Setup test environment done. Get storage objects as following:')
    for k in d_storage_object.keys():
        LOG.print_plain_log('INFO', '{} : {}'.format(k, d_storage_object[k]))

    # Assert before return
    assert isinstance(d_storage_object, dict), "[Assert Error] Variable d_storage_object - {} is not a dict!".format(d_storage_object)

    return d_storage_object


##############################################################################
# Teardown Environment
##############################################################################

def teardown_test_environment_vvoldr(storage, io_host, uemcli_host, windows_host, d_testparam):
    """
    :param storage:
    :param io_host:
    :param uemcli_host:
    :param windows_host:
    :param d_testparam:
    """

    LOG.print_log('INFO', "Teardown test environment...")

    ### --------------- vCenter Part --------------- ###
    ######
    LOG.print_step('Delete the virtual machine.')

    vm_name = d_testparam['VM']['name']
    remove_vm(vm_name, windows_host)

    ######
    LOG.print_step('Unmount the datastore.')
    esx_host_ip = d_testparam['ESXHOST_1']['ip']
    vvol_ds_session = ['VVOL_DATASTORE_1', 'VVOL_DATASTORE_2', 'VVOL_DATASTORE_3', 'VVOL_DATASTORE_4']
    for session in vvol_ds_session:
        ds_name = d_testparam[session]['name'] + storage.name
        unmount_datastore(ds_name, esx_host_ip, windows_host)

    ######
    LOG.print_step('Remove the vasa provider.')
    remove_vasa_provider(storage.mgmt_ip, windows_host)

    ### --------------- Storage Part --------------- ###
    ######
    LOG.print_step('Remove the datastore.')
    # TODO

    ######
    LOG.print_step('Remove the capability profiles.')
    # TODO

    ######
    LOG.print_step('Remove the ESX host.')
    # TODO

    ######
    LOG.print_step('Remove the vCenter.')
    # TODO

    ######
    LOG.print_step('Remove the nasserver.')
    # TODO

    ######
    LOG.print_step('Remove the iscsi interface.')
    # TODO

    ######
    LOG.print_step('Remove the pool.')
    # TODO


