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
import time
import datetime
import json
import glob

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

from logging import handlers

import thumbnailer

# tools
ALEXA_URL_FETCHER = './alexa_top_sites.py'
URL_PREPARER = './prepare_url_list.py'
HAR_GENERATOR = './web-profiler/tools/har_generator.py'
SCREENSHOT_GENERATOR = './web-profiler/tools/screenshot_generator.py'
PROFILER = './profiler.py'
RSYNC = '/usr/bin/env rsync'
RESULT_CHECKER = './check_results.py'



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


def send_mail(send_from, send_to, subject, text, server, credentials, files=[]):
    assert isinstance(send_to, list)
    assert isinstance(files, list)

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)
    


    smtp = smtplib.SMTP_SSL(server)
    smtp.login(*credentials)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()


class TimeLog(object):

    def __init__(self, format='%H:%M:%S'):
        self._times = []  # list of tuples: (tag, timestamp)
        self._format = format
    
    def record_time(self, tag):
        self._times.append((tag, datetime.datetime.now()))

    def __str__(self):
        string = ''
        last_timestamp = None
        for tag, timestamp in self._times:
            difference = ''
            if last_timestamp:
                difference = '\t(%s)' % (timestamp - last_timestamp)

            string += '%s\t%s%s\n' % (tag, timestamp.strftime(self._format), difference)

            last_timestamp = timestamp

        string += '\nTOTAL TIME ELAPSED:  %s' % (self._times[-1][1] - self._times[0][1])

        return string

    def __repr__(self):
        return self.__str__()



def main():
    logging.info('=============== MANAGER LAUNCHED ===============')

    timelog = TimeLog()
    timelog.record_time('Manager launched')


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
    timelog.record_time('Set up temp directory')



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
    timelog.record_time('Set up output directory')



    ##
    ## Prepare URL list
    ##
    if not conf['URL_FILE']:
        try:
            alexa_url_list = '%s/alexa_url_list.txt' % conf['TEMPDIR']
            prepared_url_list = '%s/prepared_url_list.txt' % conf['TEMPDIR']

            # Get top 500 Alexa URLs
            # TODO: top 500
            alexa_cmd = '%s -n 500 > %s' % (ALEXA_URL_FETCHER, alexa_url_list)
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
        timelog.record_time('Prepared URL list')



    ##
    ## Generate profiles
    ##
    for user_agent_tag in conf['USER_AGENTS']:
        logging.info('Generating profiles for user agent: %s' % user_agent_tag)
            
        uagent_tmpdir = os.path.join(conf['TEMPDIR'], user_agent_tag)
        uagent_outdir = os.path.join(conf['OUT_SUBDIR'], user_agent_tag)

        ##
        ## STAGE ONE: Capture HARs for the URLs
        ##
        try:
            har_cmd = '%s -f %s -o %s -g %s -t %s -v' %\
                (HAR_GENERATOR, conf['URL_FILE'], uagent_tmpdir,\
                conf['HAR_GENERATOR_LOG'], conf['HAR_GENERATOR_STDOUT'])
            if conf['USER_AGENTS'][user_agent_tag]['string']:
                har_cmd += ' -u "%s"' % conf['USER_AGENTS'][user_agent_tag]['string']
            logging.debug('Running HAR genrator: %s', har_cmd)
            subprocess.check_call(har_cmd, shell=True)  # TODO: careful!
        except:
            logging.exception('Error capturing HARs for user agent %s', user_agent_tag)
            # TODO: mark error?
        timelog.record_time('%s: HARs' % user_agent_tag)


        ##
        ## STAGE TWO: Capture screenshots for the URLs
        ##
        try:
            screenshot_cmd = '%s -f %s -o %s -g %s -v' %\
                (SCREENSHOT_GENERATOR, conf['URL_FILE'], uagent_tmpdir, conf['SCREENSHOT_GENERATOR_LOG'])
            if conf['USER_AGENTS'][user_agent_tag]['string']:
                screenshot_cmd += ' -u "%s"' % conf['USER_AGENTS'][user_agent_tag]['string']
            logging.debug('Running screenshot genrator: %s', screenshot_cmd)
            subprocess.check_call(screenshot_cmd, shell=True)  # TODO: careful!
        except:
            logging.exception('Error capturing screenshots for user agent %s', user_agent_tag)
            # TODO: mark error?
        timelog.record_time('%s: screenshots' % user_agent_tag)


        ##
        ## STAGE TWO AND A HALF: Copy pickled results from tmpdir to outdir
        ##
        try:
            for pickle_file in glob.glob(uagent_tmpdir + '/*.pickle'):
                shutil.copy(pickle_file, uagent_outdir)
        except:
            logging.exception('Error copying pickled results.')
    
    
        ##
        ## STAGE THREE: Generate profiles
        ##
        try:
            profiler_cmd = '%s -d %s -o %s -g %s -v' %\
                (PROFILER, uagent_tmpdir, uagent_outdir, conf['PROFILER_LOG'])
            logging.debug('Running profiler: %s', profiler_cmd)
            subprocess.check_call(profiler_cmd.split())
        except:
            logging.exception('Error profiling user agent %s', user_agent_tag)
            # TODO: mark error?
        timelog.record_time('%s: profiles' % user_agent_tag)


        ##
        ## STAGE FOUR: Prepare image thumbnails
        ##
        try:
            screenshot_dir = os.path.join(uagent_outdir, 'site_screenshots')
            thumbnailer.process_image_dir(screenshot_dir)
            
        except:
            logging.exception('Error processing thumbnails for user agent %s', user_agent_tag)
            # TODO: mark error?
        timelog.record_time('%s: thumbnails' % user_agent_tag)



    ##
    ## If successful, update main manifest
    ##
    # TODO: only update if everything was OK?
    # TODO: filter old crawls (adjust manifest, build rsync exclude list)
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
        # make an rsync exclude file
        rsync_exclude_path = os.path.join(conf['TEMPDIR'], 'rsync.exclude')
        with open(rsync_exclude_path, 'w') as f:
            for entry in conf['RSYNC_EXCLUDE']:
                f.write('%s\n' % entry)
        f.closed
        # TODO: also add files we want to pull off the web server

        # renew kerberos ticket
        subprocess.check_call('kinit -R'.split())

        # sync files
        rsync_cmd = '%s -avz --delete --delete-excluded --exclude-from=%s %s %s:%s' %\
            (RSYNC, rsync_exclude_path, conf['OUTDIR'], conf['WEB_SERVER'],\
            conf['WEB_SERVER_DIR'])
        logging.debug('Running rsync: %s', rsync_cmd)
        subprocess.check_call(rsync_cmd.split())
    except:
        logging.exception('Error copying profiles to web server')
    timelog.record_time('Uploaded to AFS')



    ##
    ## Send summary email
    ##
    try:
        # generate HAR summary file
        har_summary_path = os.path.join(conf['TEMPDIR'], 'har_summary.txt')
        checker_cmd = '%s %s -f %s > %s'\
            % (RESULT_CHECKER, conf['OUTDIR'], 'har_generator_results.pickle',\
                har_summary_path)
            
        logging.debug('Running checker for HAR files: %s', checker_cmd)
        subprocess.check_call(checker_cmd, shell=True)  # TODO: careful!
        
        # generate screenshot summary file
        screenshot_summary_path = os.path.join(conf['TEMPDIR'], 'screenshot_summary.txt')
        checker_cmd = '%s %s -f %s > %s'\
            % (RESULT_CHECKER, conf['OUTDIR'],\
                'screenshot_generator_results.pickle', screenshot_summary_path)
            
        logging.debug('Running checker for screenshot files: %s', checker_cmd)
        subprocess.check_call(checker_cmd, shell=True)  # TODO: careful!
    
        # email summary files
        smtp_conf = None
        with open(conf['SMTP_CONF'], 'r') as f:
            smtp_conf = eval(f.read())
        f.closed

        send_mail('dtbn07@gmail.com',\
                  ['dtbn07@gmail.com'],\
                  'HTTPS Dashboard Crawl Summary',\
                  '%s\n\n' % timelog,\
                  smtp_conf['server'],\
                  smtp_conf['credentials'],\
                  files=[har_summary_path, screenshot_summary_path])
    except:
        logging.exception('Error sending summary email.')



    ##
    ## Delete temp directories
    ##
    #shutil.rmtree(conf['TEMPDIR'])

    
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
