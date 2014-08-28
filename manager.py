#!/usr/bin/env python

##
## Manages all stages of the HTTPS dashboard pipeline:
##  1) Gather HAR files for sites of interest.
##  2) Generate profiles based on the HAR files.
##

import os
import sys
import argparse
import logging
import subprocess
import tempfile
import shutil
import datetime

HAR_GENERATOR = './web-profiler/tools/har_generator.py'
PROFILER = './profiler.py'

# TODO: put these in conf file
MANAGER_LOG='./logs/manager.log'
HAR_GENERATOR_LOG='./logs/har_generator.log'
PROFILER_LOG='./logs/profiler.log'

URL_FILE='./web-profiler/tools/tmp_urls'
USER_AGENTS={'chrome-37': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.94 Safari/537.36'}
TEMPDIR=os.path.join(tempfile.gettempdir(), 'https-dashboard')
OUTDIR='./profiles'

OUT_SUBDIR = None



def main():

    ##
    ## Prepare temp directories
    ##
    try:
        if os.path.exists(TEMPDIR):
            logging.info('Removing existing temp directory')
            shutil.rmtree(TEMPDIR)
        os.makedirs(TEMPDIR)

        # make a subdir for each user agent
        for user_agent_tag in USER_AGENTS:
            os.makedirs(os.path.join(TEMPDIR, user_agent_tag))

        logging.info('Set up temp directory: %s', TEMPDIR)
    except:
        logging.exception('Error preparing temp directory')
        sys.exit(-1)


    ##
    ## Prepare output directories
    ##
    try:
        # make new directory in outdir named with today's date
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        OUT_SUBDIR = os.path.join(OUTDIR, today)
        if os.path.exists(OUT_SUBDIR):
            backup_dir = '%s_backup-%s' %\
                (OUT_SUBDIR, datetime.datetime.now().strftime('%H-%M-%S'))
            logging.warn('Subdirectory for today already exists; moving to: %s', backup_dir)
            shutil.move(OUT_SUBDIR, backup_dir)
        os.makedirs(OUT_SUBDIR)
        
        # make a subdir for each user agent
        for user_agent_tag in USER_AGENTS:
            os.makedirs(os.path.join(OUT_SUBDIR, user_agent_tag))

        logging.info('Set up output subdirectory: %s', OUT_SUBDIR)
    except:
        logging.exception('Error preparing output directory')
        sys.exit(-1)


    ##
    ## STAGE ONE: Generate HARs for the URLs
    ##
    for user_agent_tag in USER_AGENTS:
        try:
            uagent_dir = os.path.join(OUT_SUBDIR, user_agent_tag)
            har_cmd = '%s -f %s -o %s -u "%s" -g %s' %\
                (HAR_GENERATOR, URL_FILE, uagent_dir, USER_AGENTS[user_agent_tag],\
                 HAR_GENERATOR_LOG)
            logging.debug('Running HAR genrator: %s', har_cmd)
            subprocess.check_call(har_cmd, shell=True)  # TODO: careful!
        except:
            logging.exception('Error running HAR generator for user agent %s',\
                user_agent_tag)
            # TODO: mark error?

    ##
    ## STAGE TWO: Generate profiles
    ##

    ##
    ## Delete temp directories
    ##

    ##
    ## If successful, update "latest" symlink to point to today's data
    ##



if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Compare two HARs.')
    parser.add_argument('-c', '--config', default='./default.conf', help='Manager configuration file')
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='only print errors')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='print debug info. --quiet wins if both are present')
    parser.add_argument('-g', '--logfile', default=None, help='Path for log file.')
    args = parser.parse_args()
    
    # set up logging
    if args.quiet:
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    config = {
        'filename': MANAGER_LOG,
        'format' : "%(levelname) -10s %(asctime)s %(module)s:%(lineno) -7s %(message)s",
        'level' : level
    }
    logging.basicConfig(**config)
    logging.info('=============== MANAGER LAUNCHED ===============')
    
    main()
