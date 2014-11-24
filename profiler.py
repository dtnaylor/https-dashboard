#!/usr/bin/env python

##
## INPUT: Directory of input files (HARs and images)
## OUTPUT: (1) A summary profile (JSON)
##         (2) A per-site profile (JSON)
##         (3) A per-site screenshot (if present in input dir)
##

import os
import sys
import shutil
import argparse
import string
import socket
import json
import logging
import glob
from collections import defaultdict

sys.path.append('./web-profiler')
from webloader.har import Har

try:
    import geoip2.database
except ImportError:
    pass

GEOIP_DB = '/home/dnaylor/Downloads/GeoLite2-City.mmdb'
location_cache = {}


class ObjectStatus:
    SAME = ''
    HTTP_ONLY = '<<<'
    HTTPS_ONLY = '>>>'
    DIFFERENT = '***'
    TOTAL = 'total'

    __labels = {
        SAME: 'Same Origin',
        DIFFERENT: 'Different Origin',
        HTTP_ONLY: 'HTTP Only',
        HTTPS_ONLY: 'HTTPS Only'
    }

    @classmethod
    def human_label(cls, status):
        return ObjectStatus.__labels[status]

# Assuming one of the HARs is HTTP and the other is HTTPS, return
# the HTTP URL
def get_http_har(har1, har2):
    return har2 if 'https' in har1.url else har1

# Assuming one of the HARs is HTTP and the other is HTTPS, return
# the HTTPS URL
def get_https_har(har1, har2):
    return har1 if 'https' in har1.url else har2

def get_location_for_domain(domain):
    global location_cache
    response = None

    if domain in location_cache:
        response = location_cache[domain]

    try:
        # resolve DNS name
        ip = socket.gethostbyname(domain)
        
        # map IP to location
        reader = geoip2.database.Reader(GEOIP_DB)
        response = reader.city(ip)
        location_cache[domain] = response
    except Exception as e:
        return ''

    if response.city.name:
        return '%s, %s' % (response.city.name, response.country.name)
    else:
        return ''

def profile_dir():
    return os.path.join(args.outdir, 'site_profiles')

def screenshot_dir():
    return os.path.join(args.outdir, 'site_screenshots')


# expects "objects" as a dict:
# filename -> har url -> origin server
# filename -> 'status' -> ObjectStatus
def print_summary(counts, har1, har2):
    print '='*50
    print 'HAR 1: %s' % har1.url
    print '\tHTTP Objects: %d' % har1.num_http_objects
    print '\tHTTPS Objects: %d' % har1.num_https_objects
    print 'HAR 2: %s' % har2.url
    print '\tHTTP Objects: %d' % har2.num_http_objects
    print '\tHTTPS Objects: %d\n' % har2.num_https_objects
    print 'Objects w/ same origin:\t%d' % counts[ObjectStatus.SAME]
    print 'Objects w/ diff origin:\t%d' % counts[ObjectStatus.DIFFERENT]
    print 'HTTP-only objects:\t%d' % counts[ObjectStatus.HTTP_ONLY]
    print 'HTTPS-only objects:\t%d' % counts[ObjectStatus.HTTPS_ONLY]
    print '='*50


# expects "objects" as a dict:
# filename -> har url -> origin server
# filename -> 'status' -> ObjectStatus
def print_table(objects, har1, har2):
    # setup
    obj_width = 55
    domain_width = 35
    row_format ="{:>%d.%d}   {:<%d.%d}   {:<%d.%d} {:<3}" %\
        (obj_width, obj_width, domain_width, domain_width, domain_width, domain_width)
    width = obj_width+2*domain_width+7

    # print header
    print '='*width
    print row_format.format('', har1.url, har2.url, '')
    print row_format.format('',
        '(%d objects, %d hosts)' % (har1.num_objects, har1.num_hosts),
        '(%d objects, %d hosts)' % (har2.num_objects, har2.num_hosts), '')
    print '-'*width

    # print body
    for obj in objects:
        http_origin = objects[obj]['http-origin']
        https_origin = objects[obj]['https-origin']
        print row_format.format(obj, http_origin, https_origin, objects[obj]['status'])
        
        if args.locations:
            http_origin_loc = get_location_for_domain(http_origin)
            https_origin_loc = get_location_for_domain(https_origin)
            print row_format.format('', origin1_loc, origin2_loc, '')
    print '='*width


def compare_objects(http_har, https_har, do_print=False):

    # filename -> har url -> origin server
    # filename -> 'status' -> ObjectStatus
    objects = defaultdict(lambda: defaultdict(str))

    if http_har:
        for obj in http_har.objects:
            objects[obj.filename]['http-origin'] = obj.host
            objects[obj.filename]['http-protocol'] = obj.protocol
    if https_har:
        for obj in https_har.objects:
            objects[obj.filename]['https-origin'] = obj.host
            objects[obj.filename]['https-protocol'] = obj.protocol

    # count number of different objects and origin domains
    counts = defaultdict(int)
    total = 0

    for obj in objects:
        http_origin = objects[obj]['http-origin']
        https_origin = objects[obj]['https-origin']
        if http_origin == '' and https_origin != '':
            objects[obj]['status'] = ObjectStatus.HTTPS_ONLY
        elif https_origin == '' and http_origin != '':
            objects[obj]['status'] = ObjectStatus.HTTP_ONLY
        elif http_origin != https_origin:
            objects[obj]['status'] = ObjectStatus.DIFFERENT
        else:
            objects[obj]['status'] = ObjectStatus.SAME
        counts[objects[obj]['status']] += 1
        total += 1
        
    if do_print:
        print_summary(counts, har1, har2)
        print_table(objects, har1, har2)

    return objects, counts, total


def save_profile(http_har, https_har, outdir):
    '''Save a joint profile comparing the two HARs, for use in the HTTPS dashboard'''
    # will eventually dump this dict to JSON
    profile = {}

    ##
    ## Availability
    ##
    if http_har and not https_har:
        profile['availability'] = 'http-only'
    elif not http_har and https_har:
        profile['availability'] = 'https-only'
    else:
        profile['availability'] = 'both'
                
    if https_har:
        profile['https_partial'] = 'yes' if https_har.num_http_objects > 0 else 'no'
        
    

    ##
    ## Individual profiles
    ##
    if http_har: profile['http-profile'] = http_har.profile
    if https_har: profile['https-profile'] = https_har.profile

    ##
    ## URLs
    ##
    if http_har:
        print http_har.url
        profile['base-url'] = http_har.url.split('://')[1]
    else:
        profile['base-url'] = https_har.url.split('://')[1]
    if http_har: profile['http-url'] = http_har.url
    if https_har: profile['https-url'] = https_har.url

    ##
    ## Number of objects loaded with HTTP and HTTPS for each version
    ##
    if http_har:
        profile['http-protocol-counts'] = [['HTTP', http_har.num_http_objects],
                                           ['HTTPS', http_har.num_https_objects]]
    if https_har:
        profile['https-protocol-counts'] = [['HTTP', https_har.num_http_objects],
                                            ['HTTPS', https_har.num_https_objects]]

    ##
    ## Object details
    ##
    #if http_har and https_har:
    profile['object-details'] = []
    objects, _, _ = compare_objects(http_har, https_har)
    for obj in objects:
        d = dict(objects[obj])  # make a copy of the dict
        d['filename'] = obj if obj != '' else '/'
        profile['object-details'].append(d)

    ##
    ## Save as JSON
    ##
    filename = None
    if http_har:
        filename = '%s.json' % Har.sanitize_url(http_har.url.split('://')[1])
    else:
        filename = '%s.json' % Har.sanitize_url(https_har.url.split('://')[1])
    filepath = os.path.join(outdir, filename)
    with open(filepath, 'w') as f:
        json.dump(profile, f)
    f.closed
    

def three_sort(result_dict):
    '''Sort the data (all three lists) three ways: alphabetically by URL,
       numerically by HTTP numbers, and numerically by HTTPS numbers. Store 
       each version in the supplied result_dict'''
    
    zipped = zip(result_dict['url']['sort-alpha'],
                 result_dict['HTTP']['sort-alpha'],
                 result_dict['HTTPS']['sort-alpha'])

    # sort by URL
    unzipped = zip(*sorted(zipped, key=lambda x: x[0]))
    result_dict['url']['sort-alpha'] = unzipped[0]
    result_dict['HTTP']['sort-alpha'] = unzipped[1]
    result_dict['HTTPS']['sort-alpha'] = unzipped[2]

    # sort by HTTP
    unzipped = zip(*sorted(zipped, key=lambda x: x[1])) 
    result_dict['url']['sort-http'] = unzipped[0]
    result_dict['HTTP']['sort-http'] = unzipped[1]
    result_dict['HTTPS']['sort-http'] = unzipped[2]
    
    # sort by HTTPS
    unzipped = zip(*sorted(zipped, key=lambda x: x[2])) 
    result_dict['url']['sort-https'] = unzipped[0]
    result_dict['HTTP']['sort-https'] = unzipped[1]
    result_dict['HTTPS']['sort-https'] = unzipped[2]



def main():

    # compare two HARs for manual inspection
    if args.har1 and args.har1:
        har1 = Har.from_file(args.har1)
        har2 = Har.from_file(args.har2)

        compare_objects(har1, har2, do_print=True)

    # make profiles for many HARs at once
    if args.indir:
        logging.info('Profiling HARs in %s' % args.indir)
        
        # figure out, based on the existence of har files, which sites are
        # accessible over HTTP only, HTTPS only, or both
        http_only_harpaths = []
        https_only_harpaths = []
        both_harpaths = []  # stores tuples: (http-path, https-path)
        for http_path in glob.glob(args.indir + '/http---*.har'):
            # look for an HTTPS HAR
            https_path = string.replace(http_path, 'http---', 'https---')
            if os.path.exists(https_path):
                both_harpaths.append((http_path, https_path))
            else:
                http_only_harpaths.append(http_path)
        for https_path in glob.glob(args.indir + '/https---*.har'):
            # look for an HTTP HAR
            http_path = string.replace(https_path, 'https---', 'http---')
            if not os.path.exists(http_path):
                https_only_harpaths.append(https_path)

        # summary dict maps stat names (e.g., 'num_objects') to dictionaries:
        #   'url' -> list of URLs
        #   'HTTP' -> HTTP value for this stat
        #   'HTTPS' -> HTTPS value for this stat
        summary = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        summary['sites'] = []  # 'sites' is just a list, not a dict like the others
        summary['availability'] = [
            ['HTTP Only', len(http_only_harpaths)],
            ['HTTPS Only', len(https_only_harpaths)],
            ['Both', len(both_harpaths)]
        ]
        basic_stats = ('num_objects', 'num_tcp_handshakes', 'num_mbytes', 'num_hosts',)

        # extract stats from the sites accessible over only HTTP
        for http_path in http_only_harpaths:
            logging.debug('Har path: %s' % http_path)
            # load HAR
            http_har = Har.from_file(http_path)
            save_profile(http_har, None, profile_dir())
            
            ##
            ## global summary stats
            ##
            summary['sites'].append({
                'site':http_har.base_url,  # URL
                'availability':'http-only',  # protocol availability
            })
        
        # extract stats from the sites accessible over only HTTPS
        for https_path in https_only_harpaths:
            logging.debug('Har path: %s' % https_path)
            # load HAR
            https_har = Har.from_file(https_path)
            save_profile(None, https_har, profile_dir())
            
            ##
            ## global summary stats
            ##
            summary['sites'].append({
                'site':https_har.base_url,  # URL
                'availability':'https-only',  # protocol availability
                'https_partial':'yes' if https_har.num_http_objects > 0 else 'no',
            })

        # extract stats from the sites accessible over both protocols
        for http_path, https_path in both_harpaths:
            logging.debug('Har paths: %s, %s', http_path, https_path)
            # load both HARs
            http_har = Har.from_file(http_path)
            https_har = Har.from_file(https_path)
            save_profile(http_har, https_har, profile_dir())

            ##
            ## global summary stats
            ##
            summary['sites'].append({
                'site':http_har.base_url,  # URL
                'availability':'both',  # protocol availability
                'https_partial':'yes' if https_har.num_http_objects > 0 else 'no',
            })

            # number of objects fetched per protocol
            # will eventually sort three ways; for now, just temporarily put it 
            # in the order the HARs are in under 'sort-alpha'
            summary['http_site_protocol_counts']['url']['sort-alpha'].append(http_har.base_url)
            summary['http_site_protocol_counts']['HTTP']['sort-alpha'].append(http_har.num_http_objects)
            summary['http_site_protocol_counts']['HTTPS']['sort-alpha'].append(http_har.num_https_objects)
            summary['https_site_protocol_counts']['url']['sort-alpha'].append(https_har.base_url)
            summary['https_site_protocol_counts']['HTTP']['sort-alpha'].append(https_har.num_http_objects)
            summary['https_site_protocol_counts']['HTTPS']['sort-alpha'].append(https_har.num_https_objects)

            # basic stats
            # Careful! the 'url', 'HTTP', and 'HTTPS' tags mean something
            # slightly different from above
            for stat in basic_stats:
                summary[stat]['url']['sort-alpha'].append(http_har.base_url)
                summary[stat]['HTTP']['sort-alpha'].append(http_har.get_by_name(stat))
                summary[stat]['HTTPS']['sort-alpha'].append(https_har.get_by_name(stat))

        # sort stats by HTTP and by HTTPS; save all three versions
        for stat in basic_stats + ('http_site_protocol_counts', 'https_site_protocol_counts'):
            if len(summary[stat]) > 0:
                three_sort(summary[stat])

        # save summary stats
        filepath = os.path.join(args.outdir, 'summary.json')
        with open(filepath, 'w') as f:
            json.dump(summary, f)
        f.closed

        # copy screenshots to outdir, if present
        for screenshot_path in glob.glob(args.indir + '/*.png'):
            shutil.copy(screenshot_path, screenshot_dir())




if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Compare two HARs.')
    parser.add_argument('har1', nargs='?', help='HAR 1')
    parser.add_argument('har2', nargs='?', help='HAR 2')
    parser.add_argument('-d', '--indir', default=None, help='Directory containing input files (HARs and images).')
    parser.add_argument('-o', '--outdir', default='.', help='Destination directory for profiles.')
    parser.add_argument('-l', '--locations', action='store_true', default=False, help='Print the locations of origin servers')
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
        'format' : "%(levelname) -10s %(asctime)s %(module)s:%(lineno) -7s %(message)s",
        'level' : level
    }
    if args.logfile:
        config['filename'] = args.logfile
    logging.basicConfig(**config)
    
    # set up output directory
    try:
        if not os.path.isdir(args.outdir):
            os.makedirs(args.outdir)
        if not os.path.isdir(profile_dir()):
            os.makedirs(profile_dir())
        if not os.path.isdir(screenshot_dir()):
            os.makedirs(screenshot_dir())
    except Exception as e:
        logging.exception('Error making output directory: %s' % args.outdir)
        sys.exit(-1)
    
    main()
