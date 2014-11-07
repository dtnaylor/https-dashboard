#!/usr/bin/env python
import argparse
import requests
import sys
import urlparse


def make_url(url, protocol, port=None):
    # make sure it's a complete URL to begin with, or urlparse can't parse it
    if '://' not in url:
        url = 'http://%s' % url
    comps = urlparse.urlparse(url)

    new_netloc = comps.netloc
    if port:
        new_netloc = new_netloc.split(':')[0]
        new_netloc = '%s:%s' % (new_netloc, port)

    new_comps = urlparse.ParseResult(scheme=protocol, netloc=new_netloc,\
        path=comps.path, params=comps.params, fragment=comps.fragment,\
        query=comps.query)

    return urlparse.urlunparse(new_comps)


def main():
    '''Input: a list of URLs.
       Output: same list of URLs, but one HTTP and one HTTPS
    '''
    with open(args.infile, 'r') as inf:
        with open(args.outfile, 'w') as outf:
            for line in inf:
                outf.write('%s\n' % make_url(line.strip(), 'http'))
                outf.write('%s\n' % make_url(line.strip(), 'https'))
        outf.closed
    inf.closed


if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Makes a list of URLs where each URL has an HTTP and an HTTPS version.')
    parser.add_argument('infile', help='Input URL file.')
    parser.add_argument('outfile', help='Output URL file.')
    args = parser.parse_args()

    main()
