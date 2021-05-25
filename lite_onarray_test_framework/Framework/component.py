from Framework.setup_testsuite import *
from Framework.threads import *

##############################################################################
# Module Variable
##############################################################################

LOG = ExecuteLog('component', LOG_LEVEL, testlog)

##############################################################################
# Common Function
##############################################################################

def get_object_profile(object, cmd, update_profile=True):
    object_type = object.__class__.__name__

    str_log = "Run uemcli show {}...".format(object_type)
    output, return_code = run_uemcli_check_returncode(object.storage, cmd, step_str=str_log)

    d_profile = {}
    for line in output.splitlines():
        m = re.search(r'(\b[a-zA-Z\s\-]+?)\s+=\s+(.*)', line)
        if m:
            # print('{} : {}'.format(m.group(1), m.group(2)))
            d_profile[m.group(1)] = m.group(2)

    LOG.print_log('DEBUG', "Get following {} profile:".format(object_type))
    LOG.print_plain_log('DEBUG', d_profile)

    if update_profile:
        object.profile.update(d_profile)
        LOG.print_log('INFO', "{} {} profile updated.".format(object_type, object.identifier))

    return d_profile


def get_object_profile_from_all(object, cmd):
    object_type = object.__class__.__name__
    id_field = object.identifier_field

    str_log = "Run uemcli show {}...".format(object_type)
    output, return_code = run_uemcli_check_returncode(object.storage, cmd, step_str=str_log)

    d_profile = {}
    for line in output.splitlines():
        #print(line)
        m_id = re.search(r'\d+.+\bID\s+=\s+(.*)', line)
        m = re.search(r'(\b[a-zA-Z\s\-]+?)\s+=\s+(.*)', line)

        if m_id:
            if d_profile.get('ID'):
                break
            else:
                d_profile = {}
        if m:
            # print('{} : {}'.format(m.group(1), m.group(2)))
            d_profile[m.group(1)] = m.group(2)
        if d_profile.get(id_field):
            if d_profile[id_field] == object.identifier:
                continue
            else:
                d_profile = {}

    LOG.print_log('DEBUG', "Get following profile for {}:".format(object_type))
    LOG.print_plain_log('DEBUG', d_profile)
    assert d_profile.get(id_field), "[Assert Error] Failed to find {} object with {} - {}!".\
        format(object_type, id_field, object.identifier)

    object.profile.update(d_profile)
    LOG.print_log('INFO', "{} {} profile updated.".format(object_type, object.identifier))


def get_object_mlucli_profile(object, cmd):
    object_type = object.__class__.__name__

    output, return_code = run_command_on_storage_check_returncode(object.storage, cmd)

    d_mlucli_profile = {}
    for line in output.splitlines():
        m = re.search(r'(\b[0-9a-zA-Z\s\-_]+?)\s+:\s+(.*)', line)
        if m:
            # print('{} : {}'.format(m.group(1), m.group(2)))
            d_mlucli_profile[m.group(1)] = m.group(2)

    LOG.print_log('DEBUG', "Get following {} mlucli profile:".format(object_type))
    for k in d_mlucli_profile.keys():
        LOG.print_plain_log('DEBUG', '{} : {}'.format(k, d_mlucli_profile[k]))

    object.mlucli_profile.update(d_mlucli_profile)
    LOG.print_log('INFO', "{} {} mlucli profile updated.".format(object_type, object.identifier))


##############################################################################
# Component Class
##############################################################################

class SP():

    SP_ID = ['spa', 'spb']

    def __init__(self, storage_obj, sp_id, profile={}):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(sp_id) is str and sp_id.lower() in self.SP_ID, "[Assert Error] Input sp_id is invalid!"

        self.storage = storage_obj
        self.sp_id = sp_id.lower()
        if self.sp_id == 'spa':
            self.sp_ip = self.storage.spa_ip
        elif self.sp_id == 'spb':
            self.sp_ip = self.storage.spb_ip

        self.profile = {}
        self.identifier = self.sp_id

        self.feature_state = {}

        if len(profile) > 0:
            self.profile.update(profile)

    def get_sp_profile(self):
        cmd = '/env/sp -id {} show -detail'.format(self.sp_id)
        get_object_profile(self, cmd)

    def get_feature_state(self):
        cmd = 'featurestate --all'
        output, return_code = run_command_on_storage_check_returncode(self.storage, cmd, sp_owner=self.sp_id)
        d_featureHash = {}
        for line in output.split('\n'):
            if len(line) > 0:
                name, state = line.split()
                # print(name, state)
                d_featureHash[name] = state

        LOG.print_log('DEBUG', "Get following feature state:")
        for k in d_featureHash.keys():
            LOG.print_plain_log('DEBUG', '{} : {}'.format(k, d_featureHash[k]))

        self.feature_state = dict(d_featureHash)
        assert len(self.feature_state) > 0, "[Assert Error] Failed to get feature state on {}!".format(self.sp_id)

        return self.feature_state

    def check_sp_reachable(self, timeout=60, thread_name=None):
        #
        if thread_name is None:
            log_obj = LOG
        else:
            assert type(thread_name) is str and len(thread_name) > 0 and not thread_name.isspace(), \
                "[Assert Error] The input thread_name {} is invalid!".format(thread_name)
            log_obj = ExecuteLog('component', LOG_LEVEL, testlog, thread_name=thread_name)
        #
        self.storage.check_sp_pingable(sp=self.sp_id, timeout=timeout, log_obj=log_obj)
        log_obj.print_log('INFO', "{} is reachable.".format(self.sp_id))

    def panic(self, enable_kdump=True, thread_name=None):
        #
        if thread_name is None:
            log_obj = LOG
        else:
            assert type(thread_name) is str and len(thread_name) > 0 and not thread_name.isspace(), \
                "[Assert Error] The input thread_name {} is invalid!".format(thread_name)
            log_obj = ExecuteLog('component', LOG_LEVEL, testlog, thread_name=thread_name)
        #
        self.clear_rescue_state_counters(log_obj=log_obj)

        #
        log_obj.print_log('INFO', 'Panicking Storage {} {}...'.format(self.sp_id, self.sp_ip))

        def trigger_panic(enable_kdump, thread_name):
            cmd = 'echo "{}" > /proc/sysrq-trigger'.format('c' if enable_kdump else 'b')
            output, return_code = \
                run_command_on_storage_check_returncode(self.storage, cmd, sp_owner=self.sp_id, log_obj=log_obj)

        my_threads = []
        name = 'trigger_panic'
        t = MyThread(task_function=trigger_panic, task_args=(enable_kdump,), is_daemon=True, name=name)
        LOG.print_log('INFO', "Start the thread {} to panic {}.".format(name, self.sp_id))
        t.start()
        my_threads.append(t)
        time.sleep(5)

        log_obj.print_log('INFO', 'Storage {} {} is paniced.'.format(self.sp_id, self.sp_ip))

    def reboot(self, thread_name=None):
        #
        if thread_name is None:
            log_obj = LOG
        else:
            assert type(thread_name) is str and len(thread_name) > 0 and not thread_name.isspace(), \
                "[Assert Error] The input thread_name {} is invalid!".format(thread_name)
            log_obj = ExecuteLog('component', LOG_LEVEL, testlog, thread_name=thread_name)
        #
        self.clear_rescue_state_counters(log_obj=log_obj)
        #
        log_obj.print_log('INFO', 'Rebooting Storage {} {}...'.format(self.sp_id, self.sp_ip))
        cmd = '/EMC/Platform/bin/svc_shutdown -r'
        output, return_code = \
            run_command_on_storage_check_returncode(self.storage, cmd, sp_owner=self.sp_id, log_obj=log_obj)
        time.sleep(10)
        log_obj.print_log('INFO', 'Storage {} {} is rebooted.'.format(self.sp_id, self.sp_ip))

    def clear_rescue_state_counters(self, log_obj=LOG):
        step_str = 'On {} - Clearing Rescue State Counters.'.format(self.sp_id)
        cmd = '/EMC/Platform/bin/svc_rescue_state -c'
        output, return_code = \
            run_command_on_storage_check_returncode(self.storage, cmd, step_str=step_str, sp_owner=self.sp_id, log_obj=log_obj)
        assert "Clearing BMC Faults" in output, "[Assert Error] Failed to {}!".format(step_str)

    def wait_for_reboot(self, wait_for_shutdown=True, timeout=1200, thread_name=None):
        #
        if thread_name is None:
            log_obj = LOG
        else:
            assert type(thread_name) is str and len(thread_name) > 0 and not thread_name.isspace(), \
                "[Assert Error] The input thread_name {} is invalid!".format(thread_name)
            log_obj = ExecuteLog('component', LOG_LEVEL, testlog, thread_name=thread_name)
        #
        if wait_for_shutdown:
            log_obj.print_log('INFO', 'Waiting for storage {} {} to complete shutdown...'.format(self.sp_id, self.sp_ip))
            check_not_pingable(self.sp_ip, timeout=timeout, host_type=self.sp_id, log_obj=log_obj)
            log_obj.print_log('INFO', 'Storage {} {} is shutdown.'.format(self.sp_id, self.sp_ip))

        log_obj.print_log('INFO', 'Waiting for storage {} {} to come up...'.format(self.sp_id, self.sp_ip))
        check_pingable(self.sp_ip, timeout=timeout, host_type=self.sp_id, log_obj=log_obj)
        log_obj.print_log('INFO', 'Storage {} {} is come up.'.format(self.sp_id, self.sp_ip))

    def wait_for_system_complete_state(self, timeout=3600, thread_name=None):
        #
        if thread_name is None:
            log_obj = LOG
        else:
            assert type(thread_name) is str and len(thread_name) > 0 and not thread_name.isspace(), \
                "[Assert Error] The input thread_name {} is invalid!".format(thread_name)
            log_obj = ExecuteLog('component', LOG_LEVEL, testlog, thread_name=thread_name)
        #
        start_time = time.time()
        while True:
            time.sleep(10)
            current_time = time.time()
            if current_time - start_time > timeout:
                break

            cmd_1 = '/sbin/get_boot_mode'
            output_1, return_code_1 = \
                run_command_on_storage_without_check(self.storage, cmd_1, sp_owner=self.sp_id, log_obj=log_obj)
            m1 = re.match(r'Normal Mode', output_1)

            cmd_2 = 'system-state.sh list'
            output_2, return_code_2 = \
                run_command_on_storage_check_returncode(self.storage, cmd_2, sp_owner=self.sp_id, log_obj=log_obj)
            m2 = re.search(r'\nsystem_complete', output_2)
            m3 = re.search(r'rebooting', output_2)

            if m3:
                log_obj.print_log('INFO', 'Storage {} {} reported a rebooting state, waiting...'.format(self.sp_id, self.sp_ip))
                continue

            if m1 and m2:
                log_obj.print_log('INFO', 'Storage {} {} get system_complete state.'.format(self.sp_id, self.sp_ip))
                return

        assert False, "[Assert Error] Storage {} {} didn't get system_complete state in {} seconds!".format(self.sp_id, self.sp_ip, timeout)


class System():

    def __init__(self, storage_obj, profile={}):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"

        self.storage = storage_obj
        self.profile = {}
        self.identifier = None

        if len(profile) > 0:
            self.profile.update(profile)

    def get_system_profile(self):
        cmd = '/stor/general/system show -detail'
        get_object_profile(self, cmd)


class Pool():

    def __init__(self, storage_obj, name, profile={}):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(name) is str and name != "" and not name.isspace(), "[Assert Error] Input pool name is invalid!"

        self.storage = storage_obj
        self.name = name
        self.identifier = self.name
        self.identifier_field = 'Name'
        self.profile = {self.identifier_field: self.identifier}

        if len(profile) > 0:
            self.profile.update(profile)

    def get_pool_profile(self):
        cmd = '/stor/config/pool -name {} show -detail'.format(self.name)
        get_object_profile(self, cmd)


class NasServer():

    def __init__(self, storage_obj, name, profile={}):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(name) is str and name != "" and not name.isspace(), "[Assert Error] Input pool name is invalid!"

        self.storage = storage_obj
        self.name = name
        self.identifier = self.name
        self.identifier_field = 'Name'
        self.profile = {self.identifier_field: self.identifier}
        self.interface_id = None
        self.nfs_id = None

        if len(profile) > 0:
            self.profile.update(profile)

    def get_nasserver_profile(self):
        cmd = '/net/nas/server -name {} show -detail'.format(self.name)
        get_object_profile(self, cmd)

    def get_nasserver_interface(self):
        cmd = '/net/nas/if -server {} show -detail'.format(self.profile['ID'])

        str_log = "Run uemcli show {} failed!".format(self.__class__.__name__)
        output, return_code = run_uemcli_check_returncode(self.storage, cmd, step_str=str_log)

        tmp_if_id = None
        for line in output.splitlines():
            m_id = re.search(r'\bID\s+=\s+(.*)', line)
            m_nasserver = re.search(r'\bNAS server\s+=\s+(.*)', line)

            if m_id:
                tmp_if_id = m_id.group(1)
                continue
            elif m_nasserver and tmp_if_id is not None:
                if m_nasserver.group(1) == self.profile['ID']:
                    self.interface_id = tmp_if_id
                    break

        LOG.print_log('INFO', "Get nasserver interface id {}.".format(self.interface_id))

    def get_nasserver_nfs(self):
        cmd = '/net/nas/nfs -server {} show -detail'.format(self.profile['ID'])
        output, return_code = self.storage.run_uemcli(cmd)

        LOG.print_log('INFO', "Command {} - output is:\n".format(cmd))
        LOG.print_plain_log('INFO', output)
        LOG.print_log('INFO', "exit status is:{}.".format(return_code))

        assert return_code == 0, "[Assert Error] uemcli show nas interface failed!"

        tmp_nfs_id = None
        for line in output.splitlines():
            m_id = re.search(r'\bID\s+=\s+(.*)', line)
            m_nasserver = re.search(r'\bNAS server\s+=\s+(.*)', line)

            if m_id:
                tmp_nfs_id = m_id.group(1)
                continue
            elif m_nasserver and tmp_nfs_id is not None:
                if m_nasserver.group(1) == self.profile['ID']:
                    self.nfs_id = tmp_nfs_id
                    break

        LOG.print_log('INFO', "Get nasserver interface id {}.".format(self.nfs_id))


class CapabilityProfile():

    def __init__(self, storage_obj, name, profile={}):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(name) is str and name != "" and not name.isspace(), "[Assert Error] Input capability profile name is invalid!"

        self.storage = storage_obj
        self.name = name
        self.identifier = self.name
        self.identifier_field = 'Name'
        self.profile = {self.identifier_field: self.identifier}

        if len(profile) > 0:
            self.profile.update(profile)

    def get_cp_profile(self):
        cmd = '/stor/config/cp show -detail'.format(self.name)
        get_object_profile_from_all(self, cmd)


class Datastore():

    def __init__(self, storage_obj, name, profile={}):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(name) is str and name != "" and not name.isspace(), "[Assert Error] Input capability profile name is invalid!"

        self.storage = storage_obj
        self.name = name
        self.identifier = self.name
        self.identifier_field = 'Name'
        self.profile = {self.identifier_field: self.identifier}

        if len(profile) > 0:
            self.profile.update(profile)

    def get_ds_profile(self):
        cmd = '/stor/prov/vmware/vvolds show -detail'.format(self.name)
        get_object_profile_from_all(self, cmd)


def fetch_all_object_profile(cls, storage_obj, cmd):
    all_profile = []
    object_type = cls.__name__

    str_log = "Run uemcli show {}...".format(object_type)
    output, return_code = run_uemcli_check_returncode(storage_obj, cmd, step_str=str_log)

    d_profile = {}
    lines = output.splitlines()
    for i in range(len(lines)):
        m1 = re.search(r'^\d+.*ID\s+=\s+(.*)', lines[i])
        m2 = re.search(r'(\b[a-zA-Z\s\-]+?)\s+=\s+(.*)', lines[i])
        if m1:
            # update the last vvol profile
            if d_profile.get('ID') is not None:
                all_profile.append(d_profile)
            # clear the d_profile for next one
            d_profile = {}
            d_profile['ID'] = m1.group(1)
            LOG.print_log('DEBUG', "Find {} {}.".format(object_type, d_profile['ID']))
        elif m2:
            # print('{} : {}'.format(m2.group(1), m2.group(2)))
            d_profile[m2.group(1)] = m2.group(2)

        if i == len(lines) - 1 and d_profile.get('ID') is not None:
            all_profile.append(d_profile)

    LOG.print_log('INFO', "Get {} {} profile.".format(len(all_profile), object_type))
    for p in all_profile:
        LOG.print_plain_log('INFO', p)

    return all_profile


class VVol():

    # Class Attribute
    VVOL_TYPE = ['Data', 'Config', 'Swap', 'Memory']
    REPLICA_TYPE = ['Base', 'Ready Snap']
    ALL_VVOL = []

    @classmethod
    def find_vvol(cls, storage_obj, datastore_id, vvol_size_b, vvol_type='Data', replica_type='Base', vm_uuid=None, fetch=True):
        """
        :param storage_obj: Storage instance
        :param datastore_id: str 'res_4'
        :param vvol_size_b: int 17179869184
        :param vvol_type: str
        :param replica_type: str
        :param vm_uuid: str
        :param fetch: True by default
        :return: vvol_obj: VVol instance
        """
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(datastore_id) is str and datastore_id.startswith('res_'), "[Assert Error] Input datastore_id is invalid!"
        assert type(vvol_size_b) is int and vvol_size_b > 0, "[Assert Error] Input vvol_size_b is invalid!"
        assert type(vvol_type) is str and vvol_type in cls.VVOL_TYPE, "[Assert Error] Input vvol_type is invalid!"
        assert type(replica_type) is str and replica_type in cls.REPLICA_TYPE, "[Assert Error] Input replica_type is invalid!"
        if vm_uuid is not None:
            assert type(vm_uuid) is str and len(vm_uuid) > 0 and not vm_uuid.isspace(), "[Assert Error] Input vm_uuid is invalid!"

        if fetch:
            LOG.print_log('INFO', "Fetch all VVol information using uemcli...")
            cmd = '/stor/prov/vmware/vvol show -detail'
            cls.ALL_VVOL = fetch_all_object_profile(cls, storage_obj, cmd)

        vvol_uuid = None
        for vvol_profile in cls.ALL_VVOL:
            if int(vvol_profile['Size'].split()[0]) == int(vvol_size_b) and \
               vvol_profile['Type'] == vvol_type and \
               vvol_profile['Replica type'] == replica_type and \
               vvol_profile['Datastore'] == datastore_id:
                if vm_uuid:
                    if vvol_profile['Virtual machine'] == vm_uuid:
                        vvol_uuid = vvol_profile['ID']
                        break
                else:
                    vvol_uuid = vvol_profile['ID']
                    break

        assert vvol_uuid, "[Assert Error] Failed to find the specfied VVol!"
        LOG.print_log('INFO', "Get satisfied VVol - {}.".format(vvol_uuid))

        vvol_obj = VVol(storage_obj, vvol_uuid)
        vvol_obj.get_vvol_profile()
        vvol_obj.get_vvol_mlucli_profile()

        return vvol_obj

    @classmethod
    def find_vvols(cls, storage_obj, datastore_id, vvol_size_b, vvol_type='Data', replica_type='Base', vm_uuid=None, fetch=True):
        """
        :param storage_obj: Storage instance
        :param datastore_id: str 'res_4'
        :param vvol_size_b: int 17179869184
        :param vvol_type: str
        :param replica_type: str
        :param vm_uuid: str
        :param fetch: True by default
        :return: vvols: VVol instance list
        """
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(datastore_id) is str and datastore_id.startswith('res_'), "[Assert Error] Input datastore_id is invalid!"
        assert type(vvol_size_b) is int and vvol_size_b > 0, "[Assert Error] Input vvol_size_b is invalid!"
        assert type(vvol_type) is str and vvol_type in cls.VVOL_TYPE, "[Assert Error] Input vvol_type is invalid!"
        assert type(replica_type) is str and replica_type in cls.REPLICA_TYPE, "[Assert Error] Input replica_type is invalid!"
        if vm_uuid is not None:
            assert type(vm_uuid) is str and len(vm_uuid) > 0 and not vm_uuid.isspace(), "[Assert Error] Input vm_uuid is invalid!"

        def create_vvol_obj(uuid):
            vvol_obj = VVol(storage_obj, vvol_uuid)
            vvol_obj.get_vvol_profile()
            vvol_obj.get_vvol_mlucli_profile()
            return vvol_obj

        if fetch:
            LOG.print_log('INFO', "Fetch all VVol information using uemcli...")
            cmd = '/stor/prov/vmware/vvol show -detail'
            cls.ALL_VVOL = fetch_all_object_profile(cls, storage_obj, cmd)

        vvols = []
        for vvol_profile in cls.ALL_VVOL:
            if int(vvol_profile['Size'].split()[0]) == int(vvol_size_b) and \
               vvol_profile['Type'] == vvol_type and \
               vvol_profile['Replica type'] == replica_type and \
               vvol_profile['Datastore'] == datastore_id:
                if vm_uuid:
                    if vvol_profile['Virtual machine'] == vm_uuid:
                        vvol_uuid = vvol_profile['ID']
                        vvol = create_vvol_obj(vvol_uuid)
                        vvols.append(vvol)
                else:
                    vvol_uuid = vvol_profile['ID']
                    vvol = create_vvol_obj(vvol_uuid)
                    vvols.append(vvol)

        assert len(vvols) > 0, "[Assert Error] Failed to find satisfied VVol!"
        LOG.print_log('INFO', "Get {} satisfied VVol:".format(len(vvols)))
        for vvol in vvols:
            LOG.print_plain_log('INFO', '{}, {}'.format(vvol.uuid, vvol.profile['Size']))

        return vvols

    @classmethod
    def find_vvol_uuid_in_datastore(cls, storage_obj, datastore_id, vvol_type=None, replica_type=None):
        """
        :param storage_obj:
        :param datastore_id:
        :param vvol_type:
        :param replica_type:
        :return: vvol_uuid: list
        """
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(datastore_id) is str and datastore_id.startswith('res_'), "[Assert Error] Input datastore_id is invalid!"
        assert vvol_type is None or (type(vvol_type) is str and vvol_type in cls.VVOL_TYPE), "[Assert Error] Input vvol_type is invalid!"
        assert replica_type is None or (type(replica_type) is str and replica_type in cls.REPLICA_TYPE), "[Assert Error] Input replica_type is invalid!"

        LOG.print_log('INFO', "Fetch all VVol information using uemcli...")
        cmd = '/stor/prov/vmware/vvol show -detail'
        cls.ALL_VVOL = fetch_all_object_profile(cls, storage_obj, cmd)

        vvols_uuid = []
        for vvol_profile in cls.ALL_VVOL:
            if vvol_profile['Datastore'] != datastore_id:
                continue
            if vvol_type and vvol_profile['Type'] != vvol_type:
                continue
            if replica_type and vvol_profile['Replica type'] != replica_type:
                continue
            vvols_uuid.append(vvol_profile['ID'])

        if len(vvols_uuid) == 0:
            LOG.print_log('INFO', "No VVol is found in datastore {} with vvol_type - {}, replica_type - {}.".format(datastore_id, vvol_type, replica_type))
        else:
            LOG.print_log('INFO', "{} VVols are found in datastore {} with vvol_type - {}, replica_type - {}.".format(len(vvols_uuid), datastore_id, vvol_type, replica_type))
            LOG.print_plain_log('INFO', vvols_uuid)
        return vvols_uuid

    def __init__(self, storage_obj, uuid, vvol_type=None, replica_type=None, profile={}):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(uuid) is str and uuid.startswith('naa.'), "[Assert Error] Input vvol uuid is invalid!"
        if vvol_type:
            assert type(vvol_type) is str and vvol_type in VVol.VVOL_TYPE, "[Assert Error] Input vvol_type is invalid!"
        if replica_type:
            assert type(replica_type) is str and replica_type in VVol.REPLICA_TYPE, "[Assert Error] Input replica_type is invalid!"

        # if size_GB is not None:
        #     assert type(size_GB) is str or type(size_GB) is int or type(size_GB) is float, "[Assert Error] Input size_GB must be string/int/float!"
        #     if type(size_GB) is str:
        #         m = re.search(r'[^0-9\.]', size_GB)
        #         assert len(size_GB) > 0 and m is None, "[Assert Error] Input size_GB is string but in invalid format!"
        #     size_GB = float(size_GB)

        self.storage = storage_obj
        self.uuid = uuid
        self.vvol_type = vvol_type
        self.replica_type = replica_type

        self.identifier = self.uuid
        self.identifier_field = 'ID'
        self.profile = {self.identifier_field: self.identifier}
        self.vvol_oid = None
        self.vvol_inode = None
        self.mlucli_profile = {}

        if len(profile) > 0:
            self.profile.update(profile)

    def get_vvol_profile(self):
        cmd = '/stor/prov/vmware/vvol -id {} show -detail'.format(self.uuid)
        get_object_profile(self, cmd)
        self.vvol_type = self.profile['Type']
        self.replica_type = self.profile['Replica type']

    def get_vvol_mlucli_profile(self):
        cmd = 'MluCli.exe poll -vvol | grep -B 15 "{}" | grep Key'.format(self.uuid)
        output, return_code = run_command_on_storage_check_returncode(self.storage, cmd)

        m = re.search(r'^Key\s+:\s+(0x[0-9a-zA-Z]+)', output)
        assert m, "[Assert Error] Failed to get VVol object id!"
        self.vvol_oid = m.group(1)
        LOG.print_log('INFO', "Get vvol oid: {}".format(self.vvol_oid))

        cmd = 'MluCli.exe poll -vvol {}'.format(self.vvol_oid)
        get_object_mlucli_profile(self, cmd)

    def get_vvol_inode(self):
        cmd = 'MluCli.exe poll -vu | grep -A 50 "{}" | grep -E "Identification_NiceName|FSID|Cbfs_Inode_Number"'.format(self.uuid)
        output, return_code = run_command_on_storage_check_returncode(self.storage, cmd)

        m = re.search(r'Identification_NiceName\s+:\s+(naa.+)\nFSID\s+:\s+(\d+)\nCbfs_Inode_Number\s+:\s+([0-9A-Za-z]+)', output)
        assert m, "[Assert Error] Failed to get VVol informations from MluCli.exe poll -vu!"
        if m.group(1) == self.uuid:
            self.vvol_inode = str(int(m.group(3), 16))

        if self.vvol_inode is None:
            LOG.print_log('INFO', "Failed to get vvol inode number for vvol {}".format(self.uuid))
        else:
            LOG.print_log('INFO', "Get vvol inode number: {}".format(self.vvol_inode))

    def check_vvol_online(self, timeout=60):
        while timeout > 0:
            self.get_vvol_profile()
            if 'OK' in self.profile['Health state']:
                LOG.print_log('INFO', "VVol {} is already online.".format(self.uuid))
                return
            timeout -= 5
            time.sleep(5)

        assert False, "[Assert Error] VVol {} health state is {}, it is not online in {} seconds!". \
            format(self.uuid, self.profile['Health state'], timeout)

    def check_vvol_offline(self, timeout=60):
        while timeout > 0:
            self.get_vvol_profile()
            if 'Critical failure' in self.profile['Health state']:
                LOG.print_log('INFO', "VVol {} is already offline.".format(self.uuid))
                return
            timeout -= 5
            time.sleep(5)

        assert False, "[Assert Error] VVol {} health state is {}, it is not offline in {} seconds!". \
            format(self.uuid, self.profile['Health state'], timeout)

    def restore_snap_vvol(self):
        assert self.vvol_type == 'Data' and self.replica_type == 'Ready Snap',\
            "[Assert Error] The vvol to restore must be a snap data vvol!"

        parent_uuid = self.profile['Parent']
        snap_uuid = self.uuid
        str_log = "Restore parent {} with snap {}...".format(parent_uuid, snap_uuid)
        cmd = '/stor/prov/vmware/vvol -id {} restore -snap {}'.format(parent_uuid, snap_uuid)
        run_uemcli_check_returncode(self.storage, cmd, step_str=str_log)


class VCenter():

    def __init__(self, storage_obj, vcenter_ip, vcenter_username, vcenter_password, profile={}):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(vcenter_ip) is str and vcenter_ip != "" and not vcenter_ip.isspace(), "[Assert Error] Input vcenter_ip is invalid!"

        self.storage = storage_obj
        self.vcenter_ip = vcenter_ip
        self.vcenter_username = vcenter_username
        self.vcenter_password = vcenter_password

        self.identifier = self.vcenter_ip
        self.identifier_field = 'Address'
        self.profile = {self.identifier_field: self.identifier}

        if len(profile) > 0:
            self.profile.update(profile)

    def get_vcenter_profile(self):
        cmd = '/virt/vmw/vc show -detail'
        get_object_profile_from_all(self, cmd)


class ESXHost():

    def __init__(self, storage_obj, esxhost_ip, profile={}):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(esxhost_ip) is str and esxhost_ip != "" and not esxhost_ip.isspace(), "[Assert Error] Input esxhost_ip is invalid!"

        self.storage = storage_obj
        self.esxhost_ip = esxhost_ip
        self.identifier = self.esxhost_ip
        self.identifier_field = 'Name'
        self.profile = {self.identifier_field: self.identifier}

        if len(profile) > 0:
            self.profile.update(profile)

    def get_esxhost_profile(self):
        cmd = '/virt/vmw/esx show -detail'
        get_object_profile_from_all(self, cmd)


class Host():

    def __init__(self, storage_obj, host_obj, host_name, host_ip, profile={}):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert isinstance(host_obj, LinuxHost), "[Assert Error] Input storage_obj is invalid!"
        assert type(host_name) is str and host_name != "" and not host_ip.isspace(), "[Assert Error] Input host_name is invalid!"
        assert type(host_ip) is str and host_ip != "" and not host_ip.isspace(), "[Assert Error] Input host_ip is invalid!"

        self.storage = storage_obj
        self.host = host_obj
        self.host_name = host_name
        self.host_ip = host_ip
        self.identifier = self.host_name
        self.identifier_field = 'Name'
        self.profile = {self.identifier_field: self.identifier}

        if len(profile) > 0:
            self.profile.update(profile)

        self.host_iqn = None
        self.host_initiator_profile = None
        self.iscsi_port = '3260'
        self.iscsi_ip_list = []
        self.iscsi_iqn_list = []

    def get_host_profile(self):
        cmd = '/remote/host -name {} show -detail'.format(self.host_name)
        get_object_profile(self, cmd)

    def get_host_iqn(self):
        cmd = 'cat /etc/iscsi/initiatorname.iscsi'
        output, return_code = run_command_on_host_check_returncode(self.host, cmd)
        m = re.search(r'InitiatorName=(iqn.+)', output)
        if m:
            self.host_iqn = m.group(1)

        assert self.host_iqn, "[Assert Error] Failed to get IQN for Host-{}!".format(self.identifier)
        LOG.print_log('INFO', 'IQN for Host-{} is {}.'.format(self.identifier, self.host_iqn))

        return self.host_iqn

    def check_iscsi_session(self, iqn_list, ip_list):
        assert type(iqn_list) is list and len(iqn_list) > 0, "[Assert Error] Input iqn_list {} is invalid!".format(iqn_list)
        assert type(ip_list) is list and len(ip_list) > 0, "[Assert Error] Input ip_list {} is invalid!".format(ip_list)
        assert len(iqn_list) == len(ip_list), "[Assert Error] The number of ip_list and iqn_list must be same!"

        cmd = 'iscsiadm -m session -P 3'
        output, return_code = run_command_on_host_check_returncode(self.host, cmd)

        for i in range(0, len(ip_list)):
            iqn = iqn_list[i]
            ip_addr = ip_list[i]
            LOG.print_log('INFO', 'Check iscsi session for target {} ip={}'.format(iqn, ip_addr))
            m = re.search(r'Target:\s+' + iqn + r'.+\n\s+Current Portal:\s+' + ip_addr + ':' + self.iscsi_port, output)
            assert m, "[Assert Error] Failed to find iscsi session for target {} ip={}!".format(iqn, ip_addr)

    def check_no_iscsi_session(self):
        cmd = 'iscsiadm -m session -P 3'
        output, return_code = run_command_on_host_without_check(self.host, cmd)

    def establish_iscsi_connection(self, ip_list):
        port = self.iscsi_port

        def add_portal_for_interface(ip_addr):
            cmd = 'iscsiadm -m discoverydb -p {}:{} -t st -o new'.format(ip_addr, port)
            output, return_code = run_command_on_host_check_returncode(self.host, cmd)
            assert 'New discovery record for [{},{}] added'.format(ip_addr, port) in output, \
                "[Assert Error] Failed to add new record for {}!".format(ip_addr)

            cmd = 'iscsiadm -m discoverydb -p {}:{} -t st --discover'.format(ip_addr, port)
            output, return_code = run_command_on_host_check_returncode(self.host, cmd)
            m = re.search(ip_addr + ':' + port + r'.*(iqn.+)', output)
            assert m, "[Assert Error] Failed to find record for {}!".format(ip_addr)

            if_iqn = m.group(1)
            LOG.print_log('INFO', 'Get storage interface {} iqn: {}.'.format(ip_addr, if_iqn))
            return if_iqn

        def log_into_target(iqn, ip_addr):
            LOG.print_log('INFO', 'Logging into target {} ip={}'.format(iqn, ip_addr))
            cmd = 'iscsiadm -m node --target {} --portal {}:{} --login'.format(iqn, ip_addr, port)
            output, return_code = run_command_on_host_check_returncode(self.host, cmd)
            m = re.search(r'Login to.*target:\s+' + iqn + r'.*portal:\s+' + ip_addr + ',' + port + r'.*successful', output)
            assert m, "[Assert Error] Failed to log into target {} ip={}!".format(iqn, ip_addr)

        # STEP_1
        LOG.print_log('INFO', 'Check iscsi env is clean.')

        cmd_1 = 'iscsiadm -m discoverydb'
        output_1, return_code_1 = run_command_on_host_without_check(self.host, cmd_1)
        cmd_2 = 'iscsiadm -m session -R'
        output_2, return_code_2 = run_command_on_host_without_check(self.host, cmd_2)

        if len(output_1) == 0 and 'No session found' in output_2:
            LOG.print_log('INFO', 'ISCSI env is clean, no session found.')
        else:
            pass
            # TODO: delete old iscsi session

        # STEP_2
        LOG.print_log('INFO', 'Add target portal for storage interface.')
        iqn_list = []
        for ip_addr in ip_list:
            if_iqn = add_portal_for_interface(ip_addr)
            iqn_list.append(if_iqn)
        assert len(iqn_list) == len(ip_list), "[Assert Error] The number of ip_list and iqn_list is not same!"

        # STEP_3
        LOG.print_log('INFO', 'Logging into target.')
        for i in range(0, len(ip_list)):
            iqn = iqn_list[i]
            ip_addr = ip_list[i]
            log_into_target(iqn, ip_addr)
        self.iscsi_ip_list = ip_list
        self.iscsi_iqn_list = iqn_list

        # STEP_4
        LOG.print_log('INFO', 'Check iscsi session.')
        self.check_iscsi_session(self.iscsi_iqn_list, self.iscsi_ip_list)

    def teardown_iscsi_connection(self):

        def log_out_target(iqn, ip_addr):
            LOG.print_log('INFO', 'Log out of target {} ip={}'.format(iqn, ip_addr))
            cmd = 'iscsiadm -m node -u -T {} -p {}:{}'.format(iqn, ip_addr, self.iscsi_port)
            output, return_code = run_command_on_host_check_returncode(self.host, cmd)
            m = re.search(r'Logout of.*target:\s+' + iqn + r'.*portal:\s+' + ip_addr + ',' + self.iscsi_port + r'.*successful', output)
            assert m, "[Assert Error] Failed to log out of target {} ip={}!".format(iqn, ip_addr)

        def delete_portal_for_interface(ip_addr):
            cmd = 'iscsiadm -m discoverydb -p {}:{} -o delete -t st'.format(ip_addr, self.iscsi_port)
            output, return_code = run_command_on_host_check_returncode(self.host, cmd)

        # STEP_1
        LOG.print_log('INFO', 'Check iscsi session.')

        assert len(self.iscsi_iqn_list) == len(self.iscsi_ip_list), \
            "[Assert Error] The number of iscsi_iqn_list and iscsi_ip_list is not same!"

        cmd = 'iscsiadm -m session -R'
        output, return_code = run_command_on_host_check_returncode(self.host, cmd)
        for i in range(0, len(self.iscsi_ip_list)):
            iqn = self.iscsi_iqn_list[i]
            ip_addr = self.iscsi_ip_list[i]
            m = re.search(r'Rescanning session.+' + r'target:\s+' + iqn + r'.+portal:\s+' + ip_addr + ',' + self.iscsi_port, output)
            if m:
                LOG.print_log('INFO', 'Rescanning session target {} ip={}'.format(iqn, ip_addr))
            else:
                LOG.print_log('WARNING', 'Failed to find session target {} ip={}'.format(iqn, ip_addr))

        self.check_iscsi_session(self.iscsi_iqn_list, self.iscsi_ip_list)

        # STEP_2
        LOG.print_log('INFO', 'Logout of iscsi session.')
        for i in range(0, len(self.iscsi_ip_list)):
            iqn = self.iscsi_iqn_list[i]
            ip_addr = self.iscsi_ip_list[i]
            log_out_target(iqn, ip_addr)

        # STEP_3
        LOG.print_log('INFO', 'Add target portal for storage interface.')
        for ip_addr in self.iscsi_ip_list:
            delete_portal_for_interface(ip_addr)

        self.iscsi_iqn_list = []
        self.iscsi_ip_list = []

        # STEP_4
        LOG.print_log('INFO', 'Check no iscsi session exist.')
        self.check_no_iscsi_session()

    def get_host_initiator(self):
        cmd = '/remote/initiator -host {} show -detail'.format(self.profile['ID'])
        self.host_initiator_profile = get_object_profile(self, cmd, update_profile=False)

        LOG.print_log('INFO', 'Get host_initiator_profile:')
        LOG.print_plain_log('INFO', self.host_initiator_profile)

        assert type(self.host_initiator_profile) is dict and len(self.host_initiator_profile) > 0, \
            "[Assert Error] Failed to get initiator profile for Host-{}!".format(self.identifier)

        return self.host_initiator_profile

    def check_host_initiator_state(self, state='OK', timeout=300):
        sleep_interval = 30
        while timeout > 0:
            self.get_host_initiator()
            health_state = self.host_initiator_profile['Health State']
            if state in health_state:
                LOG.print_log('INFO', 'Already got state {} in health state {}.'.format(state, health_state))
                return
            LOG.print_log('INFO', 'Wait for {} second and check again...'.format(sleep_interval))
            timeout -= sleep_interval
            time.sleep(sleep_interval)

        assert False, "[Assert Error] For Host {} initiator, failed to get state {} in {} second!" \
            .format(self.host_name, state, timeout)


##############################################################################
# Internal Component Class
##############################################################################
class CBFS():

    # Class Attribute
    ALL_CBFS = []

    def __init__(self, storage_obj, fsid, sp_owner='spa'):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(fsid) is str and fsid.startswith('107'), "[Assert Error] Input fsid is invalid!"
        assert type(sp_owner) is str and sp_owner.lower() in ['spa', 'spb'], "[Assert Error] Input sp_owner is invalid!"

        self.storage = storage_obj
        self.fsid = fsid
        self.sp_owner = sp_owner.lower()
        self.identifier = self.fsid

    def get_fsInfo(self):
        cmd = 'TestMluServiceApi.exe "fsInfo fsid={}"'.format(self.fsid)
        output, return_code = run_command_on_storage_check_returncode(self.storage, cmd, sp_owner=self.sp_owner)
        return output


class PoolAllocation():

    def __init__(self, storage_obj, oid):
        assert isinstance(storage_obj, Storage), "[Assert Error] Input storage_obj is invalid!"
        assert type(oid) is str and oid.startswith('0x34'), "[Assert Error] Input fsid is invalid!"

        self.storage = storage_obj
        self.oid = oid
        self.mlucli_profile = {}
        self.identifier = self.oid

    def get_poolallocation_mlucli_profile(self):
        cmd = 'MluCli.exe poll -poolalloc {}'.format(self.oid)
        get_object_mlucli_profile(self, cmd)



if __name__ == '__main__':
    pass

