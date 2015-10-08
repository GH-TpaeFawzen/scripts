#!/usr/bin/env python3
# vim:fileencoding=utf-8:ft=python
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Last modified: 2015-10-08 22:17:49 +0200
#
# To the extent possible under law, Roland Smith has waived all copyright and
# related or neighboring rights to vid2mkv.py. This work is published from the
# Netherlands. See http://creativecommons.org/publicdomain/zero/1.0/

"""Convert all video files given on the command line to Theora/Vorbis streams
in a Matroska container using ffmpeg."""

__version__ = '1.2.1'

from concurrent.futures import ThreadPoolExecutor
from functools import partial
import argparse
import logging
import os
import subprocess
import sys


def main(argv):
    """
    Entry point for vid2mkv.

    Arguments:
        argv: Command line arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-q', '--videoquality', type=int, default=6,
                        help='video quality (0-10, default 6)')
    parser.add_argument('-a', '--audioquality', type=int, default=3,
                        help='audio quality (0-10, default 3)')
    parser.add_argument('--log', default='warning',
                        choices=['debug', 'info', 'warning', 'error'],
                        help="logging level (defaults to 'warning')")
    parser.add_argument('-v', '--version',
                        action='version',
                        version=__version__)
    parser.add_argument("files", metavar='file', nargs='+',
                        help="one or more files to process")
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log.upper(), None),
                        format='%(levelname)s: %(message)s')
    logging.info('command line arguments = {}'.format(argv))
    logging.info('parsed arguments = {}'.format(args))
    checkfor(['ffmpeg', '-version'])
    starter = partial(runencoder, vq=args.videoquality,
                      aq=args.audioquality)
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as tp:
        convs = tp.map(starter, args.files)
    convs = [(fn, rv) for fn, rv in convs if rv != 0]
    for fn, rv in convs:
        print('Conversion of {} failed, return code {}'.format(fn, rv))


def checkfor(args, rv=0):
    """
    Make sure that a program necessary for using this script is available.
    If the required utility is not found, this function will exit the program.

    Arguments:
        args: String or list of strings of commands. A single string may not
            contain spaces.
        rv: Expected return value from evoking the command.
    """
    if isinstance(args, str):
        if ' ' in args:
            raise ValueError('no spaces in single command allowed')
        args = [args]
    try:
        rc = subprocess.call(args, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        if rc != rv:
            raise OSError
        logging.info('found required program "{}"'.format(args[0]))
    except OSError as oops:
        outs = 'required program "{}" not found: {}.'
        logging.error(outs.format(args[0], oops.strerror))
        sys.exit(1)


def runencoder(fname, vq, aq):
    """
    Use ffmpeg to convert a video file to Theora/Vorbis streams in a Matroska
    container.

    Arguments:
        fname: Name of the file to convert.
        vq : Video quality. See ffmpeg docs.
        aq: Audio quality. See ffmpeg docs.

    Returns:
        (fname, return value)
    """
    basename, ext = os.path.splitext(fname)
    known = ['.mp4', '.avi', '.wmv', '.flv', '.mpg', '.mpeg', '.mov', '.ogv',
             '.mkv', '.webm']
    if ext.lower() not in known:
        ls = 'file "{}" has unknown extension, ignoring it.'.format(fname)
        logging.warning(ls)
        return (fname, 0)
    ofn = basename + '.mkv'
    args = ['ffmpeg', '-i', fname, '-c:v', 'libtheora', '-q:v', str(vq),
            '-c:a', 'libvorbis', '-q:a', str(aq), '-sn', '-y', ofn]
    logging.info('starting conversion of "{}" to "{}"'.format(fname, ofn))
    rv = subprocess.call(args, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    logging.info('finished "{}"'.format(ofn))
    return fname, rv


if __name__ == '__main__':
    main(sys.argv[1:])
