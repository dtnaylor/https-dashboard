#!/usr/bin/env python

import pprint
import requests
from collections import defaultdict

REPS_PER_URL = 10

URLS = [
'http://google.com',
'https://google.com',
'http://youtube.com',
'https://youtube.com',
'http://cnn.com',
'https://cnn.com',
]


def check(url, headers):
    try:
        response = requests.get(url, timeout=30,\
            headers=headers, verify=False) 
    except requests.exceptions.ConnectionError as e:
        return '%s\tCONNECT ERROR' % url
    except requests.exceptions.Timeout as e:
        return '%s\tTIMEOUT' % url
    except Exception as e:
        return '%s\tERROR' % url

    result = '%s    [%d, %s]' % (url, response.status_code, response.url)

    for r in response.history:
        result += ', [%d, %s]' % (r.status_code, r.url)

    return result

def run(headers):
    results = defaultdict(list)
    for i in range(REPS_PER_URL):
        for url in URLS:
            results[url].append(check(url, headers))

    return results



def main():
    mobile_headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19'}
    desktop_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.94 Safari/537.36'}


    print '\n\nMOBILE:\n'
    pprint.pprint(dict(run(mobile_headers)))
    
    print '\n\nDESKTOP:\n'
    pprint.pprint(dict(run(desktop_headers)))


if __name__ == '__main__':
    main()
