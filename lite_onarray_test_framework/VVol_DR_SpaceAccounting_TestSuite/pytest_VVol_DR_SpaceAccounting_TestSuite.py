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

import pytest

# Import modules
from Example_TestSuite.setup_teardown_environment import *

# Import TestCases
from Example_TestSuite.TestCase.TC_Example_System_Pool_Lun import *


##############################################################################
# Fixtures
##############################################################################

@pytest.fixture(scope='class', autouse=True)
def setup_teardown_testsuite(if_setup_env, if_teardown_env):
    """
    Add "--setup-env True" to setup testsuite env before testcases execution.
    Add "--teardown-env True" to teardown testsuite env after testcases execution.
    For example:
    pytest pytest_pytest_Example_TestSuite.py::TestExampleTestSuiteBlock -v --setup-env True --teardown-env True
    """
    print("\n### Get into function setup_teardown_testsuite...")
    testbed_filename = 'testbed_OB-H1651.cfg'
    testparam_filename = 'testparam_Block.cfg'
    storage, io_host, uemcli_host, windows_host, d_testparam = \
        collect_testbed_testsuite_configurations(testbed_filename, testparam_filename)

    if if_setup_env.lower() == 'true':
        print('# Setup testsuite environment...')
        d_storage_object = {}
        # d_storage_object = \
        #     setup_test_environment_block(storage, io_host, uemcli_host, windows_host, d_testparam)
    else:
        print('###### False ######')
        d_storage_object = {}

    yield storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object

    if if_teardown_env.lower() == 'true':
        print("\n# Teardown testsuite environment...")
        # teardown_test_environment_block(storage, io_host, uemcli_host, windows_host, d_testparam)


##############################################################################
# Class for TestCases
##############################################################################

class TestExampleTestSuiteBlock():
    def test_something_block_1(self):
        assert 1 + 1 == 2

    def test_something_block_2(self):
        assert 1 + 1 > 2

    def test_something_block_3(self):
        import random
        assert random.random() > 0.5

    @pytest.mark.xfail
    def test_TC_Example_System_Pool_Lun(self, setup_teardown_testsuite):
        storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object = setup_teardown_testsuite
        TC_Example_System_Pool_Lun(storage, io_host, uemcli_host, windows_host, d_testparam, d_storage_object)


class TestExampleTestSuiteFile():
    def test_something_file_1(self):
        assert True

    def test_something_file_2(self):
        assert "Hello" == "Hell"
