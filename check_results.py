#!/usr/bin/env python

##
## Checks pickled HAR generator results, looking for possible errors.
##

import os
import sys
import argparse
import logging
import glob
import pickle
import pprint

from collections import defaultdict

sys.path.append(os.path.join(os.path.dirname(__file__), 'web-profiler'))
from webloader.chrome_loader import ChromeLoader
from webloader.loader import PageResult


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



def header(header_name):
    left_pad = (80 - len(header_name)) / 2
    right_pad = (80 - len(header_name)) / 2

    if len(header_name) % 2 == 1:
        right_pad += 1

    return '\n\n' + '='*left_pad + ' %s ' % header_name + '='*right_pad + '\n'

def field(name, value, level=0):
    return '\t'*level + '%s:\t%s\n' % (name, value)


def stats_for_loader(loader):
    num_urls = len(loader.page_results)
    num_loads = len(loader.urls)

    # how many pages succeeded? weren't accessible? failed?
    status_counts = defaultdict(int)
    for url, page_result in loader.page_results.iteritems():
        status_counts[page_result.status] += 1

    return num_urls, num_loads, status_counts


def pad_list(l, length):
    l += [None]*(length-len(l))


def main():
    loaders = defaultdict(dict)
    summary_text = ''

    # get the non-backup crawl directories; load loaders & store in dict
    for crawl_dir in glob.glob(args.profiles + '/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'):
        for uagent_dir in glob.glob(crawl_dir + '/*'):
            if os.path.isdir(uagent_dir):
                for har_result_pickle in glob.glob(uagent_dir + '/har_generator_results.pickle'):
                    date_string = os.path.split(crawl_dir)[1]
                    user_agent = os.path.split(uagent_dir)[1]

                    loader = None
                    with open(os.path.join(har_result_pickle), 'r') as f:
                        loader = pickle.load(f)
                    f.closed

                    loaders[date_string][user_agent] = loader






    ##
    ## summary of recent crawls
    ##
    recent_crawls = sorted(loaders.keys(), reverse=True)

    num_urls_dict = defaultdict(list)  # user agent -> list
    num_loads_dict = defaultdict(list)  # user agent -> list
    status_counts_dict = defaultdict(lambda: defaultdict(list))  # user agent -> status -> list
    crawls_so_far = 0
    for crawl_date in recent_crawls:
        # not all crawls might have the same set of user agents.
        # append null entries to any user agents this crawl didn't have

        for uagent in loaders[crawl_date]:
        
            num_urls, num_loads, status_counts =\
                stats_for_loader(loaders[crawl_date][uagent])

            pad_list(num_urls_dict[uagent], crawls_so_far)
            num_urls_dict[uagent].append(num_urls)

            pad_list(num_loads_dict[uagent], crawls_so_far)
            num_loads_dict[uagent].append(num_loads)

            for status, count in status_counts.iteritems():
                pad_list(status_counts_dict[uagent][status], crawls_so_far)
                status_counts_dict[uagent][status].append(count)

        crawls_so_far += 1



    summary_text += header('RECENT CRAWLS SUMMARY')
    summary_text += field('Dates', recent_crawls)
    summary_text += field('User Agents', '')
    for uagent in num_urls_dict.keys():
        summary_text += field(uagent, '', level=1)
        summary_text += field('# URLS', num_urls_dict[uagent], level=2)
        summary_text += field('# loads', num_loads_dict[uagent], level=2)

        for status, count in status_counts_dict[uagent].iteritems():
            summary_text += field(status, count, level=2)







    ##
    ## look for URLs that changed status this time
    ##
    last_crawl = recent_crawls[0]
    summary_text += header('STATUS CHANGES')
    summary_text += field('User Agents', '')
    for uagent, loader in loaders[last_crawl].iteritems():
        summary_text += field(uagent, '', level=1)
        previous_loader = loaders[recent_crawls[1]][uagent]

        for url in loader.page_results:
            status = loader.page_results[url].status
            previous_status = previous_loader.page_results[url].status

            if status != previous_status:
                summary_text += field(url, '%s -> %s' % (previous_status, status), level=2)




    ##
    ## per-page results
    ##
    summary_text += header('LAST CRAWL DETAILS')
    for uagent in loaders[last_crawl]:
        loader = loaders[last_crawl][uagent]
        summary_text += field(uagent, '', level=0)

        for url, page_result in loader.page_results.iteritems():
            summary_text += field(url, page_result.status, level=1)



    print summary_text







if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Check pickled HAR generator results for possible errors.')
    parser.add_argument('profiles', nargs='?', default='./profiles', help='Profile directory.')
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='only print errors')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='print debug info. --quiet wins if both are present')
    args = parser.parse_args()
    

    # set up logging
    setup_logging()
    
    main()
