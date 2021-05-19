#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import os.path
import sys
import re
import urllib.error
import urllib.request
from urllib.parse import urlparse

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


def proceed_log(module, log):
    def _proceed_local_file(_module, _log):
        html_pattern = re.compile(r'''<!DOCTYPE html>''')
        # Loading dependency information about the GNOSIS RETAIL configuration ...
        flavor_pattern = re.compile(r'Loading dependency information about the GNOSIS (.+) configuration ...')
        # 0-ini  1-need  2-fail 3-ok
        flavor_match = 0
        target_flavor = 'DEBUG'
        if _module.upper() == 'DEBUG' or _module.upper() == 'RETAIL':
            target_flavor = _module.upper()
            target_component = 'image'
            flavor_match = 1
        else:
            target_component = _module.lower()
        _build_result = ''
        with open(_log, 'rt') as fp:
            for line in fp:
                if html_pattern.search(line) is not None:
                    return 'is_html'
                if flavor_match == 0 or flavor_match == 1:
                    re_search = flavor_pattern.search(line)
                    if re_search is not None:
                        flavor = re_search.group(1)
                        if flavor_match == 1:
                            if flavor.upper() == target_flavor:
                                debug_message("Flavor %s match" % flavor.upper())
                                flavor_match = 3
                            else:
                                die("Build flavor %s doesn't match %s."
                                    % (flavor.upper(), target_flavor.upper()), 1)
                        if flavor_match == 0:
                            target_flavor = flavor
                if 'package:GNOSIS:%s:%s' % (target_flavor, target_component) in line:
                    debug_message(line.strip())
                    _build_result = 'OK'
                    break
            if flavor_match == 1:
                die("Build failed (Flavor not found in log)", 1)
            if _build_result != 'OK':
                die("No '%s build success' is found in log." % target_component)
        return _build_result

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
            file = os.path.join(temp_path, 'CHUNK_for_check_build_log')

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
    # 1. local file
    if os.path.exists(log):
        debug_message("Parse local file.")
        if os.path.isfile(log):
            build_result = _proceed_local_file(module, log)
            if build_result == 'is_html':
                die("Fail to parse %s" % log, 2)
            else:
                return build_result
        else:
            die("%s is not a file." % log)
    # 2. link
    elif log.startswith('http'):
        debug_message("Try to parse as raw content.")
        try:
            file = _downloadchunks(log)
            build_result = _proceed_local_file(module, file)
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
                    build_result = _proceed_local_file(module, file)
                    if build_result == 'is_html':
                        die("Build is not SUCCESSFUL.", 3)
                    else:
                        return build_result
                else:
                    die('Unable to parse %s' % log)
        except urllib.error.HTTPError:
            die("HTTPError", 3)
    else:
        debug_message('Unable to parse %s' % log)
    return build_result


@click.command()
@click.option('--debug/--no-debug', default=False,
              help='Print DEBUG log on screen.')
@click.option('--type', default='DEBUG',
              help='build module')
@click.argument('log', required=True)
def main(debug, type, log):
    """
    :param debug: debug message
    :param type: build module
    :param log: could be a local file, or a web raw content, or a Jenkins job
    :return:
        0 -- build ok
        1 -- flavor not match
        2 -- build fail
        3 -- URL 404
    """
    if debug:
        global _debug_on
        _debug_on = True
    result = proceed_log(type, log)
    if result != 'OK':
        die("%s BUILD_FAILURE" % type, 2)
    print("\033[92m[INFO]\033[0m %s build %s" % (type, result))


if __name__ == '__main__':
    main()
