from Framework.io_tool import *
from Framework.test_actions import *
from Framework.threads import *
from Framework.space_accounting_checker import *
from Framework.recovery_and_fsck import *

##############################################################################
# Module Variable
##############################################################################

testcase_name = 'TC_VVOL_DR_File_FullClone_FastClone'
LOG = ExecuteLog(testcase_name, LOG_LEVEL, testlog)

##############################################################################
# Test Case Definition
##############################################################################

@tc_symbol_printer(testcase_name)
def TC_VVOL_DR_File_FullClone_FastClone(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object={}):

    # d_storage_object = {}
    # if setup_env:
    #     LOG.print_step('Setup test environment.')
    #     d_storage_object = setup_test_environment(storage, io_host, uemcli_host, windows_host, d_testparam)

    #####
    LOG.print_step('Get the system, storage pool, and datastore.')
    vm_name = d_testparam['VM']['name']

    if d_storage_object.get('VCENTER_1') is not None:
        vcenter = d_storage_object['VCENTER_1']
    else:
        vcenter_ip = d_testparam['VCENTER_1']['ip']
        vcenter_username = d_testparam['VCENTER_1']['username']
        vcenter_password = d_testparam['VCENTER_1']['password']
        vcenter = VCenter(storage, vcenter_ip, vcenter_username, vcenter_password)

    system = System(storage)

    if d_storage_object.get('POOL_1') is not None:
        pool = d_storage_object['POOL_1']
    else:
        pool_name = d_testparam['POOL_1']['name']
        pool = Pool(storage, pool_name)

    datastores = []
    if d_storage_object.get('VVOL_DATASTORE_4') is not None:
        datastore = d_storage_object['VVOL_DATASTORE_4']
        datastore.get_ds_profile()
    else:
        ds_name = d_testparam['VVOL_DATASTORE_4']['name'] + storage.name
        datastore = Datastore(storage, ds_name)
        datastore.get_ds_profile()
    datastores.append(datastore)

    file_disk_size = [10, 20, 30, 40]
    # file_disk_size = [50]
    file_selected_size = [50]

    # ######
    # LOG.print_step('Power off the virtual machine.')
    # poweroff_vm(vm_name, windows_host)
    #
    # for ds in datastores:
    #     ds_name = ds.name
    #     disk_size = block_disk_size
    #
    #     LOG.print_step('Remove hard disks on datastore.')
    #     vm_name = d_testparam['VM']['name']
    #     remove_all_harddisk_in_datastore(vm_name, ds_name, windows_host)
    #
    #     LOG.print_step('Create harddisks for virtual machine.')
    #     storage_policy_1 = 'CompressionAndDedup_New'
    #     create_harddisk(vm_name, ds_name, storage_policy_1, disk_size, vcenter, windows_host)
    #
    # LOG.print_step('Power on the virtual machine.')
    # vm_name = d_testparam['VM']['name']
    # poweron_vm(vm_name, windows_host)
    # time.sleep(30)

    #####
    LOG.print_step('Select the primary data vvol, CBFS, pool allocation, datastore, pool and system for test.')

    d_cbfs_vvol, d_datastore_vvol, \
    test_primary_vvol, test_cbfs, test_poolalloc = \
        collect_vvol_cbfs_poolallocation_from_datastore(storage, datastores, [file_selected_size], [file_disk_size], vm_uuid=None)

    test_primary_vvol = []
    block_selected_size = []
    for cbfsid in d_cbfs_vvol.keys():
        for vvol in d_cbfs_vvol[cbfsid]:
            test_primary_vvol.append(vvol)
            #
            vvol_used_kb, _ = get_size_in_kb_human(vvol.profile['Size'])
            vvol_used_gb = B_to_GB(vvol_used_kb)
            block_selected_size.append(int(vvol_used_gb))

    test_datastore = datastores
    test_pool = [pool]
    test_system = [system]

    ######
    LOG.print_step('Check test objects for each level.')

    LOG.print_log('INFO', 'Selected {} VVol in test_primary_vvol:'.format(len(test_primary_vvol)))
    LOG.print_plain_log('INFO', [(vvol.uuid, vvol.profile['Size']) for vvol in test_primary_vvol])

    LOG.print_log('INFO', 'Selected {} CBFS in test_cbfs:'.format(len(test_cbfs)))
    LOG.print_plain_log('INFO', [obj.identifier for obj in test_cbfs])

    LOG.print_log('INFO', 'Selected {} Poolallocation in test_poolalloc:'.format(len(test_poolalloc)))
    LOG.print_plain_log('INFO', [obj.identifier for obj in test_poolalloc])

    LOG.print_log('INFO', 'Selected {} Datastore test_datastore:'.format(len(test_datastore)))
    LOG.print_plain_log('INFO', [obj.identifier for obj in test_datastore])

    LOG.print_log('INFO', 'Selected {} Pool test_pool:'.format(len(test_pool)))
    LOG.print_plain_log('INFO', [obj.identifier for obj in test_pool])

    LOG.print_log('INFO', 'Selected {} System test_system:'.format(len(test_system)))
    LOG.print_plain_log('INFO', [obj.identifier for obj in test_system])