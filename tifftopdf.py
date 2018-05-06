#!/usr/bin/env python3
# file: tifftopdf.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Copyright © 2012-2017 R.F. Smith <rsmith@xs4all.nl>.
# SPDX-License-Identifier: MIT
# Created: 2012-06-29T21:02:55+02:00
# Last modified: 2018-04-16T22:39:06+0200
"""
Convert TIFF files to PDF format.

Using the utilities tiffinfo and tiff2pdf from the libtiff package.
"""

from functools import partial
import argparse
import concurrent.futures as cf
import logging
import os
import re
import subprocess
import sys

__version__ = '1.4'


def main(argv):
    """
    Entry point for tifftopdf.

    Arguments:
        argv: command line arguments
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--log',
        default='warning',
        choices=['debug', 'info', 'warning', 'error'],
        help="logging level (defaults to 'warning')"
    )
    parser.add_argument('-j', '--jpeg', help='use JPEG compresion', action="store_true")
    parser.add_argument(
        '-q', '--quality', help='JPEG compresion quality (default 85)', type=int, default=85
    )
    parser.add_argument('-v', '--version', action='version', version=__version__)
    parser.add_argument("files", metavar='file', nargs='+', help="one or more files to process")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log.upper(), None), format='%(levelname)s: %(message)s'
    )
    logging.debug('command line arguments = {}'.format(argv))
    logging.debug('parsed arguments = {}'.format(args))
    checkfor('tiffinfo', 255)
    checkfor(['tiff2pdf', '-v'])
    errmsg = 'conversion of {} failed, return code {}'
    func = tiffconv
    if args.jpeg:
        logging.info('using JPEG compression.')
        func = partial(tiffconv, jpeg=True, quality=args.quality)
    with cf.ThreadPoolExecutor(max_workers=os.cpu_count()) as tp:
        for fn, rv in tp.map(func, args.files):
            if rv == 0:
                logging.info('finished "{}"'.format(fn))
            else:
                logging.error(errmsg.format(fn, rv))


def checkfor(args, rv=0):
    """
    Ensure that a program necessary for using this script is available.

    Exits the program is the requirement cannot be found.

    Arguments:
        args: String or list of strings of commands. A single string may
            not contain spaces.
        rv: Expected return value from evoking the command.
    """
    if isinstance(args, str):
        if ' ' in args:
            raise ValueError('no spaces in single command allowed')
        args = [args]
    try:
        rc = subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if rc != rv:
            raise OSError
        logging.info('found required program "{}"'.format(args[0]))
    except OSError as oops:
        outs = 'required program "{}" not found: {}.'
        logging.error(outs.format(args[0], oops.strerror))
        sys.exit(1)


def tiffconv(fname, jpeg=False, quality=85):
    """
    Start a tiff2pdf process for given file.

    Arguments:
        name: Name of the tiff file to convert.
        jpeg: Use JPEG compression.
        quality: JPEG compression quality.

    Returns:
        A 2-tuple (input filename, tiff2pdf return value).
    """
    try:
        args = ['tiffinfo', fname]
        txt = subprocess.check_output(args, stderr=subprocess.DEVNULL)
        txt = txt.decode('utf-8').split()
        if 'Width:' not in txt:
            raise ValueError('no width in TIF')
        index = txt.index('Width:')
        width = float(txt[index + 1])
        length = float(txt[index + 4])
        try:
            index = txt.index('Resolution:')
            xres = float(txt[index + 1][:-1])
            yres = float(txt[index + 2])
        except ValueError:
            xres, yres = None, None
        outname = re.sub('\.tif{1,2}?$', '.pdf', fname, flags=re.IGNORECASE)
        program = ['tiff2pdf']
        if xres:
            args = [
                '-w',
                str(width / xres), '-l',
                str(length / xres), '-x',
                str(xres), '-y',
                str(yres), '-o', outname, fname
            ]
        else:
            args = ['-o', outname, '-z', '-p', 'A4', '-F', fname]
            ls = "no resolution in {}. Fitting to A4"
            logging.warning(ls.format(fname))
        if jpeg:
            args = program + ['-n', '-j', '-q', str(quality)] + args
        else:
            args = program + args
        logging.info('calling "{}"'.format(' '.join(args)))
        rv = subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info('created "{}"'.format(outname))
        return (fname, rv)
    except Exception as e:
        ls = 'starting conversion of "{}" failed: {}'
        logging.error(ls.format(fname, str(e)))
        return (fname, 0)


if __name__ == '__main__':
    main(sys.argv[1:])
