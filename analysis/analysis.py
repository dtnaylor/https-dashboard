#! /usr/bin/env python

import sys
import os
import json
import logging
import argparse
import pprint
import numpy
import glob
from collections import defaultdict

sys.path.append('/home/dnaylor/myplot')
import myplot

############### PLOT SETTINGS ###############
XLABELS = {
    'num_tcp_handshakes': 'TCP Connections',
    'num_hosts': 'Hosts',
    'num_objects': 'Objects',
    'num_mbytes': 'Total Size (MB)',
    'mean_object_size': 'Mean Object Size (kB)',
    'median_object_size': 'Median Object Size (kB)',
    'num_objects_type_image': 'Images',
    'num_objects_type_css': 'CSS Files',
    'num_objects_type_html': 'HTML Files',
    'num_objects_type_javascript': 'Javascript Files',
    'num_objects_type_flash': 'Flash Files',
}

DATA_TRANSFORMS = {
    'num_tcp_handshakes': lambda x: x,
    'num_hosts': lambda x: x,
    'num_objects': lambda x: x,
    'num_mbytes': lambda x: x,
    'mean_object_size': lambda x: x/1024.0,
    'median_object_size': lambda x: x/1024.0,
    'num_objects_type_image': lambda x: x,
    'num_objects_type_css': lambda x: x,
    'num_objects_type_html': lambda x: x,
    'num_objects_type_javascript': lambda x: x,
    'num_objects_type_flash': lambda x: x,
}




############### HELPER FUNCTIONS ###############

# NOTE: if we update main manifest to not show all crawls to make UI manageable,
# we might want to just glob the profile dir instead
def get_crawl_dates(profile_dir):
    '''Get a list of all available crawl dates'''
    with open(os.path.join(profile_dir, 'main-manifest.json'), 'r') as f:
        main_manifest = json.load(f)
    return main_manifest['dates']

def get_user_agents(crawl_dir):
    '''Get a list of the user agents included in this crawl'''
    with open(os.path.join(crawl_dir, 'crawl-manifest.json'), 'r') as f:
        crawl_manifest = json.load(f)
    return crawl_manifest['user-agents'].keys()




############### ANALYSIS FUNCTIONS ###############

def analyze_crawl(crawl_dir):
    '''Plots stats about the specified crawl'''
    logging.info('Analyzing crawl: %s' % crawl_dir)

    # get list of user agents and load stats for each one
    summaries = {}
    user_agents = get_user_agents(crawl_dir)
    for user_agent in user_agents:
        logging.info('User agent: %s' % user_agent)
        uagent_dir = os.path.join(crawl_dir, user_agent)

        # load summary json
        summary = None
        with open(os.path.join(uagent_dir, 'summary.json'), 'r') as f:
            summaries[user_agent] = json.load(f)

    # plot basic stats
    for stat in ('num_tcp_handshakes', 'num_hosts', 'num_mbytes',
        'num_objects', 'mean_object_size', 'median_object_size',
        'num_objects_type_image', 'num_objects_type_css',
        'num_objects_type_html', 'num_objects_type_javascript',
        'num_objects_type_flash'):

        data = []
        labels = []
        linestyles = []
        colors = []
        nextcolor = 0
        for user_agent in user_agents:
            summary = summaries[user_agent]
            if stat not in summary: continue

            transform = numpy.vectorize(DATA_TRANSFORMS[stat])

            data += [ transform(summary[stat]['HTTP']['sort-alpha']),
                     transform(summary[stat]['HTTPS']['sort-alpha']) ]
            labels += ['HTTP (%s)' % user_agent, 'HTTPS (%s)' % user_agent]
            linestyles += [0, 1]
            colors += [nextcolor, nextcolor]
            nextcolor += 1

        myplot.cdf(data, labels=labels, xlabel=XLABELS[stat],\
            linestyles=linestyles, colors=colors, filename='%s.pdf' % stat)


        


############### MAIN ###############

def main():
    # pick crawl date to analyze (for single-crawl analysis)
    date = args.date
    if not date:
        date = get_crawl_dates(args.profiles)[0]  # most recent

    crawl_dir = os.path.join(args.profiles, date)
    analyze_crawl(crawl_dir)


    # TODO:
    # - don't we just need to do this for a single crawl date?
    # - what sorts of stats are we interested in over time?
    # - should we save basic stats for every site (not just those w/ both protocols)?
        
    


if __name__ == '__main__':
    # set up command line args
    parser = argparse.ArgumentParser(description='Analyze a HAR file.')
    parser.add_argument('profiles', help='Directory of profiles to analyze.')
    parser.add_argument('-d', '--date', help='Crawl date to analyze (defaults to most recent)')
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='only print errors')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='print debug info. --quiet wins if both are present')
    args = parser.parse_args()

    
    # set up logging
    if args.quiet:
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        format = "%(levelname) -10s %(asctime)s %(module)s:%(lineno) -7s %(message)s",
        level = level
    )

    main()
