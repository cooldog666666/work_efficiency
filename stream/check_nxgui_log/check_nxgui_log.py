#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import os.path
import sys
import re
import urllib.error
import urllib.request
from urllib.parse import urlparse
from datetime import datetime

_debug_on = False


def ePrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def debug_message(message):
    if _debug_on:
        print("[DEBUG]", message)


def die(message, exit_code=255):
    """Terminate, displaying an error message."""
    ePrint("\033[91m[ERROR]\033[0m", message)
    sys.exit(exit_code)


def proceed_log(log):
    '''
    :param log: nxgui testing log
    :return: result, time
    '''
    def _proceed_local_file(_log):
        # [selenium:testng] CemGuiAutomation.view.wizard.createlunwizard.createthinclonewizard.CreateThinCloneAutomationTest - Failed
        # [selenium:testng] CemGuiAutomation.view.wizard.addlunwizard.AddLunWizardWithNewIoLimitTest - Failed
        failed_pattern = re.compile(r'''.*(CemGuiAutomation.*) - Failed$''')
        failed_case_list = []
        time_pattern = re.compile(r'''.*(20[12]\d-\d\d-\d\d [0-2]\d:\d\d:\d\d):\d\d\d.*''')
        html_pattern = re.compile(r'''<!DOCTYPE html>''')
        _time = ''
        with open(_log, 'rt') as fp:
            for line in iter(fp.readline, ''):
                if html_pattern.search(line) is not None:
                    return 'is_html', ''
                re_search = failed_pattern.search(line)
                if re_search is not None:
                    failed_case_list.append(re_search.group(1))
                    print('  %s : Failed' % re_search.group(1))
                if not _time:
                    re_search = time_pattern.search(line)
                    if re_search is not None:
                        _time = re_search.group(1)
        if failed_case_list:
            return 'FAILED', _time
        else:
            return 'PASSED', _time

    def _downloadchunks(url):
        """Helper to download large files
            the only arg is a url
           this file will go to a temp directory
           the file will also be downloaded
           in chunks and print out how much remains
        """

        # move the file to a more uniq path
        os.umask(0o002)
        temp_path = "/tmp/"
        try:
            file = os.path.join(temp_path, 'CHUNK_for_check_nxgui_log')

            req = urllib.request.urlopen(url)
            CHUNK = 256 * 10240
            with open(file, 'wb') as fp:
                while True:
                    chunk = req.read(CHUNK)
                    if not chunk: break
                    fp.write(chunk)
            debug_message("Downloaded as %s" % file)
            return file
        except urllib.error.HTTPError:
            die("HTTP Error", 4)
        return ''
    build_result = ''
    build_time = ''
    # 1. local file
    if os.path.exists(log):
        debug_message("Parse local file.")
        if os.path.isfile(log):
            build_result, build_time = _proceed_local_file(log)
            if build_result == 'is_html':
                die("Fail to parse %s" % log, 2)
            else:
                return build_result, build_time
        else:
            die("%s is not a file." % log)
    # 2. link
    elif log.startswith('http'):
        debug_message("Try to parse as raw content.")
        try:
            file = _downloadchunks(log)
            build_result, build_time = _proceed_local_file(file)
            if build_result == 'is_html':
                debug_message("Try to parse as a Jenkins job.")
                job_pattern = re.compile('''(/.*job/[\w\d-]+/\d+).*''')
                urlparse_result = urlparse(log)
                debug_message(urlparse_result.path)
                re_match = job_pattern.match(urlparse_result.path)
                if re_match is not None:
                    jenkins_job_url = '{}://{}{}/consoleText'.format(
                        urlparse_result.scheme,
                        urlparse_result.netloc,
                        re_match.group(1))
                    debug_message(jenkins_job_url)
                    file = _downloadchunks(jenkins_job_url)
                    build_result, build_time = _proceed_local_file(file)
                    if build_result == 'is_html':
                        die("Build is not SUCCESSFUL.", 3)
                    else:
                        return build_result, build_time
                else:
                    die('Unable to parse %s' % log)
        except urllib.error.HTTPError:
            die("HTTPError", 3)
    else:
        debug_message('Unable to parse %s' % log)
    return build_result, build_time


@click.command()
@click.option('--debug/--no-debug', default=False,
              help='Print DEBUG log on screen.')
@click.option('--expired', type=click.INT, default=15,
              help='Log expired days')
@click.argument('log', required=True)
def main(debug, expired, log):
    """
    :param debug: debug message
    :param log: could be a local file, or a web raw content, or a Jenkins job
    :return:
        0 -- pass and delta date < expired days
        1 -- pass but delta date > expired days
        2 -- nxgui testing fail
        3 -- URL 404
    """
    if debug:
        global _debug_on
        _debug_on = True
    (result, time) = proceed_log(log)
    if result != 'PASSED':
        die("NXGUI test is not 'PASSED'", 2)
    if (datetime.now() - datetime.strptime(time, '%Y-%m-%d %H:%M:%S')).days > expired:
        die("NXGUI test log expired (> %d days)" % expired, 1)
    print("\033[92m[INFO]\033[0m %r" % result)


if __name__ == '__main__':
    main()
