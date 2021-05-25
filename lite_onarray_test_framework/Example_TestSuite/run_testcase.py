##############################################################################
# Project Configuration
##############################################################################
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
print('\nAdd the project path {} into PYTHONPATH.'.format(rootPath))
sys.path.append(rootPath)
print('---------------------- PYTHONPATH --------------------------')
for i in sys.path:
    print(i)
print('------------------------------------------------------------')

##############################################################################
# Import TestCases
##############################################################################

from Example_TestSuite.setup_teardown_environment import *

from Example_TestSuite.TestCase.TC_Example_System_Pool_Lun import *

##############################################################################
# Module Variable
##############################################################################

LOG = ExecuteLog('run_testcase', LOG_LEVEL, testlog)

##############################################################################
# Run TestCases
##############################################################################

@ts_symbol_printer()
def run_testcase(testbed_filename, testparam_filename, setup_env=False, teardown_env=False):
    storage, io_host, uemcli_host, windows_host, d_testparam = \
        collect_testbed_testsuite_configurations(testbed_filename, testparam_filename)

    d_storage_object = {}
    if setup_env:
        d_storage_object = setup_test_environment_block(storage, io_host, uemcli_host, windows_host, d_testparam)

    # YOUR TESTCASES
    TC_Example_System_Pool_Lun(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)

    if teardown_env:
        teardown_test_environment_block(storage, io_host, uemcli_host, windows_host, d_testparam)


if __name__ == '__main__':

    testbed_filename = 'testbed_OB-H1651.cfg'
    testparam_filename = 'testparam_Block.cfg'
    run_testcase(testbed_filename, testparam_filename, setup_env=False, teardown_env=False)
