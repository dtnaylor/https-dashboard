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

from logging import handlers

import thumbnailer

# tools
ALEXA_URL_FETCHER = './alexa_top_sites.py'
URL_PREPARER = './prepare_url_list.py'
HAR_GENERATOR = './web-profiler/tools/har_generator.py'
SCREENSHOT_GENERATOR = './web-profiler/tools/screenshot_generator.py'
PROFILER = './profiler.py'
RSYNC = '/usr/bin/env rsync'



def setup_logging():
    if args.quiet:
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    config = {
        'filename': conf['MANAGER_LOG'],
        'format' : "%(levelname) -10s %(asctime)s %(module)s:%(lineno) -7s %(message)s",
        'level' : level
    }
    logging.basicConfig(**config)

    # email me on error or exception
    smtp_conf = None
    with open(conf['SMTP_CONF'], 'r') as f:
        smtp_conf = eval(f.read())
    f.closed

    email_handler = handlers.SMTPHandler(\
        smtp_conf['server'], 'dtbn07@gmail.com',\
        ['dtbn07@gmail.com'], 'HTTPS Dashboard Error',\
        credentials=smtp_conf['credentials'], secure=())
    email_handler.setLevel(logging.ERROR)
    logging.getLogger('').addHandler(email_handler)


def load_conf(conf_file):
    conf = None
    try:
        with open(conf_file, 'r') as f:
            conf = eval(f.read())
        f.closed
    except:
        logging.exception('Error reading configuration: %s', conf_file)

    return conf



def main():
    logging.info('=============== MANAGER LAUNCHED ===============')

    ##
    ## Prepare temp directories
    ##
    try:
        if not conf['TEMPDIR']:
            conf['TEMPDIR'] = os.path.join(tempfile.gettempdir(), 'https-dashboard')

        if os.path.exists(conf['TEMPDIR']):
            logging.info('Removing existing temp directory')
            shutil.rmtree(conf['TEMPDIR'])
        os.makedirs(conf['TEMPDIR'])

        # make a subdir for each user agent
        for user_agent_tag in conf['USER_AGENTS']:
            os.makedirs(os.path.join(conf['TEMPDIR'], user_agent_tag))

        logging.info('Set up temp directory: %s', conf['TEMPDIR'])
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
        conf['OUT_SUBDIR'] = os.path.abspath(os.path.join(conf['OUTDIR'], today))
        if os.path.exists(conf['OUT_SUBDIR']):
            backup_dir = '%s_backup-%s' %\
                (conf['OUT_SUBDIR'], datetime.datetime.now().strftime('%H-%M-%S'))
            logging.warn('Subdirectory for today already exists; moving to: %s', backup_dir)
            shutil.move(conf['OUT_SUBDIR'], backup_dir)
        os.makedirs(conf['OUT_SUBDIR'])
        
        # make a subdir for each user agent
        for user_agent_tag in conf['USER_AGENTS']:
            os.makedirs(os.path.join(conf['OUT_SUBDIR'], user_agent_tag))

        # write manifest file
        # TODO: add crawl date
        manifest = {
            'user-agents': conf['USER_AGENTS'],
        }
        manifest_file = os.path.join(conf['OUT_SUBDIR'], 'crawl-manifest.json')
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f)
        f.closed

        logging.info('Set up output subdirectory: %s', conf['OUT_SUBDIR'])
    except:
        logging.exception('Error preparing output directory')
        sys.exit(-1)



    ##
    ## Prepare URL list
    ##
    if not conf['URL_FILE']:
        try:
            alexa_url_list = '%s/alexa_url_list.txt' % conf['TEMPDIR']
            prepared_url_list = '%s/prepared_url_list.txt' % conf['TEMPDIR']

            # Get top 500 Alexa URLs
            # TODO: top 500
            alexa_cmd = '%s -n 1 > %s' % (ALEXA_URL_FETCHER, alexa_url_list)
            logging.info('Getting Alexa URLs: %s' % alexa_cmd)
            subprocess.check_call(alexa_cmd, shell=True)  # TODO: careful!

            # Make a file with the HTTP and HTTPS versions of those URLs
            prepare_cmd = '%s %s %s' %\
                (URL_PREPARER, alexa_url_list, prepared_url_list)
            logging.info('Preparing URL list: %s' % prepare_cmd)
            subprocess.check_call(prepare_cmd.split())

            conf['URL_FILE'] = prepared_url_list
        except:
            logging.exception('Error preparing URL list')
            sys.exit(-1)


    ##
    ## Generate profiles
    ##
    for user_agent_tag in conf['USER_AGENTS']:
        logging.info('Generating profiles for user agent: %s' % user_agent_tag)
        try:

            ##
            ## STAGE ONE: Generate HARs and screenshots for the URLs
            ##
            uagent_tmpdir = os.path.join(conf['TEMPDIR'], user_agent_tag)
            har_cmd = '%s -f %s -o %s -g %s -v' %\
                (HAR_GENERATOR, conf['URL_FILE'], uagent_tmpdir, conf['HAR_GENERATOR_LOG'])
            screenshot_cmd = '%s -f %s -o %s -g %s -v' %\
                (SCREENSHOT_GENERATOR, conf['URL_FILE'], uagent_tmpdir, conf['SCREENSHOT_GENERATOR_LOG'])
            if conf['USER_AGENTS'][user_agent_tag]['string']:
                har_cmd += ' -u "%s"' % conf['USER_AGENTS'][user_agent_tag]['string']
                screenshot_cmd += ' -u "%s"' % conf['USER_AGENTS'][user_agent_tag]['string']
            logging.debug('Running HAR genrator: %s', har_cmd)
            subprocess.check_call(har_cmd, shell=True)  # TODO: careful!
            logging.debug('Running screenshot genrator: %s', screenshot_cmd)
            subprocess.check_call(screenshot_cmd, shell=True)  # TODO: careful!
    
    
            ##
            ## STAGE TWO: Generate profiles
            ##
            uagent_outdir = os.path.join(conf['OUT_SUBDIR'], user_agent_tag)
            profiler_cmd = '%s -d %s -o %s -g %s -v' %\
                (PROFILER, uagent_tmpdir, uagent_outdir, conf['PROFILER_LOG'])
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
    #shutil.rmtree(conf['TEMPDIR'])

    ##
    ## If successful, update main manifest
    ##
    # TODO: only update if everything was OK?
    try:
        main_manifest_file = os.path.join(conf['OUTDIR'], 'main-manifest.json')
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
    try:
        rsync_cmd = '%s -avz --delete %s %s:%s' %\
            (RSYNC, conf['OUTDIR'], conf['WEB_SERVER'], conf['WEB_SERVER_DIR'])
        logging.debug('Running rsync: %s', rsync_cmd)
        subprocess.check_call(rsync_cmd.split())
    except:
        logging.exception('Error copying profiles to web server')

    
    logging.info('Done.')



if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Manage all the stages of site crawling for HTTPS Dashboard.')
    parser.add_argument('-c', '--config', default='./default.conf', help='Manager configuration file')
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='only print errors')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='print debug info. --quiet wins if both are present')
    #parser.add_argument('-g', '--logfile', default=None, help='Path for log file.')
    args = parser.parse_args()
    


    # load conf
    conf = load_conf(args.config)


    # set up logging
    setup_logging()
    
    main()
