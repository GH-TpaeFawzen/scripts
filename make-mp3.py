#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# $Date$
#
# To the extent possible under law, Roland Smith has waived all copyright and
# related or neighboring rights to make-mp3.py. This work is published from
# the Netherlands. See http://creativecommons.org/publicdomain/zero/1.0/

"""Encodes WAV files from cdparanoia to MP3 format with variable
bitrate.  Processing is done in parallel using as many subprocesses as
the machine has cores. Title and song information is gathered from a
text file called titles.
"""

from __future__ import division, print_function

__version__ = '$Revision$'[11:-2]

import os
import sys
import subprocess
from multiprocessing import cpu_count
from time import sleep
from checkfor import checkfor


def trackdata(fname='titels'):
    """Read the data describing the tracks from a text file.

    Arguments:
    fname -- name of the text file describing the tracks.

    This file has the following format:

      album title
      artist
      01 title of 1st song
      ..
      14 title of 14th song

    Returns:
    A list of tuples. Each tuple contains the track number, title of
    the track, name of the artist, name of the album, input file name
    and output file name.
    """
    tracks = []
    try:
        with open(fname, 'r') as tf:
            lines = tf.readlines()
    except IOError:
        return tracks
    album = lines.pop(0).strip()
    artist = lines.pop(0).strip()
    for l in lines:
        words = l.split()
        if not words:
            continue
        num = int(words.pop(0))
        # These are the default WAV file names generated by cdparanoia.
        ifname = 'track{:02d}.cdda.wav'.format(num)
        if os.access(ifname, os.R_OK):
            ofname = 'track{:02d}.mp3'.format(num)
            title = ' '.join(words)
            tracks.append((num, title, artist, album, ifname, ofname))
    return tracks


def startmp3(tinfo):
    """Use the lame(1) program to convert the music file to MP3 format.

    Arguments:
    tinfo -- a tuple containing the track number, title of the track,
    name of the artist, name of the album, input file name and output
    file name.

    Returns:
    A tuple containing the output filename and the Popen object
    for the running conversion.
    """
    num, title, artist, album, ifname, ofname = tinfo
    args = ['lame', '-S', '--preset', 'standard', '--tt', title, '--ta',
            artist, '--tl', album, '--tn', '{:02d}'.format(num),
            ifname, ofname]
    with open(os.devnull, 'w') as bb:
        p = subprocess.Popen(args, stdout=bb, stderr=bb)
    print('Start processing "{}" as {}'.format(title, ofname))
    return (ofname, p)


def manageprocs(proclist):
    """Check a list of subprocesses for processes that have ended and
    remove them from the list.
    """
    for it in proclist:
        fn, pr = it
        result = pr.poll()
        if result is not None:
            proclist.remove(it)
            if result == 0:
                print('Finished processing', fn)
            else:
                s = 'The conversion of {} exited with error code {}.'
                print(s.format(fn, result))
    sleep(0.5)


def main(argv):
    """Main program."""
    checkfor(['lame', '--help'])
    procs = []
    tracks = trackdata()
    if not tracks:
        print('No tracks found.')
        binary = os.path.basename(argv[0])
        print("{} version {}".format(binary, __version__), file=sys.stderr)
        print("Usage: {}".format(binary), file=sys.stderr)
        print("In a directory where a file 'titels' and WAV files are present",
              file=sys.stderr)
        sys.exit(1)
    maxprocs = cpu_count()
    for track in tracks:
        while len(procs) == maxprocs:
            manageprocs(procs)
        procs.append(startmp3(track))
    while len(procs) > 0:
        manageprocs(procs)


if __name__ == '__main__':
    main(sys.argv)
