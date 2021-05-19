#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from urllib.parse import urlparse
from util.colorPrint import ColorPrint
import logging
import re
import github
import os
import os.path
import click
import sys
import traceback
import time
import base64
from email.mime.text import MIMEText
import smtplib
import json
import subprocess
import shlex


class LogHelper():
    HEADER = ColorPrint.HEADER
    OKBLUE = ColorPrint.OKBLUE
    OKGREEN = ColorPrint.OKGREEN
    WARNING = ColorPrint.WARNING
    FAIL = ColorPrint.FAIL
    ENDC = ColorPrint.ENDC
    BOLD = ColorPrint.BOLD
    UNDERLINE = ColorPrint.UNDERLINE

    def __init__(self, logfilename='/tmp/%s.log' % os.path.basename(__file__).rsplit('.')[0], name='default',
                 screenlevel=logging.INFO, filelevel=logging.DEBUG):
        self.logfilename = logfilename
        self.name = name
        self.screenlevel = screenlevel
        self.filelevel = filelevel
        # logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        # file handler
        self.fh = logging.FileHandler(logfilename)
        self.fh.setLevel(self.filelevel)
        self.fh.setFormatter(logging.Formatter('*%(asctime)s|%(levelno)s|%(process)d - %(message)s'))
        # stream handler
        self.shout = logging.StreamHandler(stream=sys.stdout)
        self.shout.setLevel(self.screenlevel)
        self.shout.setFormatter(logging.Formatter('%(message)s'))
        self.sherr = logging.StreamHandler()
        self.sherr.setLevel(self.screenlevel)
        self.sherr.setFormatter(logging.Formatter('%(message)s'))

    def debugPrint(self, msg):
        # message for stream handler
        for _msg in msg.strip().split('\n'):
            smsg = '[DEBUG] %s' % (_msg)
            self.logger.addHandler(self.fh)
            self.logger.debug(msg)
            self.logger.removeHandler(self.fh)
            self.logger.addHandler(self.shout)
            self.logger.debug(smsg)
            self.logger.removeHandler(self.shout)

    def errorPrint(self, msg):
        # message for stream handler
        for _msg in msg.strip().split('\n'):
            smsg = '%s %s' % (ColorPrint('[ERROR]', ColorPrint.FAIL), _msg)
            self.logger.addHandler(self.fh)
            self.logger.error(msg)
            self.logger.removeHandler(self.fh)
            self.logger.addHandler(self.sherr)
            self.logger.error(smsg)
            self.logger.removeHandler(self.sherr)

    def warnPrint(self, msg):
        # message for stream handler
        for _msg in msg.strip().split('\n'):
            smsg = '%s %s' % (ColorPrint('[WARN]', ColorPrint.WARNING), _msg)
            self.logger.addHandler(self.fh)
            self.logger.warning(msg)
            self.logger.removeHandler(self.fh)
            self.logger.addHandler(self.shout)
            self.logger.warning(smsg)
            self.logger.removeHandler(self.shout)

    def infoPrint(self, msg, style=OKGREEN):
        # message for stream handler
        for _msg in msg.strip().split('\n'):
            smsg = '%s %s' % (ColorPrint('[INFO]', style), _msg) if style else '[INFO] %s' % _msg
            self.logger.addHandler(self.fh)
            self.logger.info(msg)
            self.logger.removeHandler(self.fh)
            self.logger.addHandler(self.shout)
            self.logger.info(smsg)
            self.logger.removeHandler(self.shout)

    def p(self, msg, loglevel='DEBUG', noln=False):
        funcname = loglevel.lower() + 'Print'
        getattr(self, funcname)(msg)


log = LogHelper(screenlevel=logging.INFO)


def die(message, exit_code=255):
    """Terminate, displaying an error message."""
    log.errorPrint(message)
    sys.exit(exit_code)


def get_admin():
    def _prompt():
        admin = click.prompt("Please input admin")
        adminpass = click.prompt("Password", hide_input=True)
        return admin, adminpass
    sm_file = '/net/sles15-chenq9-dev-00/c4_working/chenq9/sm'
    pattern = re.compile(b'''u:(\S+);p:(\S+)$''')
    if os.path.exists(sm_file):
        try:
            with open(sm_file, 'rb') as fh:
                for line in fh:
                    decode_string = base64.b64decode(line)
                    if_match = pattern.match(decode_string)
                    if if_match is not None:
                        admin = if_match.group(1).decode()
                        adminpass = if_match.group(2).decode()
                        return admin, adminpass
        except Exception:
            return _prompt()
    else:
        return _prompt()


def get_local_user():
    corpid = ''
    output = os.popen('git config --list')
    for line in output.read().split('\n'):
        ifmatch = re.match('adsk.github.account=(.*)', line)
        if ifmatch is not None:
            corpid =  ifmatch.group(1)
    if corpid == '':
        corpid = click.prompt("Please provide your CORP ID")
    else:
        corpid = click.prompt("Please provide your CORP ID", default=corpid)
    return corpid


def get_branch_state(branch_name):
#    build_state_file = '/c4site/SOBO/Public/zhengh3/SM/branch_state'
    build_state_file = '/net/sles15-chenq9-dev-00/c4_working/chenq9/SM/branch_state'
    if os.path.exists(build_state_file):
        with open(build_state_file, 'rt') as fh:
            for line in fh:
                re_match = re.match(r'%s : (\S+)' % branch_name, line)
                if re_match is not None:
                    return re_match.group(1)
            return 'not_support'
    else:
        die('%s is inaccessible. Please contact the stream manager.' % build_state_file)


def check_mlu_santiy(log_path):
    exe = 'check_sanity'
    exe_path = '/'.join((os.path.dirname(os.path.abspath(sys.argv[0])), exe))
    if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
        cmd = "%s %s" % (exe_path, log_path)
        log.debugPrint("[RUN] %s" % cmd)
        rc = os.system(cmd)
        if rc == 0:
            return True
        else:
            return False
    else:
        # log.warnPrint("%s is not executable or not exist. Anyway we can go ahead." % exe_path)
        # return True
        die("%s does not exist or is inexecutable." % exe_path)


def check_build(item, log_path):
    exe = 'check_build'
    exe_path = '/'.join((os.path.dirname(os.path.abspath(sys.argv[0])), exe))
    if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
        cmd = "%s --type %s %s" % (exe_path, item, log_path)
        log.debugPrint("[RUN] %s" % cmd)
        rc = os.system(cmd)
        if rc == 0:
            return True
        else:
            return False
    else:
        # log.warnPrint("%s is not executable or not exist. Anyway we can go ahead." % exe_path)
        # return True
        die("%s does not exist or is inexecutable." % exe_path)

def check_nxgui(log_path):
    # nxgui/NxGenWorkspace/cemgui-app/build.sh run-automation-tests
    # nxgui/NxGenWorkspace/cemgui-app/build.sh run-automation-tests-vvnx
    # nxgui/NxGenWorkspace/results/cemgui/selenium.txt
    exe = 'check_nxgui'
    exe_path = '/'.join((os.path.dirname(os.path.abspath(sys.argv[0])), exe))
    if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
        cmd = "%s %s" % (exe_path, log_path)
        log.debugPrint("[RUN] %s" % cmd)
        rc = os.system(cmd)
        if rc == 0:
            return True
        else:
            return False
    else:
        # log.warnPrint("%s is not executable or not exist. Anyway we can go ahead." % exe_path)
        # return True
        die("%s does not exist or is inexecutable." % exe_path)


def grant_permission(member, removelater=300):
    svr = '10.141.33.98'
    cmd = 'ssh c4dev@%s "github_member_manager add --removelater %d %s"' % (svr, removelater, member)
    log.debugPrint(cmd)
    try:
        rc = os.system(cmd)
    except Exception:
        log.errorPrint("Not able to grant the permission."
                       "Please contact your stream manager.")


def remove_user(admin, adminpass, member, delay=300):
    exe = 'member_manager'
    exe_path = '/'.join((os.path.dirname(os.path.abspath(sys.argv[0])), exe))
    if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
        cmd = "%s --delay %s remove --admin %s --adminpasswd %s %s"\
              % (exe_path, delay, admin, adminpass, member)
        subprocess.Popen(
            shlex.split(cmd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)


class CheckItem(object):
    def __init__(self, item, log):
        self._item = item
        self._log = log
        self._state = None

    @property
    def item(self):
        return self._item

    @property
    def log(self):
        return self._log

    @property
    def state(self):
        return self._state

    def set_log(self, ref):
        self._log = ref

    def set_state(self, state):
        # OK|FAIL|SKIP
        self._state = state


class PullRequestManager(object):
    """
    Arg:
      user: PR submitter
      base_url: generally, https://eos2git.cec.lab.emc.com/api/v3
      org: github organization (File Domain: unity-file)
      team_id: may need to use get_teams() to check the target team id
      dev_user: the one to be added into the team
    Reference:
      https://pygithub.readthedocs.io/en/latest/
    """

    def __init__(self, pr_url, admin_user, admin_passwd, base_url, dev_user,
                 sanity = None, build_debug=None, build_retail=None, build_cp=None):
        # parse pull request url
        urlparse_result = urlparse(pr_url)
        self._pr_url = pr_url
        self._pr_scheme = urlparse_result.scheme
        self._pr_netloc = urlparse_result.netloc
        parse_pattern = re.compile(r'^/([^/]+)/([^/]+)/pull/(\d+)$')
        if_match = parse_pattern.match(urlparse_result.path)
        if if_match is None:
            die('Illegal pul-request: %r' % pr_url)
        self._fork = if_match.group(1)
        log.debugPrint('PR fork: %s' % self._fork)
        self._repo = if_match.group(2)
        log.debugPrint('PR repo: %s' % self._repo)
        self._pr_number = int(if_match.group(3))
        log.debugPrint('PR number: %s' % self._pr_number)
        self._sanity = CheckItem('sanity', sanity)
        self._DEBUG_build = CheckItem('DEBUG_build', build_debug)
        self._RETAIL_build = CheckItem('RETAIL_build', build_retail)
        self._CP_build = CheckItem('CP_build', build_cp)
        self._comment = ['[PR Manager] @ %s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())]
        self.changed_modules = None
        self._statuses_map = {}
        try:
            self.g = github.Github(login_or_token=admin_user,
                                   password=admin_passwd,
                                   base_url=base_url)
            self._dev_user = self.g.get_user(login=dev_user)
            log.debugPrint("Get the dev info %s" % self._dev_user)
            self._pr = self.g \
                .get_repo('{fork}/{repo}'.format(fork=self._fork, repo=self._repo)) \
                .get_pull(self._pr_number)
            changed_modules_list = []
            for changed_file in self._pr.get_files():
                filename = changed_file.filename
                log.debugPrint("changed file: %s" % filename)
                if '/' in filename:
                    changed_modules_list.append(filename.split('/')[0])
            self._changed_modules = set(changed_modules_list)
            log.debugPrint("Changed modules are %s" % self._changed_modules)

        except github.BadCredentialsException:
            die("Bad credentials for %s" % admin_user)
        except github.UnknownObjectException:
            die("Unknown object %r" % dev_user)
        except requests.exceptions.SSLError:
            die("SSL exception. Please set REQUESTS_CA_BUNDLE.\n\
    e.g. 'export REQUESTS_CA_BUNDLE=/c4site/SOBO/Public/zhengh3/EMC_CA_Root.pem'")
        except Exception as e:
            log.errorPrint("Unknown exception %r when fetching info of team and user:" % type(e))
            die(traceback.format_exc())

    def check_pr_branch_open(self):
        '''
        Check PR is open;
        Check target branch is open;
        TODO: check AR is open
        :return:
        '''
        assert self._pr, "Something wrong with PR handler."
        if self._pr.state != 'open':
            die("PR %d is not open." % self._pr_number)
        else:
            log.infoPrint("OK. PR %d is open." % self._pr_number)
        base_branch = self._pr.base.ref
        log.debugPrint("Base branch: %s" % base_branch)
        base_branch_state = get_branch_state(base_branch)
        if base_branch_state == 'open':
            log.infoPrint("OK. %s is open for promotion." % base_branch)
        elif base_branch_state == 'close':
            die("%s is blocked for promotion." % base_branch)
        elif base_branch_state == 'not_support':
            die("%s is not supported for self-authentication. "
                "Please contact its branch manager." % base_branch)
        else:
            log.warnPrint("%s is %r? Anyway let's go ahead."
                          % (base_branch, base_branch_state))
            self._comment.append("- **[WARN]** %s branch state: %s" % (base_branch, base_branch_state))

    def check_dev_consistency(self):
        '''
        Check the submitter is consonant with PR owner
        :return: NULL
        '''
        assert self._pr, "Something wrong with PR handler."
        if self._pr.user != self._dev_user:
            die("PR submitter(%s) doesn't match %s." %
                (self._pr.user.login, self._dev_user.login))
        log.infoPrint("OK. PR submitter(%s) is consonant with %s." %
                      (self._pr.user.login, self._dev_user.login))

    def check_commitcombinedstatus(self):
        assert self._pr, "Something wrong with PR handler."
        log.infoPrint(self._pr.title)
        commit_sha = self._pr.head.sha
        repo = self.g.get_repo('{fork}/{repo}'.format(fork=self._fork, repo=self._repo))
        commit = repo.get_commit(commit_sha)
        if self._changed_modules and \
                'safe' not in self._changed_modules and \
                'sade' not in self._changed_modules:
            log.debugPrint('Updated cbfs_test status to success as no safe/sade code changed.')
            self.update_commitcombinedstatus('cbfs_test', 'success')
        self._statuses_map = {}
        status_bad = []
        whitelist_context = ['Collaborator']
        for st in commit.get_statuses():
            if st.context not in self._statuses_map:
                self._statuses_map[st.context] = st.state
                log.debugPrint("%s is %s" % (st.context, st.state))
                if st.context not in whitelist_context and st.state != 'success':
                    status_bad.append(st.context)
        if status_bad:
            die("Check item %s %s not success."
                % (', '.join(("%r"%s for s in status_bad)), "are" if len(status_bad) > 1 else "is"))
        else:
            log.infoPrint("Checks in PR are good. Move ahead for more test/build checks.")

    def _check_additional_build(self):
        log.infoPrint('''We are going to check additional builds which are not mandatory.''')
        log.infoPrint('''Leave it blank if you don't have such a build.''')
        if self._DEBUG_build.log == '':
            self._DEBUG_build.set_log(click.prompt('Do you have a DEBUG build log',
                                                   default="", show_default=False))
            log.debugPrint('DEBUG build log: %s' % self._DEBUG_build.log)
        if self._RETAIL_build.log == '':
            self._RETAIL_build.set_log(click.prompt('Do you have a RETAIL build log',
                                              default="", show_default=False))
            log.debugPrint('RETAIL build log: %s' % self._RETAIL_build.log)
        if self._DEBUG_build.log.strip():
            result = check_build('debug', self._DEBUG_build.log)
            if not result:
                die("DEBUG build not pass.")
            else:
                self._DEBUG_build.set_state('OK')
                log.infoPrint("OK. DEBUG build check complete.")
        if self._RETAIL_build.log.strip():
            result = check_build('retail', self._RETAIL_build.log)
            if not result:
                die("RETAIL build not pass.")
            else:
                self._RETAIL_build.set_state('OK')
                log.infoPrint("OK. RETAIL build check complete.")
        if self._CP_build.log:
            result = check_build('cp', self._CP_build.log)
            if not result:
                die("CP build not pass.")
            else:
                self._CP_build.set_state('OK')
                log.infoPrint("OK. CP build check complete.")

    def _check_sanity(self):
        if self._sanity.log == '':
            self._sanity.set_log(click.prompt('Please provide MLU Sanity log'))
        if self._sanity.log == "NO NEED!":
            log.infoPrint("OK. Skip Mlu Sanity check.")
            self._sanity.set_state('SKIP')
            self._comment.append("- **[WARN]** Skip Mlu Sanity check.")
            return
        if not check_mlu_santiy(self._sanity.log):
            die("Mlu Sanity not pass.")
        else:
            self._sanity.set_state('OK')
            log.infoPrint("OK. Mlu Sanity check complete.")
            return

    def additional_checks(self):
        '''
        Check Mlu Sanity
        Check additional_build
        :return:
        '''
        self._check_sanity()
        # check build except safe sade
        self._check_additional_build()
        assert self._pr, "Something wrong with PR handler."
        for module in self._changed_modules:
            if module == 'safe' or module == 'sade':
                if 'cbfs_test' not in self._statuses_map:
                    die("cbfs_test check is mandatory when safe/sade code changed.")
                log.debugPrint("safe/sade module changed but should be verified in PR.")
                continue
            elif module == 'cp':
                log.debugPrint("%s module changed." % module)
                if self._CP_build.state == 'OK' or \
                   self._DEBUG_build.state == 'OK' or \
                   self._RETAIL_build.state == 'OK' or \
                   self._sanity.state == 'OK':
                    log.debugPrint("%s build should be OK" % module)
                    continue
                self._CP_build.set_log(
                    click.prompt("CP module changed. Please provide the CP build log"))
                result = check_build('cp', self._CP_build.log)
                if not result:
                    die("CP build not pass.")
                else:
                    self._CP_build.set_state('OK')
                    log.infoPrint("OK. CP build check complete.")
            elif module == 'nxgui':
                nxgui_test_log_path = 'nxgui/NxGenWorkspace/results/cemgui/selenium.txt'
                nxgui_test_cmd1 = 'nxgui/NxGenWorkspace/cemgui-app/build.sh run-automation-tests'
                #nxgui_test_cmd2 = 'nxgui/NxGenWorkspace/cemgui-app/build.sh run-automation-tests-vvnx'
                log.infoPrint("%s module changed." % module)
                log.infoPrint(
                #    "Please 'build_all nxgui' and run\n1. {}\n2. {}\nSave and provide the log {!r} separately.".format(
                #        nxgui_test_cmd1, nxgui_test_cmd2, nxgui_test_log_path))
                    "Please 'build_all nxgui' and run\n{}\n. Save and provide the log {!r}.".format(
                        nxgui_test_cmd1, nxgui_test_log_path))
                nxgui_log1 = click.prompt("Please provide the 1st log")
                #nxgui_log2 = click.prompt("Please provide the 2nd log")
                #try:
                #    if os.path.getsize(nxgui_log1) == os.path.getsize(nxgui_log2):
                #        die("Same log file? Please save and provide two different nxgui logs.")
                #except FileNotFoundError as e:
                #    die(e)
                if not check_nxgui(nxgui_log1):
                    die("nxgui test failed.")
                #if not check_nxgui(nxgui_log2):
                #    die("nxgui test failed.")
                setattr(self, 'nxgui_1', CheckItem('nxgui', nxgui_log1))
                getattr(self, 'nxgui_1').set_state('OK')
                self._comment.append(
                    "- nxgui: %s\n\t%s" % (getattr(self, 'nxgui_1').state, getattr(self, 'nxgui_1').log))
                #setattr(self, 'nxgui_2', CheckItem('nxgui_vvnx', nxgui_log2))
                #getattr(self, 'nxgui_2').set_state('OK')
                #self._comment.append(
                #    "- nxgui vvnx: %s\n\t%s" % (getattr(self, 'nxgui_2').state, getattr(self, 'nxgui_2').log))
            else:
                log.debugPrint("%s module changed" % module)
                if self._DEBUG_build.state == 'OK' or \
                   self._RETAIL_build.state == 'OK' or \
                   self._sanity.state == 'OK':
                    log.debugPrint("%s build should be OK" % module)
                else:
                    log.warnPrint("{m} module is changed. "
                                  "You'd better build {m}/Full_Image to verify your changes."\
                                  .format(m=module))
                    module_build_log = click.prompt('Do you have a {m} build log'.format(m=module.upper()),
                                                    default="", show_default=False)
                    if module_build_log != '':
                        result = check_build(module, module_build_log)
                        if not result:
                            die("{m} build not pass.".format(m=module.upper()))
                        else:
                            setattr(self, '_{m}_build'.format(m=module.upper()),
                                    CheckItem('{m}_build'.format(m=module.upper()), module_build_log))
                            getattr(self, '_{m}_build'.format(m=module.upper())).set_state('OK')
                            log.infoPrint("OK. {m} build check complete.".format(m=module.upper()))
                            self._comment.append("- [Additional] {m} BUILD: %s\n\t%s".format(m=module.upper()) % \
                                                 (getattr(self, '_{m}_build'.format(m=module.upper())).state,
                                                 getattr(self, '_{m}_build'.format(m=module.upper())).log))
                    else:
                        self._comment.append("- **[WARN]** %s module is changed w/o build log provided." % module)

    def create_issue_comment(self):
        assert self._pr, "Something wrong with PR handler."
        if self._sanity.state is not None:
            self._comment.append("- Mlu Sanity: %s\n\t%s" % (self._sanity.state, self._sanity.log))
        if self._DEBUG_build.state is not None:
            self._comment.append("- DEBUG BUILD: %s\n\t%s" % (self._DEBUG_build.state, self._DEBUG_build.log))
        if self._RETAIL_build.state is not None:
            self._comment.append("- RETAIL BUILD: %s\n\t%s" % (self._RETAIL_build.state, self._RETAIL_build.log))
        if self._CP_build.state is not None:
            self._comment.append("- CP BUILD: %s\n\t%s" % (self._CP_build.state, self._CP_build.log))
        self._pr.create_issue_comment('\n'.join(self._comment))

    def cleanup_merge_team(self):
        team_id = 1649
        try:
            g_org = self.g.get_organization(self._fork)
            g_team = g_org.get_team(team_id)
            log.debugPrint("[cleanup_merge_team] Get the target team info %s" % g_team)
            for u in g_team.get_members():
                g_team.remove_from_members(u)
                log.debugPrint("Removed %s from merge team." % u)
        except github.UnknownObjectException as e:
            log.errorPrint("Exception %s when cleanup_merge_team" % e)

    def add_to_team(self):
        """Add the user into merge team so that he/she will be able to merge"""
        team_id = 1649
        try:
            g_org = self.g.get_organization(self._fork)
            g_team = g_org.get_team(team_id)
            log.debugPrint("Get the target team info %s" % g_team)
            if g_team.has_in_members(self._dev_user):
                log.infoPrint("OK. User %r is already in the merge team." % self._dev_user.name)
            else:
                g_team.add_membership(self._dev_user)
                log.infoPrint("OK. Added user %r into the merge team." % self._dev_user.name)
            log.infoPrint("%r is able to merge the PullRequest." % self._dev_user.login)
        except github.UnknownObjectException:
            log.errorPrint("Unable to grant the merge permission.")
            die("Illegal team id %r" % team_id)

    def remove_from_team(self):
        """remove the user from merge team"""
        team_id = 1649
        try:
            g_org = self.g.get_organization(self._fork)
            g_team = g_org.get_team(team_id)
            log.debugPrint("Get the target team info %s" % g_team)
            if g_team.has_in_members(self._dev_user):
                g_team.remove_from_members(self._dev_user)
                log.infoPrint("OK. Removed user %r from the merge team." % self._dev_user.name)
            else:
                log.infoPrint("User %r is not in the merge team." % self._dev_user.name)
        except github.UnknownObjectException:
            log.errorPrint("Unable to grant the merge permission.")
            die("Illegal team id %r" % team_id)

    def update_commitcombinedstatus(self, context, state):
        # state: "pending", "success", "error", "failure"
        assert self._pr, "Something wrong with PR handler."
        commit_sha = self._pr.head.sha
        repo = self.g.get_repo('{fork}/{repo}'.format(fork=self._fork, repo=self._repo))
        commit = repo.get_commit(commit_sha)
        status_not_set = True
        for st in commit.get_statuses():
            if st.context == context:
                status_not_set = False
                if st.state == state:
                    log.debugPrint("Commit context %r is already %r" % (context, state))
                else:
                    log.debugPrint("Ready to set %r as %r" % (context, state))
                    try:
                        commit.create_status(state, context=context)
                    except Exception as e:
                        log.warnPrint('Got %s when trying to update %s state to %s.'%
                                    (type(e), context, state))
        if status_not_set:
            log.debugPrint("Commit context %r is not set. Gonna to create one" % context)
            try:
                commit.create_status(state, context=context)
            except Exception as e:
                log.warnPrint('Got %s when trying to update %s state to %s.' %
                              (type(e), context, state))

    def mail_admin(self):
        msg_content = '\n'.join([self._pr.base.ref, self._pr.title, self._pr_url, ""] + self._comment)
        msg = MIMEText(msg_content)
        msg['Subject'] = '[PR] Granted %s merge permission' % self._dev_user.login
        msg['From'] = 'PR_Manager@localhost'
#       msg['to'] = 'Haowen.zheng@emc.com,Charlie.Chen3@emc.com'
        msg['to'] = 'Charlie.Chen1@dell.com'
        s = smtplib.SMTP('localhost')
        try:
            s.send_message(msg)
        except Exception as e:
            log.errorPrint('[ERROR] %s' % e)
        finally:
            s.quit()

    def merge(self):
        mergeable_state = self._pr.mergeable_state
        mergeable = self._pr.mergeable
        log.infoPrint('%s/%s PR #%s state is %s (mergeable: %s for %s)' \
                       % (self._fork, self._repo, self._pr_number, mergeable_state, mergeable, self._dev_user.login))
        if mergeable and mergeable_state != 'blocked':
            # PullRequestMergeStatus(sha="2cc7f79be3cc3b590db2424055b2160b08346213", merged=True)
            prms = self._pr.merge()
            if prms.merged:
                log.infoPrint('PR #%s is merged by %s.' % (self._pr_number, self._dev_user.login))
            else:
                die('''Failed to auto-merge PR #%s as %s. Please merge manually.''' % (self._pr_number, self._dev_user.login))
        else:
            die('''%s is not able to merge the PR. Some check may block the merging.''' % self._dev_user.login)


@click.command()
@click.option('--debug/--no-debug', default=False,
              help='Print DEBUG log on screen.')
@click.option('--emc_ca_root', type=click.Path(exists=True),
#             default='/c4site/SOBO/Public/zhengh3/EMC_CA_Root.pem',
              default='/net/sles15-chenq9-dev-00/c4_working/chenq9/EMC_CA_Root.pem',
              help='Specify the EMC_CA_Root.pem.')
@click.option('--corpid', default='',
              help='Should match PR submitter')
@click.option('--sanity', default='',
              help="Mlu Sanity log. Use 'NO NEED!' to skip the check.")
@click.option('--debugbuild', default='',
              help='DEBUG build log.')
@click.option('--retailbuild', default='',
              help='RETAIL build log.')
@click.option('--cpbuild', default='',
              help='CP build log.')
@click.option('--automerge', is_flag=True, default=False,
              help='Auto merge the PR when all checks passed')
@click.argument('url', 'Pull Request URL', required=True)
def main(debug, emc_ca_root, corpid, sanity, debugbuild, retailbuild, cpbuild, automerge, url):
    if debug:
        global log
        log = LogHelper(screenlevel=logging.DEBUG)
    os.environ["REQUESTS_CA_BUNDLE"] = emc_ca_root
    (admin, adminpasswd) = get_admin()
    if not corpid:
        log.debugPrint("CORP ID is not specified.")
        corpid = get_local_user()
        log.debugPrint("Get CORP ID: %s" % corpid)
    # blacklist
#    blacklist_file = '/c4site/SOBO/Public/zhengh3/SM_bl'
    blacklist_file = '/net/sles15-chenq9-dev-00/c4_working/chenq9/SM_bl'
    if os.path.exists(blacklist_file):
        with open(blacklist_file, 'r') as fh:
            if corpid in json.load(fh):
                die("Permission denied. Please contact branch manager for the promotion.")
    else:
        log.debugPrint("%s not exist." % blacklist_file)
    base_url = 'https://eos2git.cec.lab.emc.com/api/v3'
    prm = PullRequestManager(url, admin, adminpasswd, base_url, corpid,
                             sanity=sanity,
                             build_debug=debugbuild,
                             build_retail=retailbuild,
                             build_cp=cpbuild)
    prm.cleanup_merge_team()
    prm.check_dev_consistency()
    prm.check_pr_branch_open()
    prm.check_commitcombinedstatus()
    prm.additional_checks()
    prm.create_issue_comment()
    log.infoPrint("Ready to grant %s merge permission." % corpid)
    prm.add_to_team()
    prm.update_commitcombinedstatus('Collaborator', 'success')
    prm.mail_admin()
    if automerge:
        dev_passwd = click.prompt('Password for %s' % corpid, hide_input=True)
        prm_dev = PullRequestManager(url, corpid, dev_passwd, base_url, corpid)
        prm_dev.merge()
        prm.remove_from_team()
    else:
        yn = click.prompt('Merge Now? [y|n]')
        if yn == 'y' or yn == 'yes':
            dev_passwd = ''
            try:
                _cmd="""git credential fill"""
                _str = b'url=https://eos2git.cec.lab.emc.com'
                cp = subprocess.run(shlex.split(_cmd), input=_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if_user_match = re.search(b'username=%s'%corpid.encode(), cp.stdout)
                if if_user_match is not None:
                    ifmatch = re.search(b'.*password=(.+)', cp.stdout)
                    if ifmatch is not None:
                        dev_passwd = ifmatch.group(1).decode()
            except Exception as e:
                log.debugPrint("[git credential] Exception: %s" % e)
            if dev_passwd == '':
                dev_passwd = click.prompt('Password for %s' % corpid, hide_input=True)
            prm_dev = PullRequestManager(url, corpid, dev_passwd, base_url, corpid)
            prm_dev.merge()
            prm.remove_from_team()
        else:
            log.infoPrint("Done. You should be able to merge the PR now.")


if __name__ == '__main__':
    main()
