from Framework.io_tool import *
from Framework.test_actions import *
from Framework.space_accounting_checker import *
from Framework.recovery_and_fsck import *

##############################################################################
# Module Variable
##############################################################################

testcase_name = 'TC_Example_System_Pool_Lun'
LOG = ExecuteLog(testcase_name, LOG_LEVEL, testlog)

##############################################################################
# Test Case Definition
##############################################################################

@tc_symbol_printer(testcase_name)
def TC_Example_System_Pool_Lun(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object={}):
    """
    STEP_1: Get the system, storage pool.
    STEP_2: Create multiple Luns for testing.
    """

    #####
    LOG.print_step('Get the system, storage pool, and datastore.')

    system = System(storage)

    if d_storage_object.get('POOL_1') is not None:
        pool = d_storage_object['POOL_1']
    else:
        pool_name = d_testparam['POOL_1']['name']
        pool = Pool(storage, pool_name)

    pool.get_pool_profile()

    #####
    LOG.print_step('Create multiple Luns for testing.')
    luns = []



if __name__ == '__main__':
    pass
