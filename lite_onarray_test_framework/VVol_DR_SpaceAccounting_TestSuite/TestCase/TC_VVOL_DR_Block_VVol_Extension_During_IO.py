from Framework.io_tool import *
from Framework.test_actions import *
from Framework.threads import *
from Framework.space_accounting_checker import *
from Framework.recovery_and_fsck import *


##############################################################################
# Module Variable
##############################################################################

testcase_name = 'TC_VVOL_DR_Block_VVol_Extension_During_IO'
LOG = ExecuteLog(testcase_name, LOG_LEVEL, testlog)

##############################################################################
# Test Case Definition
##############################################################################

@tc_symbol_printer(testcase_name)
def TC_VVOL_DR_Block_VVol_Extension_During_IO(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object={}):

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
    if d_storage_object.get('VVOL_DATASTORE_2') is not None:
        datastore = d_storage_object['VVOL_DATASTORE_2']
        datastore.get_ds_profile()
    else:
        ds_name = d_testparam['VVOL_DATASTORE_2']['name'] + storage.name
        datastore = Datastore(storage, ds_name)
        datastore.get_ds_profile()
    datastores.append(datastore)

    test_disk_size = 10    # GB
    disk_num = 4           # Num of hard disks to create
    sa_assert = True       # If do assert in SA checker
    sleep_time = 300       # Sleep time before check SA

    n = int(test_disk_size // 10)
    block_disk_size = [(test_disk_size + i) for i in range(0, disk_num)]
    block_selected_size = [test_disk_size]

    # DEBUG
    # new_size = 30
    # block_disk_size[0] = new_size
    # block_selected_size[0] = new_size
    # block_disk_size[:] = block_disk_size[1:]
    # block_selected_size = [13]

    ######
    LOG.print_step('Power off the virtual machine.')
    poweroff_vm(vm_name, windows_host)

    for ds in datastores:
        ds_name = ds.name
        disk_size = block_disk_size

        LOG.print_step('Remove hard disks on datastore.')
        vm_name = d_testparam['VM']['name']
        remove_all_harddisk_in_datastore(vm_name, ds_name, windows_host)

        LOG.print_step('Create harddisks for virtual machine.')
        storage_policy_1 = 'CompressionAndDedup_New'
        create_harddisk(vm_name, ds_name, storage_policy_1, disk_size, vcenter, windows_host)

    LOG.print_step('Power on the virtual machine.')
    vm_name = d_testparam['VM']['name']
    poweron_vm(vm_name, windows_host)
    time.sleep(120)

    #####
    LOG.print_step('Select the primary data vvol, CBFS, pool allocation, datastore, pool and system for test.')

    d_cbfs_vvol, d_datastore_vvol, \
    test_primary_vvol, test_cbfs, test_poolalloc = \
        collect_vvol_cbfs_poolallocation_from_datastore(storage, datastores, [block_disk_size], [block_selected_size])

    fsid = test_cbfs[0].fsid
    for vvol in d_cbfs_vvol[fsid]:
        vvol_used_kb, _ = get_size_in_kb_human(vvol.profile['Size'])
        vvol_used_gb = B_to_GB(vvol_used_kb)
        if vvol_used_gb != block_selected_size[0]:
            LOG.print_log('INFO', 'Find VVol - ({}, {}) in the same CBFS, add it to test_primary_vvol.'.format(vvol.uuid, vvol.profile['Size']))
            test_primary_vvol.append(vvol)
            block_selected_size.append(int(vvol_used_gb))

    test_datastore = datastores
    test_pool = [pool]
    test_system = [system]

    pool_last_spaceaccounting = {}

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

    assert len(test_primary_vvol) == 2, "[Assert Error] The number of test_primary_vvol should be 2!"
    assert len(test_cbfs) == 1, "[Assert Error] The number of test_cbfs should be 1!"
    assert len(test_poolalloc) == 1, "[Assert Error] The number of test_poolalloc should be 1!"
    assert len(test_datastore) == 1, "[Assert Error] The number of test_datastore should be 1!"
    assert len(test_pool) == 1, "[Assert Error] The number of test_pool should be 1!"
    assert len(test_system) == 1, "[Assert Error] The number of test_system should be 1!"

    #####
    LOG.print_step('Check space accounting for related level.')

    do_assert = sa_assert
    # --- VVOL
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[0, 0], symbols=['=', '='], deviation=0.1)
    d_compare_profile['size'] = compare_profile(values_to_compare=block_selected_size, symbols=['=', '='], deviation=0.1)
    used, saving = check_vvol_space(test_primary_vvol, d_compare_profile, do_assert=do_assert)

    # --- CBFS
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[0], symbols=['='], deviation=0.15)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[0], symbols=['='], deviation=0.1)
    used, saving, nAUsNeededIfNoCompression, nPatternZeroMatched, nPatternNonZeroMatched, nDedupMappingPointers = \
    check_cbfs_space(test_cbfs, d_compare_profile, do_assert=do_assert)

    # --- POOL ALLOCATION
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[0], symbols=['='], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[0], symbols=['='], deviation=0.1)
    used, saving = check_poolalloc_space(test_poolalloc, d_compare_profile, do_assert=do_assert)

    # --- DATASTORE
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[0], symbols=['>'], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_datastore_space(test_datastore, d_compare_profile, do_assert=do_assert)

    # --- POOL
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[12], symbols=['>'], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[0], symbols=['='], deviation=0.1)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=[0], symbols=['='], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_pool_space(test_pool, d_compare_profile, do_assert=do_assert)

    pool_last_spaceaccounting = {}
    pool_last_spaceaccounting['used'] = used
    pool_last_spaceaccounting['saving'] = saving
    pool_last_spaceaccounting['saving_percent'] = saving_percent
    pool_last_spaceaccounting['saving_ratio'] = saving_ratio

    # --- SYSTEM
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=used, symbols=['='], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=saving, symbols=['='], deviation=0.1)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=saving_percent, symbols=['='], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_system_space(test_system, d_compare_profile, do_assert=do_assert)

    #####
    LOG.print_step('Start IO to the primary data vvol.')

    origin_file_path = './io_config_file/device_write_25comp_0dedup_read_no_offset_0-10g.vdb'
    updated_file_path = './io_config_file/new_vvol_write_25comp_0dedup_read_no_offset_0-10g.vdb'
    vdbench = VDBench(io_host)
    updated_workload_parameter_file = \
        vdbench.vdbench_prepare_vdb_file_for_device(block_selected_size[0], origin_file_path, updated_file_path)
    vdbench.vdbench_init_and_start_io(updated_workload_parameter_file)
    time.sleep(sleep_time)

    ######
    LOG.print_step('Check space accounting for related level.')

    do_assert = sa_assert
    # --- VVOL
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[10 * n, 0 * n], symbols=['=', '='], deviation=0.1)
    d_compare_profile['size'] = compare_profile(values_to_compare=block_selected_size, symbols=['=', '='], deviation=0.1)
    used, saving = check_vvol_space(test_primary_vvol, d_compare_profile, do_assert=do_assert)

    # --- CBFS
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=[10 * n], symbols=['='], deviation=0.2)
    d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=[0 * n], symbols=['='], deviation=0.2)
    used, saving, nAUsNeededIfNoCompression, nPatternZeroMatched, nPatternNonZeroMatched, nDedupMappingPointers = \
    check_cbfs_space(test_cbfs, d_compare_profile, do_assert=do_assert)

    # --- POOL ALLOCATION
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n], symbols=['='], deviation=0.2)
    used, saving = check_poolalloc_space(test_poolalloc, d_compare_profile, do_assert=do_assert)

    # --- DATASTORE
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n], symbols=['>'], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_datastore_space(test_datastore, d_compare_profile, do_assert=do_assert)

    # --- POOL
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[12 + 7.5 * n], symbols=['>'], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=[0], symbols=['>'], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['>='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_pool_space(test_pool, d_compare_profile, do_assert=do_assert)

    pool_last_spaceaccounting = {}
    pool_last_spaceaccounting['used'] = used
    pool_last_spaceaccounting['saving'] = saving
    pool_last_spaceaccounting['saving_percent'] = saving_percent
    pool_last_spaceaccounting['saving_ratio'] = saving_ratio

    # --- SYSTEM
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=used, symbols=['='], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=saving, symbols=['='], deviation=0.1)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=saving_percent, symbols=['='], deviation=0.1)
    # d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['>='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_system_space(test_system, d_compare_profile, do_assert=do_assert)

    ######
    LOG.print_step('Power off the virtual machine.')
    poweroff_vm(vm_name, windows_host)

    ######
    LOG.print_step('Extend the harddisk size in the vm.')
    new_size = 30
    origin_size_list = [test_disk_size]
    new_size_list = [new_size]
    set_harddisk_size(vm_name, ds_name, windows_host, origin_size_list, new_size_list)

    test_primary_vvol[0].get_vvol_profile()
    block_selected_size[0] = new_size

    ######
    LOG.print_step('Power on the virtual machine.')
    vm_name = d_testparam['VM']['name']
    poweron_vm(vm_name, windows_host)
    time.sleep(sleep_time)

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

    assert len(test_primary_vvol) == 2, "[Assert Error] The number of test_primary_vvol should be 2!"
    assert len(test_cbfs) == 1, "[Assert Error] The number of test_cbfs should be 1!"
    assert len(test_poolalloc) == 1, "[Assert Error] The number of test_poolalloc should be 1!"
    assert len(test_datastore) == 1, "[Assert Error] The number of test_datastore should be 1!"
    assert len(test_pool) == 1, "[Assert Error] The number of test_pool should be 1!"
    assert len(test_system) == 1, "[Assert Error] The number of test_system should be 1!"

    ######
    LOG.print_step('Check space accounting for related level.')

    do_assert = sa_assert
    # --- VVOL
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[10 * n, 0 * n], symbols=['=', '='], deviation=0.1)
    d_compare_profile['size'] = compare_profile(values_to_compare=block_selected_size, symbols=['=', '='], deviation=0.1)
    used, saving = check_vvol_space(test_primary_vvol, d_compare_profile, do_assert=do_assert)

    # --- CBFS
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=[10 * n], symbols=['='], deviation=0.2)
    d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=[0 * n], symbols=['='], deviation=0.2)
    used, saving, nAUsNeededIfNoCompression, nPatternZeroMatched, nPatternNonZeroMatched, nDedupMappingPointers = \
    check_cbfs_space(test_cbfs, d_compare_profile, do_assert=do_assert)

    # --- POOL ALLOCATION
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n], symbols=['='], deviation=0.2)
    used, saving = check_poolalloc_space(test_poolalloc, d_compare_profile, do_assert=do_assert)

    # --- DATASTORE
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n], symbols=['>'], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_datastore_space(test_datastore, d_compare_profile, do_assert=do_assert)

    # --- POOL
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[12 + 7.5 * n], symbols=['>'], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=[0], symbols=['>'], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['>='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_pool_space(test_pool, d_compare_profile, do_assert=do_assert)

    pool_last_spaceaccounting = {}
    pool_last_spaceaccounting['used'] = used
    pool_last_spaceaccounting['saving'] = saving
    pool_last_spaceaccounting['saving_percent'] = saving_percent
    pool_last_spaceaccounting['saving_ratio'] = saving_ratio

    # --- SYSTEM
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=used, symbols=['='], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=saving, symbols=['='], deviation=0.1)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=saving_percent, symbols=['='], deviation=0.1)
    # d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['>='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_system_space(test_system, d_compare_profile, do_assert=do_assert)

    #####
    LOG.print_step('Start IO to the extended data vvol and the data vvol in the same CBFS.')

    #
    LOG.print_log('INFO', "Ensure VDBench daemon process is started.")
    vdbench = VDBench(io_host)
    vdbench.vdbench_start_rsh_deamon()

    #
    def vdbench_thread_task(origin_file_path, vvol_size, thread_name):
        assert type(origin_file_path) is str and len(origin_file_path) > 0, \
            "[Assert Error] Input origin_file_path:{} should be a string!".format(origin_file_path)
        assert type(vvol_size) is int and vvol_size >= test_disk_size, \
            "[Assert Error] Input device_size:{} should be an int and should be larger than {}!".format(vvol_size, test_disk_size)

        file_name = os.path.basename(origin_file_path).replace('device', 'new_vvol')
        updated_file_path = os.path.dirname(origin_file_path) + '/' + file_name
        vdbench = VDBench(io_host, thread_name=thread_name)
        updated_workload_parameter_file = \
            vdbench.vdbench_prepare_vdb_file_for_device(vvol_size, origin_file_path, updated_file_path)
        vdbench.vdbench_init_and_start_io(updated_workload_parameter_file)
        time.sleep(sleep_time)

    #
    my_threads = []

    LOG.print_log('INFO', "Create a thread to start IO to extended vvol.")
    vvol_size = block_selected_size[0]
    name = 'IOToVVol{}'.format(vvol_size)
    origin_file_path = './io_config_file/device_write_50comp_0dedup_read_no_offset_10-20g.vdb'
    t = MyThread(task_function=vdbench_thread_task, task_args=(origin_file_path, vvol_size,), name=name)
    LOG.print_log('INFO', "Start the thread {} for running...".format(name))
    t.start()
    t.check_thread_alive()
    my_threads.append(t)

    LOG.print_log('INFO', "Create a thread to start IO to vvol in the same CBFS.")
    vvol_size = block_selected_size[1]
    name = 'IOToVVol{}'.format(vvol_size)
    origin_file_path = './io_config_file/device_write_50comp_0dedup_read_no_offset_0-10g.vdb'
    t = MyThread(task_function=vdbench_thread_task, task_args=(origin_file_path, vvol_size,), name=name)
    LOG.print_log('INFO', "Start the thread {} for running...".format(name))
    t.start()
    t.check_thread_alive()
    my_threads.append(t)

    LOG.print_log('INFO', "Waiting for the threads to complete...")
    for t in my_threads:
        t.join()

    LOG.print_log('INFO', "IO to VVols are done.")

    ######
    LOG.print_step('Check space accounting for related level.')

    do_assert = sa_assert
    # --- VVOL
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[20 * n, 10 * n], symbols=['=', '='], deviation=0.1)
    d_compare_profile['size'] = compare_profile(values_to_compare=block_selected_size, symbols=['=', '='], deviation=0.1)
    used, saving = check_vvol_space(test_primary_vvol, d_compare_profile, do_assert=do_assert)

    # --- CBFS
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n + 5 * n + 5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n + 5 * n + 5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=[10 * n + 10 * n + 10 * n], symbols=['='], deviation=0.2)
    d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=[0 * n], symbols=['='], deviation=0.2)
    used, saving, nAUsNeededIfNoCompression, nPatternZeroMatched, nPatternNonZeroMatched, nDedupMappingPointers = \
    check_cbfs_space(test_cbfs, d_compare_profile, do_assert=do_assert)

    # --- POOL ALLOCATION
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n + 5 * n + 5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n + 5 * n + 5 * n], symbols=['='], deviation=0.2)
    used, saving = check_poolalloc_space(test_poolalloc, d_compare_profile, do_assert=do_assert)

    # --- DATASTORE
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n + 5 * n + 5 * n], symbols=['>'], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_datastore_space(test_datastore, d_compare_profile, do_assert=do_assert)

    # --- POOL
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[12 + 7.5 * n + 5 * n + 5 * n], symbols=['>'], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n + 5 * n + 5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=pool_last_spaceaccounting['saving_percent'], symbols=['>'], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=pool_last_spaceaccounting['saving_ratio'], symbols=['>='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_pool_space(test_pool, d_compare_profile, do_assert=do_assert)

    pool_last_spaceaccounting = {}
    pool_last_spaceaccounting['used'] = used
    pool_last_spaceaccounting['saving'] = saving
    pool_last_spaceaccounting['saving_percent'] = saving_percent
    pool_last_spaceaccounting['saving_ratio'] = saving_ratio

    # --- SYSTEM
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=used, symbols=['='], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=saving, symbols=['='], deviation=0.1)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=saving_percent, symbols=['='], deviation=0.1)
    # d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['>='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_system_space(test_system, d_compare_profile, do_assert=do_assert)

    ######
    LOG.print_step('Take a snapshot for the vm.')
    snapshot_name = 'snap_100'

    snap_vvols = []
    test_snap_vvol = []

    create_snapshot(vm_name, snapshot_name, windows_host)
    time.sleep(sleep_time)

    fetched = False
    datastore_id = test_datastore[0].profile['ID']
    for vvol in test_primary_vvol:
        vvol_size_b, _ = get_size_in_kb_human(vvol.profile['Size'])
        if not fetched:
            snap_vvol = VVol.find_vvol(storage, datastore_id, vvol_size_b, vvol_type='Data', replica_type='Ready Snap', fetch=True)
            fetched = True
        else:
            snap_vvol = VVol.find_vvol(storage, datastore_id, vvol_size_b, vvol_type='Data', replica_type='Ready Snap', fetch=False)
        snap_vvols.append(snap_vvol)

        # decide which snap to select by yourself
        test_snap_vvol.append(snap_vvol)

    ######
    LOG.print_step('Check test objects for each level.')

    LOG.print_log('INFO', 'Selected {} VVol in test_snap_vvol:'.format(len(test_snap_vvol)))
    LOG.print_plain_log('INFO', [(vvol.uuid, vvol.profile['Size']) for vvol in test_snap_vvol])

    ######
    LOG.print_step('Check space accounting for related level.')

    do_assert = sa_assert
    # --- VVOL
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[20 * n, 10 * n], symbols=['=', '='], deviation=0.1)
    d_compare_profile['size'] = compare_profile(values_to_compare=block_selected_size, symbols=['=', '='], deviation=0.1)
    used, saving = check_vvol_space(test_primary_vvol, d_compare_profile, do_assert=do_assert)
    used, saving = check_vvol_space(test_snap_vvol, d_compare_profile, do_assert=do_assert)

    # --- CBFS
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n + 5 * n + 5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n + 5 * n + 5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=[10 * n + 10 * n + 10 * n], symbols=['='], deviation=0.2)
    d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=[0 * n], symbols=['='], deviation=0.2)
    used, saving, nAUsNeededIfNoCompression, nPatternZeroMatched, nPatternNonZeroMatched, nDedupMappingPointers = \
        check_cbfs_space(test_cbfs, d_compare_profile, do_assert=do_assert)

    # --- POOL ALLOCATION
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n + 5 * n + 5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n + 5 * n + 5 * n], symbols=['='], deviation=0.2)
    used, saving = check_poolalloc_space(test_poolalloc, d_compare_profile, do_assert=do_assert)

    # --- DATASTORE
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[7.5 * n + 5 * n + 5 * n], symbols=['>'], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_datastore_space(test_datastore, d_compare_profile, do_assert=do_assert)

    # --- POOL
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[12 + 7.5 * n + 5 * n + 5 * n], symbols=['>'], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[2.5 * n + 5 * n + 5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=pool_last_spaceaccounting['saving_percent'], symbols=['='], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=pool_last_spaceaccounting['saving_ratio'], symbols=['='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_pool_space(test_pool, d_compare_profile, do_assert=do_assert)

    pool_last_spaceaccounting = {}
    pool_last_spaceaccounting['used'] = used
    pool_last_spaceaccounting['saving'] = saving
    pool_last_spaceaccounting['saving_percent'] = saving_percent
    pool_last_spaceaccounting['saving_ratio'] = saving_ratio

    # --- SYSTEM
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=used, symbols=['='], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=saving, symbols=['='], deviation=0.1)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=saving_percent, symbols=['='], deviation=0.1)
    # d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['>='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_system_space(test_system, d_compare_profile, do_assert=do_assert)

    #####
    LOG.print_step('Run FSCK for VVol.')
    vvol_do_recovery(storage, test_primary_vvol, mode='sequential', check_modify='no')

    ######
    LOG.print_step('Power off the virtual machine.')
    poweroff_vm(vm_name, windows_host)

    ######
    LOG.print_step('Remove snapshot for the virtual machine.')
    remove_snapshot(vm_name, snapshot_name, windows_host)

    for ds in datastores:
        ds_name = ds.name
        LOG.print_step('Remove hard disks in datastore {}...'.format(ds_name))
        remove_harddisk(vm_name, ds_name, windows_host, size_list=[new_size])

    time.sleep(sleep_time)

    test_primary_vvol[:] = test_primary_vvol[1:]
    block_selected_size[:] = block_selected_size[1:]

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

    assert len(test_primary_vvol) == 1, "[Assert Error] The number of test_primary_vvol should be 1!"
    assert len(test_cbfs) == 1, "[Assert Error] The number of test_cbfs should be 1!"
    assert len(test_poolalloc) == 1, "[Assert Error] The number of test_poolalloc should be 1!"
    assert len(test_datastore) == 1, "[Assert Error] The number of test_datastore should be 1!"
    assert len(test_pool) == 1, "[Assert Error] The number of test_pool should be 1!"
    assert len(test_system) == 1, "[Assert Error] The number of test_system should be 1!"

    ######
    LOG.print_step('Check space accounting for related level.')

    do_assert = sa_assert
    # --- VVOL
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[10 * n], symbols=['='], deviation=0.1)
    d_compare_profile['size'] = compare_profile(values_to_compare=block_selected_size, symbols=['='], deviation=0.1)
    used, saving = check_vvol_space(test_primary_vvol, d_compare_profile, do_assert=do_assert)

    # --- CBFS
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=[10 * n], symbols=['='], deviation=0.2)
    d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=[0 * n], symbols=['='], deviation=0.2)
    used, saving, nAUsNeededIfNoCompression, nPatternZeroMatched, nPatternNonZeroMatched, nDedupMappingPointers = \
        check_cbfs_space(test_cbfs, d_compare_profile, do_assert=do_assert)

    # --- POOL ALLOCATION
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[5 * n], symbols=['='], deviation=0.2)
    used, saving = check_poolalloc_space(test_poolalloc, d_compare_profile, do_assert=do_assert)

    # --- DATASTORE
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[5 * n], symbols=['>'], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_datastore_space(test_datastore, d_compare_profile, do_assert=do_assert)

    # --- POOL
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[12 + 5 * n], symbols=['>'], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[5 * n], symbols=['='], deviation=0.2)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=[0], symbols=['>'], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['>'], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_pool_space(test_pool, d_compare_profile, do_assert=do_assert)

    pool_last_spaceaccounting = {}
    pool_last_spaceaccounting['used'] = used
    pool_last_spaceaccounting['saving'] = saving
    pool_last_spaceaccounting['saving_percent'] = saving_percent
    pool_last_spaceaccounting['saving_ratio'] = saving_ratio

    # --- SYSTEM
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=used, symbols=['='], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=saving, symbols=['='], deviation=0.1)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=saving_percent, symbols=['='], deviation=0.1)
    # d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['>='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_system_space(test_system, d_compare_profile, do_assert=do_assert)

    ######
    for ds in datastores:
        ds_name = ds.name
        LOG.print_step('Remove hard disks in datastore {}...'.format(ds_name))
        remove_all_harddisk_in_datastore(vm_name, ds_name, windows_host)

    time.sleep(sleep_time)

    #####
    LOG.print_step('Check space accounting for related level.')

    do_assert = sa_assert

    # --- POOL ALLOCATION
    d_compare_profile = dict(D1)
    d_compare_profile['used'] = compare_profile(values_to_compare=[0], symbols=['='], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[0], symbols=['='], deviation=0.1)
    used, saving = check_poolalloc_space(test_poolalloc, d_compare_profile, do_assert=do_assert)

    # --- DATASTORE
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[0], symbols=['>'], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_datastore_space(test_datastore, d_compare_profile, do_assert=do_assert)

    # --- POOL
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=[12], symbols=['>'], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=[0], symbols=['='], deviation=0.1)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=[0], symbols=['='], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_pool_space(test_pool, d_compare_profile, do_assert=do_assert)

    pool_last_spaceaccounting = {}
    pool_last_spaceaccounting['used'] = used
    pool_last_spaceaccounting['saving'] = saving
    pool_last_spaceaccounting['saving_percent'] = saving_percent
    pool_last_spaceaccounting['saving_ratio'] = saving_ratio

    # --- SYSTEM
    d_compare_profile = dict(D2)
    d_compare_profile['used'] = compare_profile(values_to_compare=used, symbols=['='], deviation=0.1)
    d_compare_profile['saving'] = compare_profile(values_to_compare=saving, symbols=['='], deviation=0.1)
    d_compare_profile['saving_percent'] = compare_profile(values_to_compare=saving_percent, symbols=['='], deviation=0.1)
    d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
    used, saving, saving_percent, saving_ratio = check_system_space(test_system, d_compare_profile, do_assert=do_assert)


    # ######
    # LOG.print_step('Power off the virtual machine.')
    # poweroff_vm(vm_name, windows_host)
    #
    # for ds in datastores:
    #     ds_name = ds.name
    #     LOG.print_step('Remove hard disks in datastore {}...'.format(ds_name))
    #     remove_all_harddisk_in_datastore(vm_name, ds_name, windows_host)
    #
    #     LOG.print_step('Remove vvols in datastore {} from storage.'.format(ds_name))
    #     ds_id = ds.profile['ID']
    #     vvols_uuid = VVol.find_vvol_uuid_in_datastore(storage_obj=storage, datastore_id=ds_id)
    #     for uuid in vvols_uuid:
    #         remove_vvol(storage, uemcli_host, uuid)


if __name__ == '__main__':
    pass

