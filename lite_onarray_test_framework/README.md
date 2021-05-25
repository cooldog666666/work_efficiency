# lite_onarray_test_framework

## Start your testing
![](https://eos2git.cec.lab.emc.com/huangy19/lite_onarray_test_framework/blob/master/Example_TestSuite.png)

### Create and setup your testsuite
- Create a directory for your testsuite under root directory.
- Create 5 basic directories and 2 essential python files under your testsuite.
    + testbed  
    Put your testbed.cfg file here.  
    How to setup testbed.cfg file?  
        + Collect your testbed informations into a cfg file to discribe the devices needed.  
    For example in testbed_OB-H1651.cfg:
        ```
          [IO_HOST]
            host_ip = 10.245.95.207
            username = root
            password = Password123!
            operation_system = Linux
            vdbench_path = /opt/vdbench50407
            iox_path = /opt/IOX
            vjtree_path = /opt/vjtree

        [UEMCLI_HOST]
            host_ip = 10.244.103.86
            username = c4dev
            password = c4dev!
            operation_system = Linux

        [STORAGE]
            name = OB-H1651
            spa_ip = 10.245.82.185
            spb_ip = 10.245.82.186
            mgmt_ip = 10.245.82.189
            username = root
            port_1 = spa_eth3
            port_2 = spb_eth3
            ioip_1 = 10.245.125.145
            ioip_2 = 10.245.125.146
            gateway = 10.245.125.1
            netmask = 255.255.255.0
        ```

    + testparam  
    Put your testparam.cfg file here.  
    How to setup testparam.cfg file?  
        + Collect your testsuite level parameters into a cfg file to discribe the test environment in testsuite scope.  
    For example in testparam_Block.cfg:  
        ```
        [POOL_1]
        name = test_pool
        profile = tprofile_12,tprofile_12
        dg = dg_2,dg_27
        drive_number = 2,2
        type = traditional

        [HOST_1]
        name = test_host
        ip = 10.245.95.207
        username = root
        password = Password123!
        ```
    
    + testlog  
    After test execution, testlog files for each level will be generated here.  
    The test execution log file will be created with a unique name with the execution datatime as a postfix.  
    Log files for command execution classes will be long-term used as append mode.  
    ![](https://eos2git.cec.lab.emc.com/huangy19/lite_onarray_test_framework/blob/master/Example_TestSuite_testlog.png)
    
    + io_config_file  
    Put your io configuration files that needed in testing here.  
    
    + TestCase  
    Put your testcases here.  
    How to setup your testcase?  
        + One python file named start with "TC_" indicate a testcase.  
        + Import the modules your need in your test case.  
        + Design your test steps into the function with the same name as testcase file.  
    For example:  
        ```python
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
        ```
    + setup_teardown_environment.py  
    Your can use this python file to define multiple testsuite level functions to setup different test environments you needed in your testsuite. The teardown functions are also defined here.  
    For example:  
        ```python
        ##############################################################################
        # Setup Environment
        ##############################################################################

        def setup_test_environment_block(storage, io_host, uemcli_host, windows_host, d_testparam):
            """
            :param storage:
            :param io_host:
            :param uemcli_host:
            :param windows_host:
            :param d_testparam:
            :return: d_storage_object
            """

            LOG.print_log('INFO', "Setup test environment...")
            d_storage_object = {}.fromkeys(d_testparam.keys(), None)

            ######
            LOG.print_step('Arrange test parameters.')
        ```
        ```python
        ##############################################################################
        # Teardown Environment
        ##############################################################################

        def teardown_test_environment_block(storage, io_host, uemcli_host, windows_host, d_testparam):
            """
            :param storage:
            :param io_host:
            :param uemcli_host:
            :param windows_host:
            :param d_testparam:
            """

            ######
            LOG.print_step('Arrange test parameters.')
          ```
    + run_testcase.py  
    This python file helps arrange the testcase executions in your testsuite.  
    How to setup run_testcase.py?  
        + Import your setup_teardown_environment module to setup and teardown testsuite environment.  
        + Import your testcases for execution.  
        + Specify your testbed file and testparam file for testing.  
        + Your can alse decide whether to setup or tear down testsuite level test environment through incoming parameters.  
        ```python
        ##############################################################################
        # Import TestCases
        ##############################################################################

        from Example_TestSuite.setup_teardown_environment import *
        from Example_TestSuite.TestCase.TC_Example_System_Pool_Lun import *
        ```  

        ```python

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
        ```
### Start your tests execution
- On Linux host, run "python run_testcase.py".
- In Windows Python IDE, run run_testcase.py.

### Enjoy your testing with lite on-array!


