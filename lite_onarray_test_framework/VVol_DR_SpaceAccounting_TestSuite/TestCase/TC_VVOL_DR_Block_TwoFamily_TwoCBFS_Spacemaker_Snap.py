from io_tool import *
from test_actions import *
from space_accounting_checker import *
from recovery_and_fsck import *
from setup_environment_vmware import *

##############################################################################
# Module Variable
##############################################################################

testcase_name = 'TC_VVOL_DR_Block_TwoFamily_TwoCBFS_Spacemaker_Snap'
LOG = ExecuteLog(testcase_name, LOG_LEVEL, testlog)

##############################################################################
# Test Case Definition
##############################################################################

@tc_symbol_printer(testcase_name)
def TC_VVOL_DR_Block_TwoFamily_TwoCBFS_Spacemaker_Snap(storage, io_host, uemcli_host, windows_host, d_testparam, setup_env=False):

    d_storage_object = {}
    if setup_env:
        LOG.print_step('Setup test environment.')
        d_storage_object = setup_test_environment(storage, io_host, uemcli_host, windows_host, d_testparam)

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
    if d_storage_object.get('VVOL_DATASTORE_2') is not None:
        datastore = d_storage_object['VVOL_DATASTORE_2']
        datastore.get_ds_profile()
    else:
        ds_name = d_testparam['VVOL_DATASTORE_2']['name'] + storage.name
        datastore = Datastore(storage, ds_name)
        datastore.get_ds_profile()
    datastores.append(datastore)

    block_disk_size = [48, 49, 50]
    selected_size = [48, 50]
    file_disk_size = [48,49,50]

    ######
    LOG.print_step('Power off the virtual machine.')
    poweroff_vm(vm_name, windows_host)
         
    for ds in datastores:
        ds_name = ds.name
        if ds_name.startswith('Block'):
            disk_size = block_disk_size
        elif ds_name.startswith('File'):
            disk_size = file_disk_size
         
        LOG.print_step('Remove hard disks on datastore.')
        vm_name = d_testparam['VM']['name']
        remove_all_harddisk_in_datastore(vm_name, ds_name, windows_host)
         
        LOG.print_step('Create harddisks for virtual machine.')
        storage_policy_1 = 'CompressionAndDedup'
        create_harddisk(vm_name, ds_name, storage_policy_1, disk_size, vcenter, windows_host)
        
    LOG.print_step('Power on the virtual machine.')
    vm_name = d_testparam['VM']['name']
    poweron_vm(vm_name, windows_host)
    time.sleep(30)

    #####
    LOG.print_step('Select the primary data vvol, CBFS, pool allocation, datastore, pool and system for test.')

    d_cbfs_vvol, d_datastore_vvol, \
    test_primary_vvol, test_cbfs, test_poolalloc = \
        collect_vvol_cbfs_poolallocation_from_datastore(storage, datastores, [block_disk_size], [selected_size])

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

    # #####
    LOG.print_step('Start prefill IO to the primary data vvol1.')
       
    origin_file_path = './VVol_DR_SpaceAccounting_TestCase/prefill.vdb'
    updated_file_path = './VVol_DR_SpaceAccounting_TestCase/new_prefill.vdb'
    vdbench = VDBench(io_host)
    updated_workload_parameter_file = \
        vdbench.vdbench_prepare_vdb_file_for_device(selected_size[0], origin_file_path, updated_file_path)
    vdbench.vdbench_init_and_start_io(updated_workload_parameter_file)
       
    LOG.print_step('Start prefill IO to the primary data vvol2.')
       
    origin_file_path = './VVol_DR_SpaceAccounting_TestCase/prefill.vdb'
    updated_file_path = './VVol_DR_SpaceAccounting_TestCase/new_prefill.vdb'
    vdbench = VDBench(io_host)
    updated_workload_parameter_file = \
        vdbench.vdbench_prepare_vdb_file_for_device(selected_size[1], origin_file_path, updated_file_path)
    vdbench.vdbench_init_and_start_io(updated_workload_parameter_file)
       
    LOG.print_step('Start overwrite IO to the primary data vvol1.')
       
    origin_file_path = './VVol_DR_SpaceAccounting_TestCase/overwrite.vdb'
    updated_file_path = './VVol_DR_SpaceAccounting_TestCase/new_overwrite.vdb'
    vdbench = VDBench(io_host)
    updated_workload_parameter_file = \
        vdbench.vdbench_prepare_vdb_file_for_device(selected_size[0], origin_file_path, updated_file_path)
    vdbench.vdbench_init_and_start_io(updated_workload_parameter_file)
       
    LOG.print_step('Start overwrite IO to the primary data vvol2.')
       
    origin_file_path = './VVol_DR_SpaceAccounting_TestCase/overwrite.vdb'
    updated_file_path = './VVol_DR_SpaceAccounting_TestCase/new_overwrite.vdb'
    vdbench = VDBench(io_host)
    updated_workload_parameter_file = \
        vdbench.vdbench_prepare_vdb_file_for_device(selected_size[1], origin_file_path, updated_file_path)
    vdbench.vdbench_init_and_start_io(updated_workload_parameter_file)
    
    LOG.print_step('Check if Spacemaker is working...')       
    def get_Total_AUsRelocated(output_str):
        """
        :param output_str: output of 'TestMluServiceApi.exe "printSpaceMakerStats"'
        :return: Total_AUsRelocated
        """
        assert len(output_str) > 0, "[Assert Error] The given printSpaceMakerStats output is empty!"
        for line in output_str.splitlines():
            m1 = re.search(r'Total AUsRelocated\s+(\d+)', line)        
            if m1:
                Total_AUsRelocated = m1.group(1)
        LOG.print_log('INFO', "Get Total_AUsRelocated:"+Total_AUsRelocated)
        return Total_AUsRelocated
        assert m1, "[Assert Error] can not get the Total_AUsRelocated!"
    def check_AUsRelocated(storage_obj,cbfs_obj_list):
        for i in range(2):
            assert isinstance(storage_obj, Storage), "[Assert Error] Invalid storage_obj!"
            cmd = 'TestMluServiceApi.exe "printSpaceMakerStats"'
            obj = cbfs_obj_list[0]
            assert isinstance(obj, CBFS), "[Assert Error] Input object - {} is invalid!".format(obj)
            output, return_code = run_command_on_storage_check_returncode(storage_obj, cmd, sp_owner=obj.sp_owner)
            Total_AUsRelocated_old = get_Total_AUsRelocated(output)
            LOG.print_log('INFO', "Get Total_AUsRelocated_old:"+Total_AUsRelocated_old)
            time.sleep(300)
            output, return_code = run_command_on_storage_check_returncode(storage_obj, cmd, sp_owner=obj.sp_owner)
            Total_AUsRelocated_new = get_Total_AUsRelocated(output)
            LOG.print_log('INFO', "Get Total_AUsRelocated_new:"+Total_AUsRelocated_new)
            assert  int(Total_AUsRelocated_new) - int(Total_AUsRelocated_old) > 0, "[Assert Error] Spacemaker is not working!"
            LOG.print_log('INFO', "Spacemaker is working...")    
    check_AUsRelocated(storage,test_cbfs)    

    ######
    LOG.print_step('Take a snapshot for the vm.')
    snapshot_name = 'snap_1'
    snap_vvols = []
    test_snap_vvol = []

    create_snapshot(vm_name, snapshot_name, windows_host)
    time.sleep(5)

    fetched = False
    datastore_id = test_datastore[0].profile['ID']
    for vvol_size in block_disk_size:
        vvol_size_b = GB_to_B(vvol_size)
        if not fetched:
            snap_vvol = VVol.find_vvol(storage, datastore_id, vvol_size_b, vvol_type='Data', replica_type='Ready Snap', fetch=True)
            fetched = True
        else:
            snap_vvol = VVol.find_vvol(storage, datastore_id, vvol_size_b, vvol_type='Data', replica_type='Ready Snap', fetch=False)
        snap_vvols.append(snap_vvol)
        if vvol_size == 50 or vvol_size == 48:
            test_snap_vvol.append(snap_vvol)
            snap_vvol.get_vvol_profile()
            snap_vvol.get_vvol_mlucli_profile()

    ######
    LOG.print_step('Check test objects for each level.')

    LOG.print_log('INFO', 'Selected {} VVol in test_snap_vvol:'.format(len(test_snap_vvol)))
    LOG.print_plain_log('INFO', [(vvol.uuid, vvol.profile['Size']) for vvol in test_snap_vvol])
    
    LOG.print_step('Start overwrite IO to the primary data vvol1.')     
    origin_file_path = './VVol_DR_SpaceAccounting_TestCase/overwrite.vdb'
    updated_file_path = './VVol_DR_SpaceAccounting_TestCase/new_overwrite.vdb'
    vdbench = VDBench(io_host)
    updated_workload_parameter_file = \
        vdbench.vdbench_prepare_vdb_file_for_device(selected_size[0], origin_file_path, updated_file_path)
    vdbench.vdbench_init_and_start_io(updated_workload_parameter_file)
      
    LOG.print_step('Start overwrite IO to the primary data vvol2.')
      
    origin_file_path = './VVol_DR_SpaceAccounting_TestCase/overwrite.vdb'
    updated_file_path = './VVol_DR_SpaceAccounting_TestCase/new_overwrite.vdb'
    vdbench = VDBench(io_host)
    updated_workload_parameter_file = \
        vdbench.vdbench_prepare_vdb_file_for_device(selected_size[1], origin_file_path, updated_file_path)
    vdbench.vdbench_init_and_start_io(updated_workload_parameter_file)
    
    LOG.print_step('Power off the virtual machine.')
    poweroff_vm(vm_name, windows_host)
    #####
    LOG.print_step('Restore the primary data vvol1 with the snap vvol.')
     
    snap_vvol = test_snap_vvol[0]
    snap_vvol.restore_snap_vvol()
     
    LOG.print_step('Restore the primary data vvol2 with the snap vvol.')
     
    snap_vvol = test_snap_vvol[1]
    snap_vvol.restore_snap_vvol()

    LOG.print_step('Run FSCK for VVol.')
    vvol_do_recovery(storage, test_primary_vvol, mode='sequential', check_modify='no')

    #####
    LOG.print_step('Delete the snap for the vm.')
    remove_snapshot(vm_name, snapshot_name, windows_host)

if __name__ == '__main__':
    pass

