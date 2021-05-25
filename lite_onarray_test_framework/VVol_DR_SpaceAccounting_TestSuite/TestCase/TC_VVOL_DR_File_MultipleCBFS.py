from Framework.io_tool import *
from Framework.test_actions import *
from Framework.threads import *
from Framework.space_accounting_checker import *
from Framework.recovery_and_fsck import *

##############################################################################
# Module Variable
##############################################################################

testcase_name = 'TC_VVOL_DR_File_MultipleCBFS'
LOG = ExecuteLog(testcase_name, LOG_LEVEL, testlog)

##############################################################################
# Test Case Definition
##############################################################################

@tc_symbol_printer(testcase_name)
def TC_VVOL_DR_File_MultipleCBFS(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object={}):

    # d_storage_object = {}
    # if setup_env:
    #     LOG.print_step('Setup test environment.')
    #     d_storage_object = setup_test_environment(storage, io_host, uemcli_host, windows_host, d_testparam)

    #####
    LOG.print_step('Get the system, storage pool, and datastore.')
    vm_name = d_testparam['VM']['name']
    esx_host = d_testparam['ESXHOST_1']['ip']

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
    file_selected_size = [20]

    # ######
    # LOG.print_step('Power off the virtual machine.')
    # poweroff_vm(vm_name, windows_host)
    #
    # for ds in datastores:
    #     ds_name = ds.name
    #     disk_size = file_disk_size
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

    # ######
    # LOG.print_step('Power off the virtual machine.')
    # snapshot_name = 'snap_1'
    # remove_snapshot(vm_name, snapshot_name, windows_host)
    #
    ######
    # LOG.print_step('Power off the virtual machine.')
    # poweroff_vm(vm_name, windows_host)

    # for ds in datastores:
    #     ds_name = ds.name
    #     remove_harddisk(vm_name, ds_name, windows_host, size_list=file_selected_size)

    # for ds in datastores:
    #     ds_name = ds.name
    #     LOG.print_step('Remove all hard disks in datastore {}...'.format(ds_name))
    #     remove_all_harddisk_in_datastore(vm_name, ds_name, windows_host)


