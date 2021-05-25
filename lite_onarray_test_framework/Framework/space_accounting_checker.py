from Framework.component import *
from Framework.unit_convert_and_assert_tool import *

##############################################################################
# Module Variable
##############################################################################

LOG = ExecuteLog('sapce_accounting_checker', LOG_LEVEL, testlog)

VERIFY_LIST_1 = ['used', 'saving', 'size']
VERIFY_LIST_2 = ['used', 'saving', 'saving_percent', 'saving_ratio']
VERIFY_LIST_CBFS = ['used', 'saving', 'nAUsNeededIfNoCompression', 'nPatternZeroMatched', 'nPatternNonZeroMatched', 'nDedupMappingPointers']
D1 = {}.fromkeys(VERIFY_LIST_1, None)
D2 = {}.fromkeys(VERIFY_LIST_2, None)
D_CBFS = {}.fromkeys(VERIFY_LIST_CBFS, None)
compare_profile = collections.namedtuple('compare_profile', ['values_to_compare', 'symbols', 'deviation'])
SYMBOL = ['=', '>', '<', '>=', '<=']


##############################################################################
# Internal Function
##############################################################################

def check_space_do_assert(symbol, actual, compare, deviation):
    if symbol == '=':
        assert_equal(actual, compare, deviation=deviation)
    elif symbol == '>':
        assert_greater(actual, compare)
    elif symbol == '<':
        assert_smaller(actual, compare)
    elif symbol == '>=':
        assert_greater_or_equal(actual, compare)
    elif symbol == '<=':
        assert_smaller_or_equal(actual, compare)

##############################################################################
# Common Function
##############################################################################

def get_space_saving_from_cbfs_fsInfo(output_str):
    """
    :param output_str: output of 'TestMluServiceApi.exe "fsInfo fsid=1073741835"'
    :return: d_cbfs_sapcesaving = {
             'nAUsNeededIfNoCompression': '',
             'nPatternZeroMatched': '',
             'nPatternNonZeroMatched': '',
             'nDedupMappingPointers': '',
             'DataBlocksNeededIfNoCompression': '',
             'overheadAllocated': '',
             'spaceSaving': '',
             'spaceSaving_in_slice': '',
             'DataBlocksNeededIfNoCompression_in_slice': '',
             'overheadAllocated_in_slice': '',
             }
    """
    assert len(output_str) > 0, "[Assert Error] The given cbfs fsInfo output is empty!"

    d_cbfs_sapcesaving = {}
    for line in output_str.splitlines():
        m1 = re.search(r'nAUsNeededIfNoCompression.*\s+(\d+)', line)
        m2 = re.search(r'nPatternZeroMatched.*\s+(\d+)', line)
        m3 = re.search(r'nPatternNonZeroMatched.*\s+(\d+)', line)
        m4 = re.search(r'nDedupMappingPointers.*\s+(\d+)', line)
        m5 = re.search(r'total spaceSaving=(\d+),DataBlocksNeededIfNoCompression=(\d+),overheadAllocated=(\d+),.+units=Blocks', line)
        m6 = re.search(r'total spaceSaving=(\d+),DataBlocksNeededIfNoCompression=(\d+),overheadAllocated=(\d+),.+units=Slices', line)
        if m1:
            d_cbfs_sapcesaving['nAUsNeededIfNoCompression'] = m1.group(1)
        elif m2:
            d_cbfs_sapcesaving['nPatternZeroMatched'] = m2.group(1)
        elif m3:
            d_cbfs_sapcesaving['nPatternNonZeroMatched'] = m3.group(1)
        elif m4:
            d_cbfs_sapcesaving['nDedupMappingPointers'] = m4.group(1)
        elif m5:
            d_cbfs_sapcesaving['spaceSaving'] = m5.group(1)
            d_cbfs_sapcesaving['DataBlocksNeededIfNoCompression'] = m5.group(2)
            d_cbfs_sapcesaving['overheadAllocated'] = m5.group(3)
        elif m6:
            d_cbfs_sapcesaving['spaceSaving_in_slice'] = m6.group(1)
            d_cbfs_sapcesaving['DataBlocksNeededIfNoCompression_in_slice'] = m6.group(2)
            d_cbfs_sapcesaving['overheadAllocated_in_slice'] = m6.group(3)

    LOG.print_log('INFO', "Get d_cbfs_sapcesaving:")
    for k in d_cbfs_sapcesaving.keys():
        LOG.print_plain_log('INFO', '{} : {}'.format(k, d_cbfs_sapcesaving[k]))

    return d_cbfs_sapcesaving


##############################################################################
# Storage Resource Space Acocunting Function
##############################################################################

def check_vvol_space(vvol_obj_list, d_compare, do_assert=True):
    """
    :param vvol_obj_list:
    :param d_compare:
    :return:
    """
    object_type = VVol.__name__
    actual_used_list = []
    actual_size_list = []

    LOG.print_log('INFO', "Func {}, start the verification.".format(sys._getframe().f_code.co_name))
    assert type(vvol_obj_list) is list and len(vvol_obj_list) > 0 and type(d_compare) is dict, \
        "[Assert Error] Invalid vvol_obj_list:{} or d_compare:{}!".format(vvol_obj_list, d_compare)

    for i in range(len(vvol_obj_list)):
        obj = vvol_obj_list[i]
        assert isinstance(obj, VVol), "[Assert Error] Input object - {} is invalid!".format(obj)
        obj.get_vvol_profile()
        obj.get_vvol_mlucli_profile()

        for k in VERIFY_LIST_1:
            # for each kind of values to check
            if d_compare.get(k) is not None:
                assert type(d_compare[k]) is compare_profile and \
                       len(d_compare[k].values_to_compare) == len(d_compare[k].symbols) and \
                       len(d_compare[k].values_to_compare) == len(vvol_obj_list) and \
                       type(d_compare[k].deviation) is float and 0 <= d_compare[k].deviation <= 1, \
                    "[Assert Error] Input d_compare is invalid or the number of values are not consistent!\n{}".format(d_compare)

                unit = 'GB'
                if k == 'used':
                    used_b, _ = get_size_in_kb_human(obj.profile['Current allocation'])
                    used_gb = B_to_GB(used_b)
                    actual_used_list.append(used_gb)
                    actual = used_gb
                elif k == 'size':
                    size_b, _ = get_size_in_kb_human(obj.profile['Size'])
                    size_gb = B_to_GB(size_b)
                    actual_size_list.append(size_gb)
                    actual = size_gb

                if do_assert:
                    compare = d_compare[k].values_to_compare[i]
                    symbol = d_compare[k].symbols[i]
                    assert type(compare) is int or type(compare) is float, "[Assert Error] Input compare - {} is invalid!".format(compare)
                    assert type(symbol) is str and symbol in SYMBOL, "[Assert Error] Input symbol - {} is invalid!".format(symbol)

                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}, compare is {} {}.".format(object_type, obj.identifier, k, actual, unit, compare, unit))
                    if symbol == '=':
                        assert_equal(actual, compare, deviation=d_compare[k].deviation)
                    elif symbol == '>':
                        assert_greater(actual, compare)
                    elif symbol == '<':
                        assert_smaller(actual, compare)
                    elif symbol == '>=':
                        assert_greater_or_equal(actual, compare)
                    elif symbol == '<=':
                        assert_smaller_or_equal(actual, compare)
                else:
                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}.".format(object_type, obj.identifier, k, actual, unit))

    return actual_used_list, actual_size_list


def check_cbfs_space(cbfs_obj_list, d_compare, do_assert=True):
    """
    :param cbfs_obj_list:
    :param d_compare:
    :return:
    """
    object_type = CBFS.__name__
    actual_used_list = []
    actual_saving_list = []
    actual_nAUsNeededIfNoCompression_list = []
    actual_nPatternZeroMatched_list = []
    actual_nPatternNonZeroMatched_list = []
    actual_nDedupMappingPointers_list = []

    LOG.print_log('INFO', "Func {}, start the verification.".format(sys._getframe().f_code.co_name))
    assert type(cbfs_obj_list) is list and len(cbfs_obj_list) > 0 and type(d_compare) is dict, \
        "[Assert Error] Invalid cbfs_obj_list:{} or d_compare:{}!".format(cbfs_obj_list, d_compare)

    for i in range(len(cbfs_obj_list)):
        obj = cbfs_obj_list[i]
        assert isinstance(obj, CBFS), "[Assert Error] Input object - {} is invalid!".format(obj)
        cbfs_info = obj.get_fsInfo()
        d_cbfs_sapcesaving = get_space_saving_from_cbfs_fsInfo(cbfs_info)

        for k in VERIFY_LIST_CBFS:
            # for each kind of values to check
            if d_compare.get(k) is not None:
                assert type(d_compare[k]) is compare_profile and \
                       len(d_compare[k].values_to_compare) == len(d_compare[k].symbols) and \
                       len(d_compare[k].values_to_compare) == len(cbfs_obj_list) and \
                       type(d_compare[k].deviation) is float and 0 <= d_compare[k].deviation <= 1, \
                    "[Assert Error] Input d_compare is invalid!\n{}".format(d_compare)

                unit = 'GB'
                if k == 'used':
                    used_gb = block_to_GB(d_cbfs_sapcesaving['overheadAllocated'])
                    actual_used_list.append(used_gb)
                    actual = used_gb
                elif k == 'saving':
                    saving_gb = slice_to_GB(d_cbfs_sapcesaving['spaceSaving_in_slice'])
                    actual_saving_list.append(saving_gb)
                    actual = saving_gb
                elif k == 'nAUsNeededIfNoCompression':
                    needcompression_gb = block_to_GB(d_cbfs_sapcesaving['nAUsNeededIfNoCompression'])
                    actual_nAUsNeededIfNoCompression_list.append(needcompression_gb)
                    actual = needcompression_gb
                elif k == 'nPatternZeroMatched':
                    zeropattern_gb = block_to_GB(d_cbfs_sapcesaving['nPatternZeroMatched'])
                    actual_nPatternZeroMatched_list.append(zeropattern_gb)
                    actual = zeropattern_gb
                elif k == 'nPatternNonZeroMatched':
                    nonzeropattern_gb = block_to_GB(d_cbfs_sapcesaving['nPatternNonZeroMatched'])
                    actual_nPatternNonZeroMatched_list.append(nonzeropattern_gb)
                    actual = nonzeropattern_gb
                elif k == 'nDedupMappingPointers':
                    dedup_gb = block_to_GB(d_cbfs_sapcesaving['nDedupMappingPointers'])
                    actual_nDedupMappingPointers_list.append(dedup_gb)
                    actual = dedup_gb

                if do_assert:
                    compare = d_compare[k].values_to_compare[i]
                    symbol = d_compare[k].symbols[i]
                    assert type(compare) is int or type(compare) is float, "[Assert Error] Input compare - {} is invalid!".format(compare)
                    assert type(symbol) is str and symbol in SYMBOL, "[Assert Error] Input symbol - {} is invalid!".format(symbol)

                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}, compare is {} {}.".format(object_type, obj.identifier, k, actual, unit, compare, unit))
                    if symbol == '=':
                        assert_equal(actual, compare, deviation=d_compare[k].deviation)
                    elif symbol == '>':
                        assert_greater(actual, compare)
                    elif symbol == '<':
                        assert_smaller(actual, compare)
                    elif symbol == '>=':
                        assert_greater_or_equal(actual, compare)
                    elif symbol == '<=':
                        assert_smaller_or_equal(actual, compare)
                else:
                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}.".format(object_type, obj.identifier, k, actual, unit))

    return actual_used_list, actual_saving_list, \
           actual_nAUsNeededIfNoCompression_list, actual_nPatternZeroMatched_list, actual_nPatternNonZeroMatched_list, actual_nDedupMappingPointers_list


def check_poolalloc_space(poolalloc_obj_list, d_compare, do_assert=True):
    """
    :param poolalloc_obj_list:
    :param d_compare:
    :return:
    """
    object_type = PoolAllocation.__name__
    actual_used_list = []
    actual_saving_list = []

    LOG.print_log('INFO', "Func {}, start the verification.".format(sys._getframe().f_code.co_name))
    assert type(poolalloc_obj_list) is list and len(poolalloc_obj_list) > 0 and type(d_compare) is dict, \
        "[Assert Error] Invalid poolalloc_obj_list:{} or d_compare:{}!".format(poolalloc_obj_list, d_compare)

    for i in range(len(poolalloc_obj_list)):
        obj = poolalloc_obj_list[i]
        assert isinstance(obj, PoolAllocation), "[Assert Error] Input object - {} is invalid!".format(obj)
        obj.get_poolallocation_mlucli_profile()

        for k in VERIFY_LIST_1:
            # for each kind of values to check
            if d_compare.get(k) is not None:
                assert type(d_compare[k]) is compare_profile and \
                       len(d_compare[k].values_to_compare) == len(d_compare[k].symbols) and \
                       len(d_compare[k].values_to_compare) == len(poolalloc_obj_list) and \
                       type(d_compare[k].deviation) is float and 0 <= d_compare[k].deviation <= 1, \
                    "[Assert Error] Input d_compare is invalid!\n{}".format(d_compare)

                unit = 'GB'
                if k == 'used':
                    used_gb = sector_to_GB(obj.mlucli_profile['UsedDataSpaceInSectors'])
                    actual_used_list.append(used_gb)
                    actual = used_gb
                elif k == 'saving':
                    saving_gb = sector_to_GB(obj.mlucli_profile['CompressionSavingsInSectors'])
                    actual_saving_list.append(saving_gb)
                    actual = saving_gb

                if do_assert:
                    compare = d_compare[k].values_to_compare[i]
                    symbol = d_compare[k].symbols[i]
                    assert type(compare) is int or type(compare) is float, "[Assert Error] Input compare - {} is invalid!".format(compare)
                    assert type(symbol) is str and symbol in SYMBOL, "[Assert Error] Input symbol - {} is invalid!".format(symbol)

                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}, compare is {} {}.".format(object_type, obj.identifier, k, actual, unit, compare, unit))
                    if symbol == '=':
                        assert_equal(actual, compare, deviation=d_compare[k].deviation)
                    elif symbol == '>':
                        assert_greater(actual, compare)
                    elif symbol == '<':
                        assert_smaller(actual, compare)
                    elif symbol == '>=':
                        assert_greater_or_equal(actual, compare)
                    elif symbol == '<=':
                        assert_smaller_or_equal(actual, compare)
                else:
                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}.".format(object_type, obj.identifier, k, actual, unit))

    return actual_used_list, actual_saving_list


def check_datastore_space(ds_obj_list, d_compare, do_assert=True):
    """
    :param ds_obj_list:
    :param d_compare:
    :return:
    """
    object_type = Datastore.__name__
    actual_used_list = []
    actual_saving_list = []
    actual_saving_percent_list = []
    actual_saving_ratio_list = []

    LOG.print_log('INFO', "Func {}, start the verification.".format(sys._getframe().f_code.co_name))
    assert type(ds_obj_list) is list and len(ds_obj_list) > 0 and type(d_compare) is dict, \
        "[Assert Error] Invalid ds_obj_list:{} or d_compare:{}!".format(ds_obj_list, d_compare)

    for i in range(len(ds_obj_list)):
        obj = ds_obj_list[i]
        assert isinstance(obj, Datastore), "[Assert Error] Input object - {} is invalid!".format(obj)
        obj.get_ds_profile()

        for k in VERIFY_LIST_2:
            # for each kind of values to check
            if d_compare.get(k) is not None:
                assert type(d_compare[k]) is compare_profile and \
                       len(d_compare[k].values_to_compare) == len(d_compare[k].symbols) and \
                       len(d_compare[k].values_to_compare) == len(ds_obj_list) and \
                       type(d_compare[k].deviation) is float and 0 <= d_compare[k].deviation <= 1, \
                    "[Assert Error] Input d_compare is invalid!\n{}".format(d_compare)

                unit = 'GB'
                if k == 'used':
                    used_b, _ = get_size_in_kb_human(obj.profile['Total used capacity'])
                    used_gb = B_to_GB(used_b)
                    actual_used_list.append(used_gb)
                    actual = used_gb
                elif k == 'saving':
                    # TODO: after this is enabled in uemcli
                    saving_b, _ = get_size_in_kb_human(obj.profile['XXXXXX'])
                    saving_gb = B_to_GB(saving_b)
                    actual_saving_list.append(saving_gb)
                    actual = saving_gb
                elif k == 'saving_percent':
                    # TODO: after this is enabled in uemcli
                    pass
                    unit = '%'
                elif k == 'saving_ratio':
                    # TODO: after this is enabled in uemcli
                    pass
                    unit = ':1'

                if do_assert:
                    compare = d_compare[k].values_to_compare[i]
                    symbol = d_compare[k].symbols[i]
                    assert type(compare) is int or type(compare) is float, "[Assert Error] Input compare - {} is invalid!".format(compare)
                    assert type(symbol) is str and symbol in SYMBOL, "[Assert Error] Input symbol - {} is invalid!".format(symbol)

                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}, compare is {} {}.".format(object_type, obj.identifier, k, actual, unit, compare, unit))
                    if symbol == '=':
                        assert_equal(actual, compare, deviation=d_compare[k].deviation)
                    elif symbol == '>':
                        assert_greater(actual, compare)
                    elif symbol == '<':
                        assert_smaller(actual, compare)
                    elif symbol == '>=':
                        assert_greater_or_equal(actual, compare)
                    elif symbol == '<=':
                        assert_smaller_or_equal(actual, compare)
                else:
                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}.".format(object_type, obj.identifier, k, actual, unit))

    return actual_used_list, actual_saving_list, actual_saving_percent_list, actual_saving_ratio_list


def check_pool_space(pool_obj_list, d_compare, do_assert=True):
    """
    :param pool_obj_list:
    :param d_compare:
    :return:
    """
    object_type = Pool.__name__
    actual_used_list = []
    actual_saving_list = []
    actual_saving_percent_list = []
    actual_saving_ratio_list = []

    LOG.print_log('INFO', "Func {}, start the verification.".format(sys._getframe().f_code.co_name))
    assert type(pool_obj_list) is list and len(pool_obj_list) > 0 and type(d_compare) is dict, \
        "[Assert Error] Invalid pool_obj_list:{} or d_compare:{}!".format(pool_obj_list, d_compare)

    for i in range(len(pool_obj_list)):
        obj = pool_obj_list[i]
        assert isinstance(obj, Pool), "[Assert Error] Input object - {} is invalid!".format(obj)
        obj.get_pool_profile()

        for k in VERIFY_LIST_2:
            # for each kind of values to check
            if d_compare.get(k) is not None:
                assert type(d_compare[k]) is compare_profile and \
                       len(d_compare[k].values_to_compare) == len(d_compare[k].symbols) and \
                       len(d_compare[k].values_to_compare) == len(pool_obj_list) and \
                       type(d_compare[k].deviation) is float and 0 <= d_compare[k].deviation <= 1, \
                    "[Assert Error] Input d_compare is invalid!\n{}".format(d_compare)

                unit = 'GB'
                if k == 'used':
                    used_b, _ = get_size_in_kb_human(obj.profile['Current allocation'])
                    used_gb = B_to_GB(used_b)
                    actual_used_list.append(used_gb)
                    actual = used_gb
                elif k == 'saving':
                    saving_b, _ = get_size_in_kb_human(obj.profile['Data Reduction space saved'])
                    saving_gb = B_to_GB(saving_b)
                    actual_saving_list.append(saving_gb)
                    actual = saving_gb
                elif k == 'saving_percent':
                    saving_percent = get_percentage(obj.profile['Data Reduction Percent'])
                    actual_saving_percent_list.append(saving_percent)
                    actual = saving_percent
                    unit = '%'
                elif k == 'saving_ratio':
                    saving_ratio = get_ratio(obj.profile['Data Reduction Ratio'])
                    actual_saving_ratio_list.append(saving_ratio)
                    actual = saving_ratio
                    unit = ':1'

                if do_assert:
                    compare = d_compare[k].values_to_compare[i]
                    symbol = d_compare[k].symbols[i]
                    assert type(compare) is int or type(compare) is float, "[Assert Error] Input compare - {} is invalid!".format(compare)
                    assert type(symbol) is str and symbol in SYMBOL, "[Assert Error] Input symbol - {} is invalid!".format(symbol)

                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}, compare is {} {}.".format(object_type, obj.identifier, k, actual, unit, compare, unit))
                    if symbol == '=':
                        assert_equal(actual, compare, deviation=d_compare[k].deviation)
                    elif symbol == '>':
                        assert_greater(actual, compare)
                    elif symbol == '<':
                        assert_smaller(actual, compare)
                    elif symbol == '>=':
                        assert_greater_or_equal(actual, compare)
                    elif symbol == '<=':
                        assert_smaller_or_equal(actual, compare)
                else:
                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}.".format(object_type, obj.identifier, k, actual, unit))

    return actual_used_list, actual_saving_list, actual_saving_percent_list, actual_saving_ratio_list


def check_system_space(system_obj_list, d_compare, do_assert=True):
    """
    :param system_obj_list:
    :param d_compare:
    :return:
    """
    object_type = System.__name__
    actual_used_list = []
    actual_saving_list = []
    actual_saving_percent_list = []
    actual_saving_ratio_list = []

    LOG.print_log('INFO', "Func {}, start the verification.".format(sys._getframe().f_code.co_name))
    assert type(system_obj_list) is list and len(system_obj_list) > 0 and type(d_compare) is dict, \
        "[Assert Error] Invalid system_obj_list:{} or d_compare:{}!".format(system_obj_list, d_compare)

    for i in range(len(system_obj_list)):
        obj = system_obj_list[i]
        assert isinstance(obj, System), "[Assert Error] Input object - {} is invalid!".format(obj)
        obj.get_system_profile()

        for k in VERIFY_LIST_2:
            # for each kind of values to check
            if d_compare.get(k) is not None:
                assert type(d_compare[k]) is compare_profile and \
                       len(d_compare[k].values_to_compare) == len(d_compare[k].symbols) and \
                       len(d_compare[k].values_to_compare) == len(system_obj_list) and \
                       type(d_compare[k].deviation) is float and 0 <= d_compare[k].deviation <= 1, \
                    "[Assert Error] Input d_compare is invalid!\n{}".format(d_compare)

                unit = 'GB'
                if k == 'used':
                    used_b, _ = get_size_in_kb_human(obj.profile['Used space'])
                    used_gb = B_to_GB(used_b)
                    actual_used_list.append(used_gb)
                    actual = used_gb
                elif k == 'saving':
                    saving_b, _ = get_size_in_kb_human(obj.profile['Data Reduction space saved'])
                    saving_gb = B_to_GB(saving_b)
                    actual_saving_list.append(saving_gb)
                    actual = saving_gb
                elif k == 'saving_percent':
                    saving_percent = get_percentage(obj.profile['Data Reduction percent'])
                    actual_saving_percent_list.append(saving_percent)
                    actual = saving_percent
                    unit = '%'
                elif k == 'saving_ratio':
                    saving_ratio = get_ratio(obj.profile['Data Reduction ratio'])
                    actual_saving_ratio_list.append(saving_ratio)
                    actual = saving_ratio
                    unit = ':1'

                if do_assert:
                    compare = d_compare[k].values_to_compare[i]
                    symbol = d_compare[k].symbols[i]
                    assert type(compare) is int or type(compare) is float, "[Assert Error] Input compare - {} is invalid!".format(compare)
                    assert type(symbol) is str and symbol in SYMBOL, "[Assert Error] Input symbol - {} is invalid!".format(symbol)

                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}, compare is {} {}.".format(object_type, obj.identifier, k, actual, unit, compare, unit))
                    if symbol == '=':
                        assert_equal(actual, compare, deviation=d_compare[k].deviation)
                    elif symbol == '>':
                        assert_greater(actual, compare)
                    elif symbol == '<':
                        assert_smaller(actual, compare)
                    elif symbol == '>=':
                        assert_greater_or_equal(actual, compare)
                    elif symbol == '<=':
                        assert_smaller_or_equal(actual, compare)
                else:
                    LOG.print_log('INFO', "{} {} - {}: actual is {} {}.".format(object_type, obj.identifier, k, actual, unit))

    return actual_used_list, actual_saving_list, actual_saving_percent_list, actual_saving_ratio_list


def collect_vvol_cbfs_poolallocation_from_datastore(storage_obj, datastore_objs, disk_size_list, select_size_list, vm_uuid=None):
    """
    :param storage_obj:
    :param datastore_objs: list of Datastore instance
    :param disk_size_list: list of list
    :param select_size_list: list of list
    :param vm_uuid: str
    :return: d_cbfs_vvol, d_datastore_vvol, test_primary_vvol, test_cbfs, test_poolalloc
    """
    assert isinstance(storage_obj, Storage), "[Assert Error] Invalid storage_obj!"
    assert type(datastore_objs) is list and type(disk_size_list) is list and type(select_size_list) is list and \
           len(datastore_objs) == len(disk_size_list) and len(disk_size_list) == len(select_size_list), \
        "[Assert Error] Invalid datastore_objs or disk_size_list or select_size_list!"
    if vm_uuid is not None:
        assert type(vm_uuid) is str and len(vm_uuid) > 0 and not vm_uuid.isspace(), "[Assert Error] Input vm_uuid is invalid!"

    d_cbfs_vvol = {}
    d_datastore_vvol = {}
    test_primary_vvol = []
    test_cbfs = []

    # VVol and CBFS
    for index in range(len(datastore_objs)):
        datastore_obj = datastore_objs[index]
        assert isinstance(datastore_obj, Datastore), "[Assert Error] Invalid datastore_obj!"
        disk_size = disk_size_list[index]
        select_size = select_size_list[index]

        datastore_name = datastore_obj.profile['Name']
        datastore_id = datastore_obj.profile['ID']
        if d_datastore_vvol.get(datastore_name) is None:
            d_datastore_vvol[datastore_name] = []

        LOG.print_log('INFO', 'Find VVol in datastore {}...'.format(datastore_name))
        created_cbfs = []
        for i in range(len(disk_size)):
            vvol_size = GB_to_B(disk_size[i])
            LOG.print_log('INFO', 'Find VVol which datastore_id is {}, vvol_size is {} B.'.format(datastore_id, vvol_size))
            fetch = (i == 0)
            vvol = VVol.find_vvol(storage_obj, datastore_id, vvol_size, vvol_type='Data', replica_type='Base', vm_uuid=vm_uuid, fetch=fetch)
            # vvol.get_vvol_profile()
            # vvol.get_vvol_mlucli_profile()
            fsid = vvol.mlucli_profile['FSID']
            LOG.print_log('INFO', 'In Datastore {}, get VVol {} in CBFS {}.'.format(datastore_name, vvol.uuid, fsid))

            # collect vvol
            if d_cbfs_vvol.get(fsid) is None:
                d_cbfs_vvol[fsid] = []
            d_cbfs_vvol[fsid].append(vvol)
            d_datastore_vvol[datastore_name].append(vvol)

            # select vvol for test
            if disk_size[i] in select_size:
                test_primary_vvol.append(vvol)
                if fsid not in created_cbfs:
                    cbfs = CBFS(storage_obj, fsid, sp_owner=vvol.profile['SP owner'])
                    test_cbfs.append(cbfs)
                    created_cbfs.append(fsid)

        for k in d_cbfs_vvol.keys():
            l = [(vvol.uuid, vvol.profile['Size']) for vvol in d_cbfs_vvol[k]]
            LOG.print_log('INFO', 'CBFS {} got {} VVol - {}.'.format(k, len(l), l))

    # Pool Allocation
    test_poolalloc = []
    created_poolalloc = []
    for vvol_obj in test_primary_vvol:
        poolalloc_oid = vvol_obj.mlucli_profile['Allocation']
        if poolalloc_oid not in created_poolalloc:
            poolalloc = PoolAllocation(storage_obj, poolalloc_oid)
            test_poolalloc.append(poolalloc)
            created_poolalloc.append(poolalloc_oid)

    return d_cbfs_vvol, d_datastore_vvol, test_primary_vvol, test_cbfs, test_poolalloc


if __name__ == '__main__':
    pass

    # # Define storage object
    # vvol_uuid = 'naa.600601604eb14d00e55feb8f19b941e6'
    # vvol = VVol(storage, vvol_uuid)
    # vvol.get_vvol_profile()
    # vvol.get_vvol_mlucli_profile()
    #
    # vvol_uuid = 'naa.600601604eb14d00bc699220d5db4191'
    # vvol_2 = VVol(storage, vvol_uuid)
    # vvol_2.get_vvol_profile()
    # vvol_2.get_vvol_mlucli_profile()
    #
    # fsid = vvol.mlucli_profile['FSID']
    # cbfs = CBFS(storage, fsid, sp_owner='spb')
    #
    # fsid_2 = vvol_2.mlucli_profile['FSID']
    # cbfs_2 = CBFS(storage, fsid_2, sp_owner='spb')
    #
    # poolalloc_oid = vvol.mlucli_profile['Allocation']
    # poolalloc = PoolAllocation(storage, poolalloc_oid)
    #
    # ds_name = d_testparam['VVOL_DATASTORE_3']['name'] + storage.name
    # datastore_file = Datastore(storage, ds_name)
    #
    # pool_name = 'vvol_pool'
    # pool = Pool(storage, pool_name)
    #
    # system = System(storage)

    ### ------------------------------------------ Example ------------------------------------------
    # d_compare_profile = dict(D1)
    # d_compare_profile['used'] = compare_profile(values_to_compare=[10, 10], symbols=['=', '='], deviation=0.1)
    # used, saving = check_vvol_space([vvol, vvol_2], d_compare_profile)
    #
    # d_compare_profile = dict(D1)
    # d_compare_profile['used'] = compare_profile(values_to_compare=[5, 7.5], symbols=['=', '='], deviation=0.1)
    # d_compare_profile['saving'] = compare_profile(values_to_compare=[5, 2.5], symbols=['=', '='], deviation=0.1)
    # used, saving = check_cbfs_space([cbfs, cbfs_2], d_compare_profile)
    # cbfs_saving = sum(saving)
    #
    # d_compare_profile = dict(D1)
    # d_compare_profile['used'] = compare_profile(values_to_compare=[10], symbols=['='], deviation=0.1)
    # d_compare_profile['saving'] = compare_profile(values_to_compare=[5], symbols=['='], deviation=0.1)
    # used, saving = check_poolalloc_space([poolalloc], d_compare_profile)
    #
    # d_compare_profile = dict(D2)
    # d_compare_profile['used'] = compare_profile(values_to_compare=[10], symbols=['>'], deviation=0.1)
    # used, saving, saving_percent, saving_ratio = check_datastore_space([datastore_file], d_compare_profile)
    #
    # d_compare_profile = dict(D2)
    # d_compare_profile['used'] = compare_profile(values_to_compare=[20], symbols=['>'], deviation=0.1)
    # d_compare_profile['saving'] = compare_profile(values_to_compare=[cbfs_saving], symbols=['='], deviation=0.1)
    # d_compare_profile['saving_percent'] = compare_profile(values_to_compare=[0], symbols=['>'], deviation=0.1)
    # d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=[0], symbols=['>'], deviation=0.1)
    # used, saving, saving_percent, saving_ratio = check_pool_space([pool], d_compare_profile)
    #
    # d_compare_profile = dict(D2)
    # d_compare_profile['used'] = compare_profile(values_to_compare=used, symbols=['='], deviation=0.1)
    # d_compare_profile['saving'] = compare_profile(values_to_compare=saving, symbols=['='], deviation=0.1)
    # d_compare_profile['saving_percent'] = compare_profile(values_to_compare=saving_percent, symbols=['='], deviation=0.1)
    # d_compare_profile['saving_ratio'] = compare_profile(values_to_compare=saving_ratio, symbols=['='], deviation=0.1)
    # used, saving, saving_percent, saving_ratio = check_system_space([system], d_compare_profile)

    # # --- VVOL
    # vvol.get_vvol_profile()
    # vvol.get_vvol_mlucli_profile()
    # vvol_used_kb, _ = get_size_in_kb_human(vvol.profile['Current allocation'])
    # vvol_used_gb = B_to_GB(vvol_used_kb)
    # print(vvol_used_gb, _)
    # assert_equal(vvol_used_gb, 10, deviation=0.1)
    #
    # # --- CBFS
    # cbfs_info = cbfs.get_fsInfo()
    # d_cbfs_sapcesaving = get_space_saving_from_cbfs_fsInfo(cbfs_info)
    # saving_gb = slice_to_GB(d_cbfs_sapcesaving['spaceSaving_in_slice'])
    # print(saving_gb)
    # assert_equal(saving_gb, 5, deviation=0.1)
    #
    # # --- POOL ALLOCATION
    # poolalloc.get_poolallocation_mlucli_profile()
    # poolalloc_saving_gb = sector_to_GB(poolalloc.mlucli_profile['CompressionSavingsInSectors'])
    # print(poolalloc_saving_gb)
    # assert_equal(poolalloc_saving_gb, 5, deviation=0.1)
    #
    # # --- DATASTORE
    # datastore_file.get_ds_profile()
    # ds_used_kb, _ = get_size_in_kb_human(datastore_file.profile['Total used capacity'])
    # ds_used_gb = B_to_GB(ds_used_kb)
    # print(ds_used_gb, _)
    # assert_greater(ds_used_gb, 10)
    #
    # # --- POOL
    # pool.get_pool_profile()
    # pool_saving_kb, _ = get_size_in_kb_human(pool.profile['Data Reduction space saved'])
    # pool_saving_gb = B_to_GB(pool_saving_kb)
    # pool_saving_percent = get_percentage(pool.profile['Data Reduction Percent'])
    # pool_saving_ratio = get_ratio(pool.profile['Data Reduction Ratio'])
    # print(pool_saving_gb, pool_saving_percent, pool_saving_ratio)
    # assert_equal(pool_saving_gb, 7.25, deviation=0.1)
    # assert_greater(pool_saving_percent, 0)
    # assert_greater(pool_saving_ratio, 1)
    #
    # # --- SYSTEM
    # system.get_system_profile()
    # system_saving_kb, _ = get_size_in_kb_human(system.profile['Data Reduction space saved'])
    # system_saving_gb = B_to_GB(system_saving_kb)
    # system_saving_percent = get_percentage(system.profile['Data Reduction percent'])
    # system_saving_ratio = get_ratio(system.profile['Data Reduction ratio'])
    # print(system_saving_gb, system_saving_percent, system_saving_ratio)
    # assert_equal(system_saving_gb, 7.25, deviation=0.1)
    # assert_greater(system_saving_percent, 0)
    # assert_greater(system_saving_ratio, 1)

