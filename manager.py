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
import json

import thumbnailer

HAR_GENERATOR = './web-profiler/tools/har_generator.py'
SCREENSHOT_GENERATOR = './web-profiler/tools/screenshot_generator.py'
PROFILER = './profiler.py'
RSYNC = '/usr/bin/env rsync'

# TODO: put these in conf file
MANAGER_LOG='./logs/manager.log'
HAR_GENERATOR_LOG='./logs/har_generator.log'
PROFILER_LOG='./logs/profiler.log'

URL_FILE='./web-profiler/tools/tmp_urls'
USER_AGENTS={
    'chrome-37-osx':
       {'name': 'Chrome 37 (OSX)', 'string': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.94 Safari/537.36'},
    'chrome-18-android':
       {'name': 'Chrome 18 (Android)', 'string': 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19'},
}
#USER_AGENTS={'default': 
#                {'name': 'Default', 'string': None},
#}
TEMPDIR=os.path.join(tempfile.gettempdir(), 'https-dashboard')
OUTDIR='./profiles'
#WEB_SERVER='linux.gp.cs.cmu.edu'
WEB_SERVER='linuxgp'
WEB_SERVER_DIR='/afs/cs.cmu.edu/project/httpsdashboard/www'

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
    today = None
    try:
        # make new directory in outdir named with today's date
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        OUT_SUBDIR = os.path.abspath(os.path.join(OUTDIR, today))
        if os.path.exists(OUT_SUBDIR):
            backup_dir = '%s_backup-%s' %\
                (OUT_SUBDIR, datetime.datetime.now().strftime('%H-%M-%S'))
            logging.warn('Subdirectory for today already exists; moving to: %s', backup_dir)
            shutil.move(OUT_SUBDIR, backup_dir)
        os.makedirs(OUT_SUBDIR)
        
        # make a subdir for each user agent
        for user_agent_tag in USER_AGENTS:
            os.makedirs(os.path.join(OUT_SUBDIR, user_agent_tag))

        # write manifest file
        # TODO: add crawl date
        manifest = {
            'user-agents': USER_AGENTS,
        }
        manifest_file = os.path.join(OUT_SUBDIR, 'crawl-manifest.json')
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f)
        f.closed

        logging.info('Set up output subdirectory: %s', OUT_SUBDIR)
    except:
        logging.exception('Error preparing output directory')
        sys.exit(-1)



    ##
    ## Generate profiles
    ##
    for user_agent_tag in USER_AGENTS:
        try:

            ##
            ## STAGE ONE: Generate HARs and screenshots for the URLs
            ##
            uagent_tmpdir = os.path.join(TEMPDIR, user_agent_tag)
            har_cmd = '%s -f %s -o %s -g %s' %\
                (HAR_GENERATOR, URL_FILE, uagent_tmpdir, HAR_GENERATOR_LOG)
            screenshot_cmd = '%s -f %s -o %s -g %s' %\
                (SCREENSHOT_GENERATOR, URL_FILE, uagent_tmpdir, HAR_GENERATOR_LOG)
            if USER_AGENTS[user_agent_tag]['string']:
                har_cmd += ' -u "%s"' % USER_AGENTS[user_agent_tag]['string']
                screenshot_cmd += ' -u "%s"' % USER_AGENTS[user_agent_tag]['string']
            logging.debug('Running HAR genrator: %s', har_cmd)
            subprocess.check_call(har_cmd, shell=True)  # TODO: careful!
            logging.debug('Running screenshot genrator: %s', screenshot_cmd)
            subprocess.check_call(screenshot_cmd, shell=True)  # TODO: careful!
    
    
            ##
            ## STAGE TWO: Generate profiles
            ##
            uagent_outdir = os.path.join(OUT_SUBDIR, user_agent_tag)
            profiler_cmd = '%s -d %s -o %s -g %s -v' %\
                (PROFILER, uagent_tmpdir, uagent_outdir, PROFILER_LOG)
            logging.debug('Running profiler: %s', profiler_cmd)
            subprocess.check_call(profiler_cmd.split())

            ##
            ## STAGE THREE: Prepare image thumbnails
            ##
            screenshot_dir = os.path.join(uagent_outdir, 'site_screenshots')
            thumbnailer.process_image_dir(screenshot_dir)
            
        except:
            logging.exception('Error profiling user agent %s', user_agent_tag)
            # TODO: mark error?


    ##
    ## Delete temp directories
    ##
    shutil.rmtree(TEMPDIR)

    ##
    ## If successful, update main manifest
    ##
    # TODO: only update if everything was OK?
    try:
        main_manifest_file = os.path.join(OUTDIR, 'main-manifest.json')
        if os.path.exists(main_manifest_file):
            with open(main_manifest_file, 'r') as f:
                main_manifest = json.load(f)
            f.closed
        else:
            main_manifest = {'dates': []}

        if today not in main_manifest['dates']:
            main_manifest['dates'].append(today)
        main_manifest['dates'] = sorted(main_manifest['dates'], reverse=True)

        with open(main_manifest_file, 'w') as f:
            json.dump(main_manifest, f)
        f.closed

    except:
        logging.exception('Error saving main manifest')


    ##
    ## Copy files to web server
    ##
    # TODO: test
    try:
        rsync_cmd = '%s -avz %s %s:%s' %\
            (RSYNC, OUTDIR, WEB_SERVER, WEB_SERVER_DIR)
        logging.debug('Running rsync: %s', rsync_cmd)
        subprocess.check_call(rsync_cmd.split())
    except:
        logging.exception('Error copying profiles to web server')

    
    logging.info('Done.')



if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Compare two HARs.')
    parser.add_argument('-c', '--config', default='./default.conf', help='Manager configuration file')
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='only print errors')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='print debug info. --quiet wins if both are present')
    #parser.add_argument('-g', '--logfile', default=None, help='Path for log file.')
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
