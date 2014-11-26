#!/usr/bin/env python

##
## Given a directory of site screenshots, prepare thumbnails and rename files.
##  INPUT: directory of files named http---site.com_trial0.png
##  OUTPUT: same directory, files now named:
##      site.com-http.png
##      site.com-http_thumb.png
##

import os
import sys
import argparse
import logging
import re
import glob

from PIL import Image, ImageDraw


THUMBNAIL_SIZE = (200, 300)
TOOTH_SIZE = 20


def process_image_file(image_file):
    # first rename image
    img_dir, img_name = os.path.split(image_file)
    basename, ext = os.path.splitext(img_name)
    match = re.search(r'(http|https)---(.*)_trial[0-9]+', basename)
    if not match:
        logging.warn('Image name not in expected format: %s', image_file)
    protocol = match.group(1)
    site = match.group(2)

    img_name = '%s-%s%s' % (site, protocol, ext)
    img_path = os.path.join(img_dir, img_name)
    thumb_name = '%s-%s_thumb%s' % (site, protocol, ext)
    thumb_path = os.path.join(img_dir, thumb_name)

    os.rename(image_file, img_path)

    # now prepare thumbnail
    im = Image.open(img_path)

    # crop to thumbnail aspect ratio
    thumb_ratio = THUMBNAIL_SIZE[0]/float(THUMBNAIL_SIZE[1])
    img_ratio = im.size[0]/float(im.size[1])
    if img_ratio < thumb_ratio:
        im = im.crop((
            0,  # left\
            0,  # upper\
            im.size[0],  # right\
            int(im.size[0]*THUMBNAIL_SIZE[1]/float(THUMBNAIL_SIZE[0]))  # lower\
        ))
    elif img_ratio > thumb_ratio:
        im = im.crop((
            0,  # left\
            0,  # upper\
            int(im.size[1]*THUMBNAIL_SIZE[0]/float(THUMBNAIL_SIZE[1])),  # right\
            im.size[1]  # lower\
        ))

    # scale image down to thumbnail size
    im.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)

    # draw jagged path on bottom edge to indicate we cut some content
    coords = []
    for i in range(THUMBNAIL_SIZE[0]/TOOTH_SIZE + 1):
        y = THUMBNAIL_SIZE[1] if i%2==0 else THUMBNAIL_SIZE[1]-TOOTH_SIZE
        coords.append((i*TOOTH_SIZE, y)) 
    canvas = ImageDraw.Draw(im)
    canvas.polygon(coords, fill="#FFFFFF")

    im.save(thumb_path)


def process_image_dir(image_dir):
    for image_file in glob.glob(image_dir + '/*'):
        process_image_file(image_file)



def main():
    # for testing; in "real life", manager imports and calls these functions
    if args.dir:
        process_image_dir(args.dir)

    if args.file:
        process_image_file(args.file)



if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Process site screenshots.')
    parser.add_argument('-d', '--dir', help='Test dir')
    parser.add_argument('-f', '--file', help='Test image file')
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
    config = {
        'format' : "%(levelname) -10s %(asctime)s %(module)s:%(lineno) -7s %(message)s",
        'level' : level
    }
    logging.basicConfig(**config)
    
    main()
