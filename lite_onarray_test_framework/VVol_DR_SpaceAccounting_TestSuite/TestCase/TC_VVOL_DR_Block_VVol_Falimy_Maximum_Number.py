from Framework.io_tool import *
from Framework.test_actions import *
from Framework.threads import *
from Framework.space_accounting_checker import *
from Framework.recovery_and_fsck import *

import random

##############################################################################
# Module Variable
##############################################################################

testcase_name = 'TC_VVOL_DR_Block_VVol_Falimy_Maximum_Number'
LOG = ExecuteLog(testcase_name, LOG_LEVEL, testlog)

##############################################################################
# Test Case Definition
##############################################################################

@tc_symbol_printer(testcase_name)
def TC_VVOL_DR_Block_VVol_Falimy_Maximum_Number(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object={}):

    #####
    LOG.print_step('Get the system, storage pool, and datastore.')
    vm_name = d_testparam['VM']['name']
    storage_policy_1 = 'CompressionAndDedup_New'

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

    ######
    LOG.print_step('Check testcase parameters.')
    sa_assert = True       # If do assert in SA checker
    sleep_time = 300       # Sleep time before check SA

    test_disk_size = 10   # GB
    disk_num = 2           # Num of hard disks to create
    round_num = 21

    n = int(test_disk_size // 10)
    block_disk_size = []
    block_selected_size = []

    cbfs_last_spaceaccounting = {}
    pool_last_spaceaccounting = {}

    total_vvol_num = 0
    total_cbfs_num = 2
    start_disk_size = int(test_disk_size)

    ######
    LOG.print_step('Start {} rounds of create harddisk and do IO testing.'.format(round_num))

    for i in range(0, round_num):
        round_index = i + 1
        round_tag = '--- Round_{} --- '.format(round_index)

        disk_size = [int(_) for _ in range(start_disk_size, start_disk_size + disk_num)]
        start_disk_size += disk_num
        total_vvol_num += disk_num
        if total_vvol_num > 40:
            total_cbfs_num += 2

        ######
        LOG.print_step(round_tag + 'Power off the virtual machine.')
        poweroff_vm(vm_name, windows_host)

        LOG.print_step(round_tag + 'Create harddisks for virtual machine.')
        ds_name = datastores[0].name
        create_harddisk(vm_name, ds_name, storage_policy_1, disk_size, vcenter, windows_host)

        LOG.print_step(round_tag + 'Power on the virtual machine.')
        poweron_vm(vm_name, windows_host)
        time.sleep(120)

        ######
        block_disk_size += disk_size
        block_selected_size += disk_size
        LOG.print_log('INFO', round_tag + '\nblock_disk_size is {}.\nblock_selected_size is {}.'.format(block_disk_size, block_selected_size))

        #####
        LOG.print_step(round_tag + 'Select the primary data vvol, CBFS, pool allocation, datastore, pool and system for test.')

        d_cbfs_vvol, d_datastore_vvol, \
        test_primary_vvol, test_cbfs, test_poolalloc = \
            collect_vvol_cbfs_poolallocation_from_datastore(storage, datastores, [block_disk_size], [block_selected_size])

        test_datastore = datastores
        test_pool = [pool]
        test_system = [system]

        ######
        LOG.print_step(round_tag + 'Check test objects for each level.')

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

        assert len(test_primary_vvol) == total_vvol_num, "[Assert Error] The number of test_primary_vvol should be {}!".format(total_vvol_num)
        assert len(test_cbfs) == total_cbfs_num, "[Assert Error] The number of test_cbfs should be {}!".format(total_cbfs_num)
        assert len(test_poolalloc) == 1, "[Assert Error] The number of test_poolalloc should be 1!"
        assert len(test_datastore) == 1, "[Assert Error] The number of test_datastore should be 1!"
        assert len(test_pool) == 1, "[Assert Error] The number of test_pool should be 1!"
        assert len(test_system) == 1, "[Assert Error] The number of test_system should be 1!"

        #####
        LOG.print_step(round_tag + 'Check space accounting for related level.')

        do_assert = sa_assert
        # --- VVOL
        d_compare_profile = dict(D1)
        d_compare_profile['used'] = compare_profile(values_to_compare=[10 * n] * (total_vvol_num - disk_num) + [0] * disk_num, symbols=['='] * total_vvol_num, deviation=0.1)
        d_compare_profile['size'] = compare_profile(values_to_compare=block_selected_size, symbols=['='] * total_vvol_num, deviation=0.1)
        used, saving = check_vvol_space(test_primary_vvol, d_compare_profile, do_assert=do_assert)

        # --- CBFS
        d_compare_profile = dict(D1)
        if round_index <= 20:
            d_compare_profile['used'] = compare_profile(values_to_compare=[(round_index - 1) * 5 * n] * total_cbfs_num, symbols=['<='] * total_cbfs_num, deviation=0.15)
            d_compare_profile['saving'] = compare_profile(values_to_compare=[(round_index - 1) * 5 * n] * total_cbfs_num, symbols=['>='] * total_cbfs_num, deviation=0.1)
            d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=[(round_index - 1) * 5 * n] * total_cbfs_num, symbols=['>='] * total_cbfs_num, deviation=0.2)
            d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=[0] * total_cbfs_num, symbols=['>='] * total_cbfs_num, deviation=0.2)
        elif round_index > 20:
            verify_used = [20 * 5 * n] * (total_cbfs_num - 2) + [(round_index - 1 - 20) * 5 * n] * 2
            verify_saving = list(verify_used)
            verify_nAUsNeededIfNoCompression = list(verify_used)
            verify_nDedupMappingPointers = [0] * total_cbfs_num
            d_compare_profile['used'] = compare_profile(values_to_compare=verify_used, symbols=['<'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['saving'] = compare_profile(values_to_compare=verify_saving, symbols=['>'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=verify_nAUsNeededIfNoCompression, symbols=['>'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=verify_nDedupMappingPointers, symbols=['>'] * total_cbfs_num, deviation=0.2)

        used, saving, nAUsNeededIfNoCompression, nPatternZeroMatched, nPatternNonZeroMatched, nDedupMappingPointers = \
        check_cbfs_space(test_cbfs, d_compare_profile, do_assert=do_assert)

        # --- POOL ALLOCATION
        d_compare_profile = dict(D1)
        d_compare_profile['used'] = compare_profile(values_to_compare=[(round_index - 1) * (5 * n + 5 * n)], symbols=['<='], deviation=0.1)
        d_compare_profile['saving'] = compare_profile(values_to_compare=[(round_index - 1) * (5 * n + 5 * n)], symbols=['>='], deviation=0.1)
        used, saving = check_poolalloc_space(test_poolalloc, d_compare_profile, do_assert=do_assert)

        # --- DATASTORE
        d_compare_profile = dict(D2)
        symbol = '<'
        if round_index == 1:
            symbol = '>'
        d_compare_profile['used'] = compare_profile(values_to_compare=[(round_index - 1) * (5 * n + 5 * n)], symbols=[symbol], deviation=0.1)
        used, saving, saving_percent, saving_ratio = check_datastore_space(test_datastore, d_compare_profile, do_assert=do_assert)

        # --- POOL
        d_compare_profile = dict(D2)
        d_compare_profile['used'] = compare_profile(values_to_compare=[12 + (round_index - 1) * (5 * n + 5 * n)], symbols=['>'], deviation=0.1)
        d_compare_profile['saving'] = compare_profile(values_to_compare=[(round_index - 1) * (5 * n + 5 * n)], symbols=['>='], deviation=0.1)
        d_compare_profile['saving_percent'] = compare_profile(values_to_compare=[0], symbols=['>='], deviation=0.1)
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
        d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
        used, saving, saving_percent, saving_ratio = check_system_space(test_system, d_compare_profile, do_assert=do_assert)

        #####
        LOG.print_step(round_tag + 'Start IO to the data vvols in different CBFS, create new data vvols during the IO is on-going.')

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

            file_name = os.path.basename(origin_file_path).replace('device', thread_name)
            updated_file_path = os.path.dirname(origin_file_path) + '/' + file_name
            vdbench = VDBench(io_host, thread_name=thread_name)
            updated_workload_parameter_file = \
                vdbench.vdbench_prepare_vdb_file_for_device(vvol_size, origin_file_path, updated_file_path)
            vdbench.vdbench_init_and_start_io(updated_workload_parameter_file)
            time.sleep(sleep_time)

        #
        my_threads = []

        LOG.print_log('INFO', "Create a thread to start IO to data vvol.")
        origin_file_path = './io_config_file/device_write_50comp_50dedup_read_no_offset_0-10g.vdb'
        for vvol_size in disk_size:
            name = 'IOToVVol{}'.format(vvol_size)
            t = MyThread(task_function=vdbench_thread_task, task_args=(origin_file_path, vvol_size,), name=name)
            LOG.print_log('INFO', "Start the thread {} for running...".format(name))
            t.start()
            t.check_thread_alive()
            my_threads.append(t)
            time.sleep(5)

        LOG.print_log('INFO', "Waiting for the threads to complete...")
        for t in my_threads:
            t.join(timeout=1800)
            t.check_thread_not_alive()

        LOG.print_log('INFO', "All threads are completed.")

        ######
        LOG.print_step(round_tag + 'Check space accounting for related level.')

        do_assert = sa_assert
        # --- VVOL
        d_compare_profile = dict(D1)
        d_compare_profile['used'] = compare_profile(values_to_compare=[10 * n] * total_vvol_num, symbols=['='] * total_vvol_num, deviation=0.1)
        d_compare_profile['size'] = compare_profile(values_to_compare=block_selected_size, symbols=['='] * total_vvol_num, deviation=0.1)
        used, saving = check_vvol_space(test_primary_vvol, d_compare_profile, do_assert=do_assert)

        # --- CBFS
        d_compare_profile = dict(D1)
        if round_index <= 20:
            d_compare_profile['used'] = compare_profile(values_to_compare=[round_index * 5 * n, round_index * 5 * n], symbols=['<'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['saving'] = compare_profile(values_to_compare=[round_index * 5 * n, round_index * 5 * n], symbols=['>'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=[round_index * 5 * n, round_index * 5 * n], symbols=['>'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=[0, 0], symbols=['>'] * total_cbfs_num, deviation=0.2)
        elif round_index > 20:
            verify_used = [20 * 5 * n] * (total_cbfs_num - 2) + [(round_index - 20) * 5 * n] * 2
            verify_saving = list(verify_used)
            verify_nAUsNeededIfNoCompression = list(verify_used)
            verify_nDedupMappingPointers = [0] * total_cbfs_num
            d_compare_profile['used'] = compare_profile(values_to_compare=verify_used, symbols=['<'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['saving'] = compare_profile(values_to_compare=verify_saving, symbols=['>'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=verify_nAUsNeededIfNoCompression, symbols=['>'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=verify_nDedupMappingPointers, symbols=['>'] * total_cbfs_num, deviation=0.2)
        used, saving, nAUsNeededIfNoCompression, nPatternZeroMatched, nPatternNonZeroMatched, nDedupMappingPointers = \
        check_cbfs_space(test_cbfs, d_compare_profile, do_assert=do_assert)

        # --- POOL ALLOCATION
        d_compare_profile = dict(D1)
        d_compare_profile['used'] = compare_profile(values_to_compare=[round_index * (5 * n + 5 * n)], symbols=['<'], deviation=0.2)
        d_compare_profile['saving'] = compare_profile(values_to_compare=[round_index * (5 * n + 5 * n)], symbols=['>'], deviation=0.2)
        used, saving = check_poolalloc_space(test_poolalloc, d_compare_profile, do_assert=do_assert)

        # --- DATASTORE
        d_compare_profile = dict(D2)
        d_compare_profile['used'] = compare_profile(values_to_compare=[round_index * (5 * n + 5 * n)], symbols=['<'], deviation=0.1)
        used, saving, saving_percent, saving_ratio = check_datastore_space(test_datastore, d_compare_profile, do_assert=do_assert)

        # --- POOL
        d_compare_profile = dict(D2)
        d_compare_profile['used'] = compare_profile(values_to_compare=[12 + round_index * (2.5 * n + 2.5 * n)], symbols=['>'], deviation=0.1)
        d_compare_profile['saving'] = compare_profile(values_to_compare=[round_index * (5 * n + 5 * n)], symbols=['>'], deviation=0.2)
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
        d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
        used, saving, saving_percent, saving_ratio = check_system_space(test_system, d_compare_profile, do_assert=do_assert)

        ######
        LOG.print_step(round_tag + 'Take a snapshot for the vm.')
        snapshot_name = 'snap_round_{}'.format(round_index)

        create_snapshot(vm_name, snapshot_name, windows_host)
        time.sleep(sleep_time)

        ######
        LOG.print_step(round_tag + 'Check space accounting for related level.')

        do_assert = sa_assert
        # --- VVOL
        d_compare_profile = dict(D1)
        d_compare_profile['used'] = compare_profile(values_to_compare=[10 * n] * total_vvol_num, symbols=['='] * total_vvol_num, deviation=0.1)
        d_compare_profile['size'] = compare_profile(values_to_compare=block_selected_size, symbols=['='] * total_vvol_num, deviation=0.1)
        used, saving = check_vvol_space(test_primary_vvol, d_compare_profile, do_assert=do_assert)

        # --- CBFS
        d_compare_profile = dict(D1)
        if round_index <= 20:
            d_compare_profile['used'] = compare_profile(values_to_compare=[round_index * 5 * n, round_index * 5 * n], symbols=['<', '<'], deviation=0.2)
            d_compare_profile['saving'] = compare_profile(values_to_compare=[round_index * 5 * n, round_index * 5 * n], symbols=['>', '>'], deviation=0.2)
            d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=[round_index * 5 * n, round_index * 5 * n], symbols=['>', '>'], deviation=0.2)
            d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=[0, 0], symbols=['>', '>'], deviation=0.2)
        elif round_index > 20:
            verify_used = [20 * 5 * n] * (total_cbfs_num - 2) + [(round_index - 20) * 5 * n] * 2
            verify_saving = list(verify_used)
            verify_nAUsNeededIfNoCompression = list(verify_used)
            verify_nDedupMappingPointers = [0] * total_cbfs_num
            d_compare_profile['used'] = compare_profile(values_to_compare=verify_used, symbols=['<'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['saving'] = compare_profile(values_to_compare=verify_saving, symbols=['>'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['nAUsNeededIfNoCompression'] = compare_profile(values_to_compare=verify_nAUsNeededIfNoCompression, symbols=['>'] * total_cbfs_num, deviation=0.2)
            d_compare_profile['nDedupMappingPointers'] = compare_profile(values_to_compare=verify_nDedupMappingPointers, symbols=['>'] * total_cbfs_num, deviation=0.2)
        used, saving, nAUsNeededIfNoCompression, nPatternZeroMatched, nPatternNonZeroMatched, nDedupMappingPointers = \
        check_cbfs_space(test_cbfs, d_compare_profile, do_assert=do_assert)

        # --- POOL ALLOCATION
        d_compare_profile = dict(D1)
        d_compare_profile['used'] = compare_profile(values_to_compare=[round_index * (5 * n + 5 * n)], symbols=['<'], deviation=0.2)
        d_compare_profile['saving'] = compare_profile(values_to_compare=[round_index * (5 * n + 5 * n)], symbols=['>'], deviation=0.2)
        used, saving = check_poolalloc_space(test_poolalloc, d_compare_profile, do_assert=do_assert)

        # --- DATASTORE
        d_compare_profile = dict(D2)
        d_compare_profile['used'] = compare_profile(values_to_compare=[round_index * (5 * n + 5 * n)], symbols=['<'], deviation=0.1)
        used, saving, saving_percent, saving_ratio = check_datastore_space(test_datastore, d_compare_profile, do_assert=do_assert)

        # --- POOL
        d_compare_profile = dict(D2)
        d_compare_profile['used'] = compare_profile(values_to_compare=[12 + round_index * (2.5 * n + 2.5 * n)], symbols=['>'], deviation=0.1)
        d_compare_profile['saving'] = compare_profile(values_to_compare=[round_index * (5 * n + 5 * n)], symbols=['>'], deviation=0.2)
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
        d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
        d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[1], symbols=['>='], deviation=0.1)
        used, saving, saving_percent, saving_ratio = check_system_space(test_system, d_compare_profile, do_assert=do_assert)

    #####
    LOG.print_step('Select the primary data vvol, CBFS, pool allocation, datastore, pool and system for test.')

    block_disk_size[:] = [i for i in range(test_disk_size, test_disk_size + disk_num)]
    block_selected_size = list(block_disk_size)

    d_cbfs_vvol, d_datastore_vvol, \
    test_primary_vvol, test_cbfs, test_poolalloc = \
        collect_vvol_cbfs_poolallocation_from_datastore(storage, datastores, [block_disk_size], [block_selected_size])

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

    assert len(test_primary_vvol) == 2, "[Assert Error] The number of test_primary_vvol should be {}!".format(2)
    assert len(test_cbfs) == 2, "[Assert Error] The number of test_cbfs should be {}!".format(2)
    assert len(test_poolalloc) == 1, "[Assert Error] The number of test_poolalloc should be 1!"
    assert len(test_datastore) == 1, "[Assert Error] The number of test_datastore should be 1!"
    assert len(test_pool) == 1, "[Assert Error] The number of test_pool should be 1!"
    assert len(test_system) == 1, "[Assert Error] The number of test_system should be 1!"

    #####
    LOG.print_step('Run FSCK for VVol.')
    fsck_vvol = list(test_primary_vvol[:2])
    vvol_do_recovery(storage, fsck_vvol, mode='sequential', check_modify='no')

    # #####
    # LOG.print_step('Remove the snapshot.')
    # remove_snapshot(vm_name, snapshot_name, windows_host)

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

