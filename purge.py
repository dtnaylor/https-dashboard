#!/usr/bin/env python

##
## Purges old crawl data (e.g., old screenshots)
##

import os
import sys
import argparse
import logging
import glob


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
            if 'thumb' not in img]:                      # filter out thumbnails

            try:
                logging.debug('Removing %s', screenshot)
                os.remove(screenshot)
            except:
                logging.exception('Error removing %s', screenshot)


# TODO: implement
def purge_hars(har_archive_dir, frequency_to_keep):
    pass





def main():
    if args.screenshots:
        purge_screenshots(args.profiles, args.keepnum)
    if args.hars:
        if not args.hars:
            logging.error('Please specify the HAR archive directory.')
        else:
            purge_hars(args.hars, args.keepfreq)






if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Purge old crawl data (e.g., old screenshots).')
    parser.add_argument('-p', '--profiles', default='./profiles', help='Profile directory.')
    parser.add_argument('-a', '--hars', help='HAR archive directory.')
    parser.add_argument('-s', '--screenshots', action='store_true', default=False, help='Purge screenshots.')
    parser.add_argument('-n', '--keepnum', type=int, default=7, help='Don\'t purge the most recent \'keep\' crawls.')
    parser.add_argument('-f', '--keepfreq', type=int, default=7, help='Keep one out of every __ crawls.')
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='only print errors')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='print debug info. --quiet wins if both are present')
    args = parser.parse_args()
    

    # set up logging
    setup_logging()
    
    main()
