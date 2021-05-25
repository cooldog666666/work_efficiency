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

from VVol_DR_SpaceAccounting_TestSuite.setup_teardown_environment import *

from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_SingleFamily_Primary import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_SingleFamily_Primary_Snap import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_SingleFamily_Primary_Snap_2 import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_MultipleFamily import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_MultipleCBFS import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_FullClone import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_FastClone import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_VVol_Extension_During_IO import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_NewVVol_DuringIO_ConcurrentIO import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_VVol_Falimy_Maximum_Number import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_Block_Basic_Reboot_Panic import *
from VVol_DR_SpaceAccounting_TestCase.TC_VVOL_DR_Block_TwoFamily_TwoCBFS_Spacemaker_Snap import *

from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_File_SingleFamily_Primary_Snap import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_File_MultipleFamily import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_File_MultipleCBFS import *
from VVol_DR_SpaceAccounting_TestSuite.TestCase.TC_VVOL_DR_File_FullClone_FastClone import *

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
        d_storage_object = setup_test_environment_vvoldr(storage, io_host, uemcli_host, windows_host, d_testparam)

    # YOUR TESTCASES
    # TC_VVOL_DR_Block_SingleFamily_Primary(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_Block_SingleFamily_Primary_Snap(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_Block_SingleFamily_Primary_Snap_2(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_Block_MultipleFamily(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_Block_MultipleCBFS(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_Block_FullClone(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_Block_FastClone(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_Block_VVol_Extension_During_IO(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_Block_NewVVol_DuringIO_ConcurrentIO(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_Block_VVol_Falimy_Maximum_Number(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    TC_VVOL_DR_Block_Basic_Reboot_Panic(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)

    # TC_VVOL_DR_File_SingleFamily_Primary_Snap(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_File_MultipleFamily(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_File_MultipleCBFS(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)
    # TC_VVOL_DR_File_FullClone_FastClone(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)

    if teardown_env:
        teardown_test_environment_vvoldr(storage, io_host, uemcli_host, windows_host, d_testparam)


if __name__ == '__main__':

    testbed_filename = 'testbed.cfg'
    testparam_filename = 'testparam.cfg'
    run_testcase(testbed_filename, testparam_filename, setup_env=False, teardown_env=False)
