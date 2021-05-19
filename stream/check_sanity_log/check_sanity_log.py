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
    def _proceed_local_file(_log):
        # printFinalOutput: MLU Sanity:Test Status ====> PASSED      End Time: 2018/06/26: 04:22:29
        final_output_pattern = re.compile(
            r'''MLU Sanity:Test Status\s*====>\s*(\S+)\s*End Time: (.+)'''
        )
        html_pattern = re.compile(r'''<!DOCTYPE html>''')
        test_result = ''
        test_time = ''
        with open(_log, 'rt') as fp:
            find_result = False
            for line in iter(fp.readline, ''):
                if html_pattern.search(line) is not None:
                    return 'is_html', ''
                re_search = final_output_pattern.search(line)
                if re_search is not None:
                    test_result = re_search.group(1)
                    test_time = re_search.group(2)
                    debug_message('%r @ %r' % (test_result, test_time))
                    find_result = True
                    return test_result, test_time
            if not find_result:
                die('No test result in the log.', 2)

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
            file = os.path.join(temp_path, 'CHUNK_for_check_sanity_log')
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
    # 1. local file
    if os.path.exists(log):
        debug_message("Parse local file.")
        if os.path.isfile(log):
            return _proceed_local_file(log)
        else:
            die("%s is not a file." % log)
    # 2. link
    elif log.startswith('http'):
        debug_message("Try to parse as raw content.")
        try:
            file = _downloadchunks(log)
            sanity_result = _proceed_local_file(file)
            if sanity_result[0] == 'is_html':
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
                    sanity_result = _proceed_local_file(file)
                    if sanity_result[0] == 'is_html':
                        die("No test result in the log.", 3)
                    else:
                        return sanity_result
                else:
                    die('Unable to parse %s' % log)
            else:
                return sanity_result
        except urllib.error.HTTPError:
            die("HTTPError", 3)
    else:
        die('Unable to parse %s' % log)


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
        0 -- Sanity pass and delta date < expired days
        1 -- Sanity pass but delta date > expired days
        2 -- Sanity fail
        3 -- URL 404
    """
    if debug:
        global _debug_on
        _debug_on = True
    (result, time) = proceed_log(log)
    if result != 'PASSED':
        die("Mlu Sanity is not 'PASSED'", 2)
    if (datetime.now() - datetime.strptime(time, '%Y/%m/%d: %H:%M:%S')).days > expired:
        die("Mlu Sanity expired (> %d days)" % expired, 1)
    print("\033[92m[INFO]\033[0m %r @ %r" % (result, time))


if __name__ == '__main__':
    main()
