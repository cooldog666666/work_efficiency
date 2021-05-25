from Framework.setup_testsuite import *
from Framework.component import *

##############################################################################
# Module Variable
##############################################################################

LOG = ExecuteLog('test_actions', LOG_LEVEL, testlog)

##############################################################################
# Storage Actions
##############################################################################

def auto_install_image(storage, image, host_obj):
    assert isinstance(storage, Storage), "[Assert Error] Input storage - {} is invalid!".format(storage)
    assert type(image) is str and image.endswith('.tgz.bin'), "[Assert Error] Input image - {} is invalid!".format(image)

    storage_name = storage.name
    step_str = 'Start installation for storage {} with image {}...'.format(storage_name, image)
    command = 'auto_install_upgrade.sh -a {} -i {} -p'.format(storage_name, image)
    run_command_on_host_check_returncode(host_obj, command, step_str=step_str)


##############################################################################
# Storage Resource Actions
##############################################################################
check_output_for_uemcli_set = 'Operation completed successfully'

@ensure_action_succeed_decorator
def create_pool(storage, name, profile, dg, drive_number, pool_type=None):

    SUPPORT_POOL_TYPE = ['traditional', 'dynamic']

    LOG.print_log('DEBUG', "Show profile...")
    spa = SP(storage, 'spa')
    d_featurestate = dict(spa.get_feature_state())
    if d_featurestate['MAPPED_RAID'] == 'ENABLED':
        LOG.print_log('INFO', "MAPPED_RAID is enabled on spa.")
        command = '/stor/config/profile -all show -output csv -detail'
    else:
        command = '/stor/config/profile show -output csv -detail'
    output, return_code = storage.run_uemcli(command)
    LOG.print_log('DEBUG', "output is:\n")
    LOG.print_plain_log('DEBUG', output)
    assert return_code == 0, "[Assert Error] uemcli show profile failed!"

    LOG.print_log('DEBUG', "Show dg...")
    command = '/stor/config/dg show -output csv -detail'
    output, return_code = storage.run_uemcli(command)
    LOG.print_log('DEBUG', "output is:\n")
    LOG.print_plain_log('DEBUG', output)
    assert return_code == 0, "[Assert Error] uemcli show dg failed!"

    step_str = "Create a pool with name: {}, profile: {}, drive_number: {}, dg: {}".format(name, profile, drive_number, dg)
    check_output = check_output_for_uemcli_set

    command = '/stor/config/pool create -name {} -storProfile {} -drivesNumber {} -diskGroup {}'.format(name, profile, drive_number, dg)
    if pool_type is not None:
        assert type(pool_type) is str and pool_type in SUPPORT_POOL_TYPE, \
            "[Assert Error] Input pool_type {} is invalid!".format(pool_type)
        step_str += ", pool_type: {}".format(pool_type)
        command += ' -type {}'.format(pool_type)

    LOG.print_log('INFO', step_str)
    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def create_nasserver(storage, name, pool_name, sp='spa'):

    step_str = "Add a nas server with parameter name: {}, sp: {}, pool_name:{}".format(name, sp, pool_name)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = '/net/nas/server create -name {} -sp {} -poolName {}'.format(name, sp, pool_name)
    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def set_nas_nfs_v3v4(storage, nfs_id):

    step_str = "Add a nas nfs with parameter nfs_id : {}".format(nfs_id)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = '/net/nas/nfs -id {} set -v3 yes -v4 yes'.format(nfs_id)
    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def create_host(storage, name, ip, host_type='host'):

    step_str = "Add a host with parameter name: {}, ip: {}, host_type: {}".format(name, ip, host_type)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = '/remote/host create -name {} -type {} -addr {}'.format(name, host_type, ip)
    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def create_initiator(storage, host_id, iqn, initiator_type='iscsi'):

    step_str = "Create host initiator with parameter host_id: {}, iqn: {}, initiator_type: {}".format(host_id, iqn, initiator_type)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = '/remote/initiator create -host {} -uid {} -type {}'.format(host_id, iqn, initiator_type)
    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def create_iscsi_interface(storage, port_id, io_ip, netmask, gateway, vlan=None):

    step_str = "Create an iscsi interface with port_id: {}, io_ip: {}, netmask: {}, gateway: {}".format(port_id, io_ip, netmask, gateway)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = '/net/if create -type iscsi -port {} -ipv4 static -addr {} -netmask {} -gateway {}'.format(port_id, io_ip, netmask, gateway)
    if vlan:
        assert str(vlan).isdigit(), "[Assert Error] Input vlan is invalid!"
        command += ' -vlanId {}'.format(vlan)
        step_str += ", vlan: {}".format(vlan)

    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def create_nasserver_interface(storage, nasserver_name, port, ip_addr, netmask, gateway, vlan=None):

    step_str = "Add a nas server interface with parameter nasserver_name: {}, port: {}, ip_addr:{}, netmask:{}, gateway:{}".format(nasserver_name, port, ip_addr, netmask, gateway)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = '/net/nas/if create -serverName {} -port {} -addr {} -netmask {} -gateway {}'.format(nasserver_name, port, ip_addr, netmask, gateway)
    if vlan:
        assert str(vlan).isdigit(), "[Assert Error] Input vlan is invalid!"
        command += ' -vlanId {}'.format(vlan)
        step_str += ", vlan: {}".format(vlan)

    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def create_nas_vmware_pe(storage, nasserver_name, if_id):

    step_str = "Add a vmware pe with parameter serverName: {}, if_id:{}".format(nasserver_name, if_id)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = '/net/nas/vmwarepe create -serverName {} -if {}'.format(nasserver_name, if_id)
    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def create_capability_profile(storage):
    # TODO
    step_str = "Add a capability profile with parameter serverName: {}, if_id:{}".format()
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = ''.format()
    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def add_vcenter(storage, vcenter, username, password, register_vasa_provider='yes'):

    step_str = "Add a vCenter with vcenter: {}, username: {}, password: {}, registerVasaProvider: {}".format(vcenter, username, password, register_vasa_provider)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = '/virt/vmw/vc create -addr {} -username {} -passwd {} -registerVasaProvider {} -localUsername admin -localPasswd Password123!'.format(vcenter, username, password, register_vasa_provider)
    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def add_esxhost(storage, esx_host, vcenter_id):

    step_str = "Add a ESXi host with parameter esx_host: {}, vcenter_id: {}".format(esx_host, vcenter_id)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = '/virt/vmw/esx create -addr {} -vc {}'.format(esx_host, vcenter_id)
    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def create_vvol_ds(storage, name, ds_type, host, cp):

    cp_list = ','.join(cp.keys())
    cp_size_list = ','.join(cp.values())
    print(cp_list)
    print(cp_size_list)

    step_str = "Create a vVol datastore with name: {}, type: {}, cp: {}, host: {}...".format(name, ds_type, cp, host)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set
    command = '/stor/prov/vmware/vvolds create -name {} -cp {} -size {} -type {} -hosts {}'.format(name, cp_list, cp_size_list, ds_type, host)
    output, return_code = storage.run_uemcli(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def remove_vvol(storage, uemcli_host, vvol_uuid):

    step_str = "Remove VVol {} in storage...".format(vvol_uuid)
    LOG.print_log('INFO', step_str)
    check_output = check_output_for_uemcli_set

    command = '/stor/prov/vmware/vvol -id {} delete'.format(vvol_uuid)
    output, return_code = storage.run_uemcli(command, stdin_str='yes\n')

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


##############################################################################
# vSphere Actions
##############################################################################

@ensure_action_succeed_decorator
def create_vm(vm_name, template_name, ds_name, esx_host, windows_host):

    step_str = "Create a virtual machine with parameter vm_name: {}, template_name:{}, datastore: {}".format(vm_name, template_name, ds_name)
    LOG.print_log('INFO', step_str)
    check_output = None
    command = \
        'powershell.exe $blockDS = Get-Datastore -Name {}; '.format(ds_name) + \
        '$template = Get-Template -Name {}; '.format(template_name) + \
        '$blockDS; ' + \
        '$template; ' + \
        'New-VM -Name {} -VMHost {} -Template $template -Datastore $blockDS -Confirm:$false'.format(vm_name, esx_host)
    output, return_code = windows_host.HOST_EC.host_runcmd(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def full_clone_vm(origin_vm_name, new_vm_name, ds_name, esx_host, windows_host):

    step_str = "Full clone a virtual machine with parameter origin_vm_name: {}, new_vm_name:{}, datastore: {}, esx_host: {}"\
        .format(origin_vm_name, new_vm_name, ds_name, esx_host)
    LOG.print_log('INFO', step_str)
    check_output = None
    command = \
        'powershell.exe $blockDS = Get-Datastore -Name {}; '.format(ds_name) + \
        '$blockDS; ' + \
        'New-VM -VMHost {} -VM {} -Name {} -Datastore $blockDS -Confirm:$false'.format(esx_host, origin_vm_name, new_vm_name)
    output, return_code = windows_host.HOST_EC.host_runcmd(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output

@ensure_action_succeed_decorator
def fast_clone_vm(origin_vm_name, new_vm_name, ds_name, esx_host, snapshot, windows_host):

    step_str = "Fast clone a virtual machine with parameter origin_vm_name: {}, new_vm_name:{}, datastore: {}, esx_host: {}, snapshot: {}"\
        .format(origin_vm_name, new_vm_name, ds_name, esx_host, snapshot)
    LOG.print_log('INFO', step_str)
    check_output = None
    command = \
        'powershell.exe $blockDS = Get-Datastore -Name {}; '.format(ds_name) + \
        '$blockDS; ' + \
        'New-VM -VMHost {} -VM {} -Name {} -LinkedClone -ReferenceSnapshot {} -Datastore $blockDS -Confirm:$false'\
            .format(esx_host, origin_vm_name, new_vm_name, snapshot)
    output, return_code = windows_host.HOST_EC.host_runcmd(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def remove_vm(vm_name, windows_host):

    step_str = "Remove the virtual machine with vm_name: {}...".format(vm_name)
    LOG.print_log('INFO', step_str)
    check_output = None

    command = \
        'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
        '$vm; ' + \
        'Remove-VM -VM $vm -Confirm:$false'

    output, return_code = windows_host.HOST_EC.host_runcmd(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def poweron_vm(vm_name, windows_host, thread_name=None):

    log_obj = LOG
    if thread_name is not None:
        log_obj = ExecuteLog('test_actions', LOG_LEVEL, testlog, thread_name=thread_name)

    step_str = "Power on the virtual machine {}".format(vm_name)
    log_obj.print_log('INFO', step_str)
    check_output = None

    command = \
        'powershell.exe Get-VM -Name {};'.format(vm_name)
    output, return_code = run_command_on_host_check_returncode(windows_host, command)

    if 'PoweredOff' in output:
        command = \
            'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
            '$vm; ' + \
            'Start-VM -VM $vm -Confirm:$false;'

        output, return_code = windows_host.HOST_EC.host_runcmd(command)

        log_obj.print_log('INFO', "output is:\n")
        log_obj.print_plain_log('INFO', output)
        log_obj.print_log('INFO', "exit status is:{}.".format(return_code))
    else:
        log_obj.print_log('INFO', "VM {} is already powered on.".format(vm_name))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def poweroff_vm(vm_name, windows_host, thread_name=None):

    log_obj = LOG
    if thread_name is not None:
        log_obj = ExecuteLog('test_actions', LOG_LEVEL, testlog, thread_name=thread_name)

    step_str = "Power off the virtual machine {}".format(vm_name)
    log_obj.print_log('INFO', step_str)
    check_output = None

    command = \
        'powershell.exe Get-VM -Name {};'.format(vm_name)
    output, return_code = run_command_on_host_check_returncode(windows_host, command)

    if 'PoweredOn' in output:
        command = \
            'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
            '$vm; ' + \
            'Stop-VM -VM $vm -Confirm:$false;'

        output, return_code = windows_host.HOST_EC.host_runcmd(command)

        log_obj.print_log('INFO', "output is:\n")
        log_obj.print_plain_log('INFO', output)
        log_obj.print_log('INFO', "exit status is:{}.".format(return_code))
    else:
        log_obj.print_log('INFO', "VM {} is already powered off.".format(vm_name))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def restart_vm(vm_name, windows_host):

    step_str = "Restart the virtual machine {}".format(vm_name)
    LOG.print_log('INFO', step_str)
    check_output = None

    command = \
        'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
        '$vm; ' + \
        'Restart-VM -VM $vm -Confirm:$false;'

    output, return_code = windows_host.HOST_EC.host_runcmd(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def create_harddisk(vm_name, ds_name, storage_policy, size_list, vcenter_obj, windows_host, thread_name=None):

    log_obj = LOG
    if thread_name is not None:
        log_obj = ExecuteLog('test_actions', LOG_LEVEL, testlog, thread_name=thread_name)

    step_str = "Create {} harddisk with vm: {}, datastore: {}, storage_policy: {}, size: {} GB...".format(len(size_list), vm_name, ds_name, storage_policy, size_list)
    log_obj.print_log('INFO', step_str)
    check_output = None

    command = \
        'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
        '$blockDS = Get-Datastore -Name {}; '.format(ds_name) + \
        '$server = Connect-VIServer -Server {} -Protocol https -User {} -Password {}; '.format(vcenter_obj.vcenter_ip, vcenter_obj.vcenter_username, vcenter_obj.vcenter_password) + \
        '$storagePolicy = Get-SpbmStoragePolicy -Server $server -Name {}; '.format(storage_policy) + \
        '$vm; ' + \
        '$blockDS; ' + \
        '$storagePolicy;'

    assert type(size_list) is list, "[Assert Error] Input size_list must be a list!"
    for size in size_list:
        command += 'New-HardDisk -VM $vm -Persistence Persistent -CapacityGB {} -Datastore $blockDS -StorageFormat Thin -StoragePolicy $storagePolicy -Confirm:$false; '.format(size)

    output, return_code = windows_host.HOST_EC.host_runcmd(command)

    log_obj.print_log('INFO', "output is:\n")
    log_obj.print_plain_log('INFO', output)
    log_obj.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def remove_harddisk(vm_name, ds_name, windows_host, size_list=None):

    if size_list is None:
        step_str = "Remove all harddisk in datastore: {}...".format(ds_name)
    else:
        assert type(size_list) is list and len(size_list) > 0 and all([type(_) is int for _ in size_list]), \
            "[Assert Error] Input size_l must be a non-empty list and all the items must be int!"
        step_str = "Remove harddisk with vm: {}, datastore: {}, size: {}...".format(vm_name, ds_name, size_list)
    LOG.print_log('INFO', step_str)
    check_output = None

    def get_name_for_delete_hd(output_string, size_l=None):
        vm_all_hd = {}
        hd_size = list()
        hd_filename = list()
        hd_name = list()

        for line in output_string.splitlines():
            if line.endswith('.vmdk'):
                m1 = re.match(r'(\[.+\.vmdk)', line)
                m2 = re.match(r'(\d+)\.(\d+)\s+.+\.vmdk', line)
                if m1:
                    hd_filename.append(m1.group(1))
                if m2:
                    hd_size.append(int(m2.group(1)))
            elif line.startswith('Hard disk '):
                m = re.search(r'(Hard disk \d+)', line)
                if m:
                    hd_name.append(m.group(1))

        LOG.print_plain_log('INFO', hd_size)
        LOG.print_plain_log('INFO', hd_filename)
        LOG.print_plain_log('INFO', hd_name)
        assert len(hd_size) == len(hd_filename) and len(hd_filename) == len(hd_name), \
            "[Assert Error] From the output, the number of disk size/filename/name are not equal!"

        delete_hd_index = list()
        for i in range(len(hd_filename)):
            vm_all_hd[hd_filename[i]] = hd_name[i]
            if ds_name in hd_filename[i]:
                if size_l:
                    assert type(size_l) is list and len(size_l) > 0, \
                        "[Assert Error] Input size_l must be a non-empty list!"
                    if hd_size[i] in size_l:
                        delete_hd_index.append(i)
                else:
                    delete_hd_index.append(i)

        LOG.print_plain_log('INFO', vm_all_hd)

        LOG.print_log('INFO', 'The following hard disk index is found to be deleted:')
        LOG.print_plain_log('INFO', delete_hd_index)
        return delete_hd_index

    #
    command = \
        'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
        '$hd_vm = Get-HardDisk -VM $vm; ' + \
        '$hd_vm; ' + \
        '$hd_vm.Filename; ' + \
        '$hd_vm.Name; '

    output, return_code = run_command_on_host_check_returncode(windows_host, command)

    # Get name for the hard disks to be deleted
    delete_hd_index = get_name_for_delete_hd(output, size_list)

    if len(delete_hd_index) == 0:
        LOG.print_log('INFO', "No hard disks under datastore {} need to be deleted.".format(ds_name))
        return step_str, '', 0, check_output

    command = \
        'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
        '$hd_vm = Get-HardDisk -VM $vm;'

    for index in delete_hd_index:
        command += \
            '$hd = $hd_vm[{}]; '.format(index) + \
            '$hd; ' + \
            'Remove-HardDisk -HardDisk $hd -DeletePermanently -Confirm:$false;'

    output, return_code = run_command_on_host_check_returncode(windows_host, command)
    time.sleep(120)

    return step_str, output, return_code, check_output


def remove_all_harddisk_in_datastore(vm_name, ds_name, windows_host):

    return remove_harddisk(vm_name, ds_name, windows_host, size_list=None)


@ensure_action_succeed_decorator
def set_harddisk_size(vm_name, ds_name, windows_host, origin_size_list, new_size_list):

    assert type(origin_size_list) is list and len(origin_size_list) > 0 and \
           all([type(_) is int for _ in origin_size_list]), \
        "[Assert Error] Input origin_size_list must be a non-empty list and all the items must be int!"

    assert type(new_size_list) is list and len(new_size_list) > 0 and \
           all([type(_) is int for _ in new_size_list]), \
        "[Assert Error] Input new_size_list must be a non-empty list and all the items must be int!"

    assert len(origin_size_list) == len(new_size_list), \
        "[Assert Error] The item number in origin_size_list must be equal to that in new_size_list!"

    step_str = "Set harddisks size from {} to {} in vm: {}, datastore: {}..." \
        .format(origin_size_list, new_size_list, vm_name, ds_name)
    LOG.print_log('INFO', step_str)
    check_output = None

    def get_index_for_harddisks(output_string, size_l):
        vm_all_hd = {}
        hd_size = list()
        hd_filename = list()
        hd_name = list()

        for line in output_string.splitlines():
            if line.endswith('.vmdk'):
                m1 = re.match(r'(\[.+\.vmdk)', line)
                m2 = re.match(r'(\d+)\.(\d+)\s+.+\.vmdk', line)
                if m1:
                    hd_filename.append(m1.group(1))
                if m2:
                    hd_size.append(int(m2.group(1)))
            elif line.startswith('Hard disk '):
                m = re.search(r'(Hard disk \d+)', line)
                if m:
                    hd_name.append(m.group(1))

        LOG.print_plain_log('INFO', hd_size)
        LOG.print_plain_log('INFO', hd_filename)
        LOG.print_plain_log('INFO', hd_name)
        assert len(hd_size) == len(hd_filename) and len(hd_filename) == len(hd_name), \
            "[Assert Error] From the output, the number of disk size/filename/name are not equal!"

        hd_index = list()
        for i in range(len(hd_filename)):
            vm_all_hd[hd_filename[i]] = hd_name[i]
            if ds_name in hd_filename[i]:
                assert type(size_l) is list and len(size_l) > 0, \
                    "[Assert Error] Input size_l must be a non-empty list!"
                if hd_size[i] in size_l:
                    hd_index.append(i)

        LOG.print_plain_log('INFO', vm_all_hd)

        LOG.print_log('INFO', 'The following hard disk index is found:')
        LOG.print_plain_log('INFO', hd_index)

        assert len(hd_index) == len(size_l), "[Assert Error] The number of harddisk found is not consistent with the input one."
        return hd_index

    #
    command = \
        'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
        '$hd_vm = Get-HardDisk -VM $vm; ' + \
        '$hd_vm; ' + \
        '$hd_vm.Filename; ' + \
        '$hd_vm.Name; '

    output, return_code = run_command_on_host_check_returncode(windows_host, command)

    # Get index for the hard disks to set size
    hd_index = get_index_for_harddisks(output, origin_size_list)

    command = \
        'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
        '$hd_vm = Get-HardDisk -VM $vm; '

    assert len(hd_index) == len(new_size_list), \
        "[Assert Error] The item number in hd_index and new_size_list must be the same!"

    i = 0
    for index in hd_index:
        new_size = new_size_list[i]
        command += \
            '$hd = $hd_vm[{}]; '.format(index) + \
            '$hd; ' + \
            'Set-HardDisk -HardDisk $hd -CapacityGB {} -Confirm:$false; '.format(new_size)
        i += 1

    output, return_code = run_command_on_host_check_returncode(windows_host, command)

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def create_snapshot(vm_name, snapshot_name, windows_host):

    step_str = "Create a snapshot with vm: {}, name: {}...".format(vm_name, snapshot_name)
    LOG.print_log('INFO', step_str)
    check_output = None

    command = \
        'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
        '$vm; ' + \
        'New-Snapshot -VM $vm -Name {} -Confirm:$false'.format(snapshot_name)

    output, return_code = windows_host.HOST_EC.host_runcmd(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def remove_snapshot(vm_name, snapshot_name, windows_host):

    step_str = "Remove the snapshot with vm: {}, name: {}...".format(vm_name, snapshot_name)
    LOG.print_log('INFO', step_str)
    check_output = None

    command = \
        'powershell.exe $vm = Get-VM -Name {}; '.format(vm_name) + \
        '$vm; ' + \
        '$snapshot = Get-Snapshot -VM $vm -Name {}; '.format(snapshot_name) + \
        '$snapshot; ' + \
        'Remove-Snapshot -Snapshot $snapshot -Confirm:$false'

    output, return_code = windows_host.HOST_EC.host_runcmd(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def unmount_datastore(ds_name, esx_host, windows_host):

    step_str = "Unmount the datastore with parameter ds_name: {}, esx_host:{}".format(ds_name, esx_host)
    LOG.print_log('INFO', step_str)
    check_output = None
    command = \
        'powershell.exe $ds = Get-Datastore -Name {} -VMHost {}; '.format(ds_name, esx_host)
    output, return_code = windows_host.HOST_EC.host_runcmd(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    if return_code != 0:
        LOG.print_log('WARNING', "Datastore with parameter ds_name: {}, esx_host:{} dose NOT exist!".format(ds_name, esx_host))
        return_code = 0
    else:
        command = \
            'powershell.exe Remove-Datastore -Datastore {} -VMHost {} -Confirm:$false; '.format(ds_name, esx_host)
        output, return_code = windows_host.HOST_EC.host_runcmd(command)

        LOG.print_log('INFO', "output is:\n")
        LOG.print_plain_log('INFO', output)
        LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


@ensure_action_succeed_decorator
def remove_vasa_provider(storage_mgmt_ip, windows_host):

    step_str = "Remove the storage VASA provider in vCenter with parameter storage_mgmt_ip: {}".format(storage_mgmt_ip)
    LOG.print_log('INFO', step_str)
    check_output = None

    def get_vasa_provider_index_to_delete(output_string, ip_addr):
        delete_index = None
        i = None
        for line in output.splitlines():
            if 'VasaVersion' in line:
                i = 0
                continue
            if type(i) is int:
                if '------' in line or len(line) == 0 or line.isspace():
                    continue
                else:
                    m = re.search(r'EMC.+https://(\d+\.\d+\.\d+\.\d+):', line)
                    if m and m.group(1) == ip_addr:
                        delete_index = i
                        break
                    i += 1

        assert type(delete_index) is int, "[Assert Error] Failed to find the vasa provider for storage {}.".format(ip_addr)
        LOG.print_log('INFO', 'Got index - {} for vasa provider that to delete for storage {}.'.format(delete_index, ip_addr))

        return delete_index

    #
    command = \
        'powershell.exe Get-VasaProvider; '
    output, return_code = run_command_on_host_check_returncode(windows_host, command)

    # Get the index for the VASA provider to be deleted
    delete_index = get_vasa_provider_index_to_delete(output, storage_mgmt_ip)

    command = \
        'powershell.exe $provider = Get-VasaProvider; ' + \
        '$provider; ' + \
        'Remove-VasaProvider -Provider $provider[{}] -Confirm:$false; '.format(delete_index)
    output, return_code = windows_host.HOST_EC.host_runcmd(command)

    LOG.print_log('INFO', "output is:\n")
    LOG.print_plain_log('INFO', output)
    LOG.print_log('INFO', "exit status is:{}.".format(return_code))

    return step_str, output, return_code, check_output


if __name__ == '__main__':
    pass
