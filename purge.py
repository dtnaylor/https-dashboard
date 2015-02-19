#!/usr/bin/env python

##
## Purges old crawl data (e.g., old screenshots)
##

import os
import sys
import argparse
import logging
import glob
import datetime

import pprint

from collections import defaultdict


def setup_logging():
    if args.quiet:
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    config = {
        'format' : "%(levelname) -10s %(asctime)s %(module)s:%(lineno) -7s %(message)s",
        'level' : level
    }
    logging.basicConfig(**config)





def purge_screenshots(profile_dir, num_to_keep):
    '''Remove screenshots for all crawls except the most recent num_to_keep.
       Does not remove thumbnails.'''

    # get the non-backup crawl directories
    crawl_dirs = glob.glob(profile_dir + '/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
    crawl_dirs = sorted(crawl_dirs, reverse=True)

    # remove screenshots from all but the newest num_to_keep
    for crawl_dir in crawl_dirs[num_to_keep:]:
        for screenshot in [img for img in\
            glob.glob('%s/*/site_screenshots/*.png' % crawl_dir)\
            if 'thumb' not in img]:                      # don't delete thumbnails

            try:
                logging.debug('Removing screenshot: %s' % screenshot)
                os.remove(screenshot)
            except:
                logging.exception('Error removing %s', screenshot)


def purge_hars(har_archive_dir, num_to_keep, frequency_to_keep):
    '''Keep the most recent num_to_keep HAR tarballs. For older tarballs, keep
       every nth, where n is frequency_to_keep'''
    
    # get a list of the HAR tarballs
    har_tarballs = glob.glob(har_archive_dir + '/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_*.tgz')
    har_tarballs = sorted(har_tarballs, reverse=True)

    # store in dict where key is datetime of tarballs date
    tarballs_by_date = defaultdict(list)
    for har_tarball in har_tarballs:
        date_string = os.path.split(har_tarball)[1].split('_')[0]
        date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
        tarballs_by_date[date].append(har_tarball)
        
    # if date is older than num_to_keep days, only keep frequency_to_keep
    dates = sorted(tarballs_by_date.keys(), reverse=True)
    epoch = datetime.datetime.utcfromtimestamp(0)
    for date in dates[num_to_keep:]:
        if (date - epoch).days % frequency_to_keep != 0:
            for tarball in tarballs_by_date[date]:
                logging.debug('Removing HAR archive: %s' % tarball)
                os.remove(tarball)
        

def purge_logs(log_dir, max_size):
    '''Delete any stdout files larger than max_size. (Log files are managed by
       rotating log handlers.)'''

    for log in glob.glob(log_dir + '/*.stdout'):
        if os.path.getsize(log) > max_size:
            # TODO: keep last 100 lines of log?
            logging.debug('Removing log: %s' % log)
            os.remove(log)






def main():
    if args.screenshots:
        purge_screenshots(args.profiles, args.keepnum)
    if args.hars:
        purge_hars(args.hars, args.keepnum, args.keepfreq)
    if args.logs:
        purge_logs(args.logs, args.maxsize)






if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Purge old crawl data (e.g., old screenshots).')
    parser.add_argument('-p', '--profiles', default='./profiles', help='Profile directory.')
    parser.add_argument('-a', '--hars', help='HAR archive directory.')
    parser.add_argument('-l', '--logs', help='Log file directory')
    parser.add_argument('-s', '--screenshots', action='store_true', default=False, help='Purge screenshots.')
    parser.add_argument('-n', '--keepnum', type=int, default=7, help='Don\'t purge the most recent \'keep\' crawls.')
    parser.add_argument('-f', '--keepfreq', type=int, default=7, help='Keep one out of every __ crawls.')
    parser.add_argument('-m', '--maxsize', type=int, default=10*1024*1024, help='Max size for log files.')
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='only print errors')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='print debug info. --quiet wins if both are present')
    args = parser.parse_args()
    

    # set up logging
    setup_logging()
    
    main()
