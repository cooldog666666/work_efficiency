#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time
import requests
from util.colorPrint import ColorPrint
import logging
import time
import github
import base64
import os
import click
import sys
import traceback
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

    def __init__(self, logfilename='/tmp/%s.log' % os.path.basename(__file__).rsplit('.')[0], name='default', screenlevel=logging.INFO, filelevel=logging.DEBUG):
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
        formatter_str = '*%(asctime)s|%(levelno)s|%(process)d - %(message)s'
        self.fh.setFormatter(logging.Formatter(formatter_str))
        # stream handler
        self.shout = logging.StreamHandler(stream=sys.stdout)
        self.shout.setLevel(self.screenlevel)
        self.shout.setFormatter(logging.Formatter('%(message)s'))
        self.sherr = logging.StreamHandler()
        self.sherr.setLevel(self.screenlevel)
        self.sherr.setFormatter(logging.Formatter('%(message)s'))

    def debugPrint(self, msg):
        # message for stream handler
        smsg = '[DEBUG] %s' % (msg)
        self.logger.addHandler(self.fh)
        self.logger.debug(msg)
        self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.shout)
        self.logger.debug(smsg)
        self.logger.removeHandler(self.shout)

    def errorPrint(self, msg):
        # message for stream handler
        smsg = '%s %s' % (ColorPrint('[ERROR]', ColorPrint.FAIL), msg)
        self.logger.addHandler(self.fh)
        self.logger.error(msg)
        self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.sherr)
        self.logger.error(smsg)
        self.logger.removeHandler(self.sherr)

    def warnPrint(self, msg):
        # message for stream handler
        smsg = '%s %s' % (ColorPrint('[WARN]', ColorPrint.WARNING), msg)
        self.logger.addHandler(self.fh)
        self.logger.warning(msg)
        self.logger.removeHandler(self.fh)
        self.logger.addHandler(self.shout)
        self.logger.warning(smsg)
        self.logger.removeHandler(self.shout)

    def infoPrint(self, msg, style=OKGREEN):
        # message for stream handler
        smsg = '%s %s' % (ColorPrint('[INFO]', style), msg) if style else '[INFO] %s' % msg
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


class TeamManager(object):
    """
    Arg:
    admin_user: should be able to add people into a team
    base_url: generally, https://eos2git.cec.lab.emc.com/api/v3
    org: github organization (File Domain: unity-file)
    team_id: may need to use get_teams() to check the target team id
    dev_user: the one to be added into the team
    """
    def __init__(self, admin_user, admin_passwd, base_url,
                       org, team_name_or_id, dev_user=None):
        # github authentication with admin user
        try:
            self.g = github.Github(login_or_token=admin_user,
                               password=admin_passwd,
                               base_url=base_url)
            self._admin_user = self.g.get_user(login=admin_user)
            log.debugPrint("Get the admin info %s" % self._admin_user)
        except github.BadCredentialsException:
            die("Bad credentials for %s" % admin_user)
        except requests.exceptions.SSLError:
            die("SSL exception. Please set REQUESTS_CA_BUNDLE. "
                "e.g. 'export REQUESTS_CA_BUNDLE=~/EMC_CA_Root.pem'")
        except github.UnknownObjectException:
            die("Unknown admin %r" % admin_user)

        self._dev_user = None
        if dev_user:
            try:
                self._dev_user = self.g.get_user(login=dev_user)
                log.debugPrint("Get the dev info %s" % self._dev_user)
            except github.UnknownObjectException:
                die("Unknown object %r" % dev_user)
        try:
            self._org = self.g.get_organization(org)
            log.debugPrint("Get the org info %s" % self._org)
        except github.UnknownObjectException:
            die("Unknown object %r" % org)
        if isinstance(team_name_or_id, str):
            for team in self._org.get_teams():
                log.debugPrint("Get a team info %s" % team)
                if team.name == team_name_or_id:
                    self._team = team
                    log.debugPrint("Get the target team info %s" % self._team)
                    break
            if not self._team:
                die("Unknown team %r" % team_name_or_id)
        elif isinstance(team_name_or_id, int):
            try:
                self._team = self._org.get_team(team_name_or_id)
                log.debugPrint("Get the target team info %s" % self._team)
            except github.UnknownObjectException:
                die("Unknown object %r" % team_name_or_id)
        else:
            die("Illegal team name/id %r" % team_name_or_id)


    def add_user(self):
        assert self._dev_user, "Who to be added?"
        if self._team.has_in_members(self._dev_user):
            log.infoPrint("OK. User %r is already in the team." % self._dev_user.name)
        else:
            self._team.add_membership(self._dev_user)
            log.infoPrint("OK. Added user %r into the team." % self._dev_user.name)

    def remove_user(self):
        assert self._dev_user, "Who to be removed?"
        if self._team.has_in_members(self._dev_user):
            self._team.remove_from_members(self._dev_user)
            log.infoPrint("OK. Removed user %r from the team." % self._dev_user.name)
        else:
            log.infoPrint("OK. User %r is not in the team." % self._dev_user.name)

    def cleanup_team(self, delay=0, interval=0, include_admin=False):
        def _once():
            tobe_removed = []
            for u in self._team.get_members():
                if u == self._admin_user and not include_admin:
                    continue
                tobe_removed.append(u)
                log.infoPrint("[CLEAN] Ready to remove %r from the team after %d seconds" % (u.name, delay))
            if not tobe_removed:
                log.debugPrint("No member needs to be removed.")
            time.sleep(delay)
            for u in tobe_removed:
                if self._team.has_in_members(u):
                    self._team.remove_from_members(u)
                    log.infoPrint("[CLEAN] Removed user %r from the team." % u.name)
        if interval > 0:
            log.debugPrint("Loop to clean team with interval %d ..." % interval)
            while True:
                _once()
                time.sleep(interval)
        else:
            _once()


@click.group()
@click.option('--debug/--no-debug', default=False,
              help='Print DEBUG log on screen.')
@click.option('--emc_ca_root', type=click.Path(exists=True),
#             default='/c4site/SOBO/Public/zhengh3/EMC_CA_Root.pem',
              default='/net/sles15-chenq9-dev-00/c4_working/chenq9/EMC_CA_Root.pem',
              help='Specify the EMC_CA_Root.pem.')
@click.option('--delay', type=click.INT, default=0,
              help='delay a task for X seconds')
def main(debug, emc_ca_root, delay):
    if debug:
        global log
        log = LogHelper(screenlevel=logging.DEBUG)
    os.environ["REQUESTS_CA_BUNDLE"] = emc_ca_root
    if delay:
        time.sleep(delay)


@main.command()
@click.option('--admin', help='who should be able to add people into a team')
@click.option('--adminpasswd', help="admin's password")
@click.option('--baseurl', default='https://eos2git.cec.lab.emc.com/api/v3',
              help='base url for github authentication')
@click.option('--org', default='unity-file',
              help='organization name')
@click.option('--team', default='merge',
              help='which team should the user be added')
@click.option('--teamid', type=click.INT, default=1649,
              help='similar with team name')
@click.option('--removelater', type=click.INT, default=0,
              help='remove the user later')
@click.argument('corpid', 'Who to be added', required=True)
def add(admin, adminpasswd, baseurl, org, team, teamid, removelater, corpid):
    """Add one into a team"""
    if not admin or not adminpasswd:
        try:
            admin = os.environ['CORPUSER']
        except KeyError:
            admin = click.prompt("Specify the admin")
        try:
            adminpasswd = base64.b64decode(os.environ['CORPPASSWD']).decode()
        except KeyError:
            adminpasswd = click.prompt("admin password", hide_input=True)
    tm = None
    if teamid:
        tm = TeamManager(admin, adminpasswd, baseurl, org, teamid, corpid)
        if removelater != 0:
            log.debugPrint("Will remove %s after %d seconds." % (corpid, removelater))
            remove_cmd = '%s --delay %d remove %s'\
                         % (os.path.abspath(sys.argv[0]), removelater, corpid)
            log.debugPrint("[SUB] %s" % remove_cmd)
            subprocess.Popen(remove_cmd, shell=True)
    elif team:
        tm = TeamManager(admin, adminpasswd, baseurl, org, team, corpid)
    else:
        die("Please specify a team")
    if tm:
        tm.add_user()


@main.command()
@click.option('--admin', help='who should be able to add people into a team')
@click.option('--adminpasswd', help="admin's password")
@click.option('--baseurl', default='https://eos2git.cec.lab.emc.com/api/v3',
              help='base url for github authentication')
@click.option('--org', default='unity-file',
              help='organization name')
@click.option('--team', default='merge',
              help='which team should the user be added')
@click.option('--teamid', type=click.INT, default=1649,
              help='similar with team name')
@click.argument('corpid', 'Who to be added', required=True)
def remove(admin, adminpasswd, baseurl, org, team, teamid, corpid):
    """Remove one from a team"""
    if not admin or not adminpasswd:
        try:
            admin = os.environ['CORPUSER']
        except KeyError:
            admin = click.prompt("Specify the admin")
        try:
            adminpasswd = base64.b64decode(os.environ['CORPPASSWD']).decode()
        except KeyError:
            adminpasswd = click.prompt("admin password", hide_input=True)
    tm = None
    if teamid:
        tm = TeamManager(admin, adminpasswd, baseurl, org, teamid, corpid)
    elif team:
        tm = TeamManager(admin, adminpasswd, baseurl, org, team, corpid)
    else:
        die("Please specify a team")
    if tm:
        tm.remove_user()


@main.command()
@click.option('--admin', help='who should be able to add people into a team')
@click.option('--adminpasswd', help="admin's password")
@click.option('--baseurl', default='https://eos2git.cec.lab.emc.com/api/v3',
              help='base url for github authentication')
@click.option('--org', default='unity-file',
              help='organization name')
@click.option('--team', default='merge',
              help='which team should the user be added')
@click.option('--teamid', type=click.INT, default=1649,
              help='similar with team name')
@click.option('--delay', type=click.INT, default=1740,
              help='Remove all members after a period')
@click.option('--interval', type=click.INT, default=0,
              help='Loop to remove all members with an interval')
@click.option('--includeadmin', is_flag=True, default=False,
              help='Remove all members include admin')
def clean(admin, adminpasswd, baseurl, org, team, teamid, delay, interval, includeadmin):
    """Clean up a team"""
    if not admin or not adminpasswd:
        try:
            admin = os.environ['CORPUSER']
        except KeyError:
            admin = click.prompt("Specify the admin")
        try:
            adminpasswd = base64.b64decode(os.environ['CORPPASSWD']).decode()
        except KeyError:
            adminpasswd = click.prompt("admin password", hide_input=True)
    tm = None
    if teamid:
        tm = TeamManager(admin, adminpasswd, baseurl, org, teamid)
    elif team:
        tm = TeamManager(admin, adminpasswd, baseurl, org, team)
    else:
        die("Please specify a team")
    if tm:
        tm.cleanup_team(delay, interval, includeadmin)


if __name__ == '__main__':
    main()

