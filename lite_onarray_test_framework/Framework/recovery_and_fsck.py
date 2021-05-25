from Framework.component import *

LOG = ExecuteLog('recovery_and_fsck', LOG_LEVEL, testlog)


def vvol_do_recovery(storage_obj, vvol_object_list, mode='sequential', check_modify=False):
    support_mode = ['sequential', 'batch']
    assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
    assert isinstance(vvol_object_list, list) and len(vvol_object_list) > 0, "[Assert Error] Input vvol_object_list is invalid!"
    assert isinstance(mode, str) and mode in support_mode, "[Assert Error] Input mode:{} is invalid!".format(mode)

    recovery_output = ''

    if mode == 'sequential':
        for vvol in vvol_object_list:
            assert isinstance(vvol, VVol), "[Assert Error] Input storage_obj is invalid!"
            vvol_uuid = vvol.uuid

            step_str = 'Set recovery flag for VVol {}.'.format(vvol_uuid)
            command = 'mlu_recover.pl setvvolrecoveryrequired -uuid {}'.format(vvol_uuid)
            output, return_code = run_command_on_storage_check_returncode(storage_obj, command, step_str=step_str)

            step_str = 'List all the objects that need recovery.'
            command = 'mlu_recover.pl listallobjectsthatrequirerecovery'
            output, return_code = run_command_on_storage_check_returncode(storage_obj, command, step_str=step_str)

            vvol.check_vvol_offline()

            step_str = 'Start recovery for VVol {}.'.format(vvol_uuid)
            command = 'mlu_recover.pl startvvolrecovery -uuid {}'.format(vvol_uuid)
            output, return_code = run_command_on_storage_check_returncode(storage_obj, command, step_str=step_str)
            recovery_output += output

            step_str = 'Bring VVol {} online.'.format(vvol_uuid)
            command = 'mlu_recover.pl bringvvolonline -uuid {}'.format(vvol_uuid)
            output, return_code = run_command_on_storage_check_returncode(storage_obj, command, step_str=step_str)

            vvol.check_vvol_online()

    elif mode == 'batch':
        vvol_uuid_list = []
        for vvol in vvol_object_list:
            vvol_uuid_list.append(vvol.uuid)

        vvol_uuid_batch = ' '.join(vvol_uuid_list)

        step_str = 'Set recovery flag for VVol {}.'.format(vvol_uuid_batch)
        command = 'mlu_recover.pl setvvolrecoveryrequired -uuid {}'.format(vvol_uuid_batch)
        output, return_code = run_command_on_storage_check_returncode(storage_obj, command, step_str=step_str)

        step_str = 'List all the objects that need recovery.'
        command = 'mlu_recover.pl listallobjectsthatrequirerecovery'
        output, return_code = run_command_on_storage_check_returncode(storage_obj, command, step_str=step_str)

        for vvol in vvol_object_list:
            vvol.check_vvol_offline()

        step_str = 'Start recovery for VVol {}.'.format(vvol_uuid_batch)
        command = 'mlu_recover.pl startvvolrecovery -uuid {}'.format(vvol_uuid_batch)
        output, return_code = run_command_on_storage_check_returncode(storage_obj, command, step_str=step_str)
        recovery_output += output

        step_str = 'Bring VVol {} online.'.format(vvol_uuid_batch)
        command = 'mlu_recover.pl bringvvolonline -uuid {}'.format(vvol_uuid_batch)
        output, return_code = run_command_on_storage_check_returncode(storage_obj, command, step_str=step_str)

        for vvol in vvol_object_list:
            vvol.check_vvol_online()

    if type(check_modify) is str:
        assert check_modify.lower() == 'yes' or check_modify.lower() == 'no', \
            "[Assert Error] Input check_modify should be yes or no if you want to check modification!"

        if check_modify.lower() == 'yes':
            string = 'YES'
        elif check_modify.lower() == 'no':
            string = 'NO'
        msg = 'IsModified\s+:\s+' + string
        m = re.findall(msg, recovery_output, re.S)
        log_str = 'There are {} VVol and {} with IsModified = {}.'.format(len(vvol_object_list), len(m), string)
        assert len(vvol_object_list) == len(m), "[Assert Error] " + log_str
        LOG.print_log('INFO', log_str)

