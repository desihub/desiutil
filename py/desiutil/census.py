# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
===============
desiutil.census
===============

Determine the number of files and size in DESI data file systems.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

def get_options(test_args=None):
    """Parse command-line options.

    Parameters
    ----------
    test_args : :class:`list`
        Override command-line arguments for testing purposes.

    Returns
    -------
    :class:`argparse.Namespace`
        A simple object containing the parsed options.
    """
    from sys import argv
    from os.path import basename
    from argparse import ArgumentParser
    from pkg_resources import resource_filename
    parser = ArgumentParser(description="Count number and size of DESI data files.",
                            prog=basename(argv[0]))
    parser.add_argument('-c', '--config-file', action='store', dest='config',
                        metavar='FILE', default=resource_filename('desiutil', 'data/census.yaml'),
                        help="Read configuration from FILE (default %(default)s).")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Print lots of extra information.")
    if test_args is None:  # pragma: no cover
        options = parser.parse_args()
    else:
        options = parser.parse_args(test_args)
    return options


def walk_error(e):
    """Handle errors reported by :func:`os.walk`.

    Parameters
    ----------
    e : :class:`OSError`
        The exception reported.
    """
    from .log import get_logger
    log = get_logger()
    log.error("OS strerror = {0.strerror}".format(e))
    log.error("OS errno = {0.errno}".format(e))
    log.error("filename = {0.filename}".format(e))
    if e.filename2 is not None:
        log.error("filename2 = {0.filename2}".format(e))
    return


def year(mtime, fy=True):
    """Convert a file's modification time into a year.

    Parameters
    ----------
    mtime : :class:`int` or :class:`float`
        File modification time as reported by :func:`os.stat`.
    fy : :class:`bool`, optional
        If ``True`` use Fiscal Year (FY) instead of calendar year.
        FY is defined to begin 1 October.

    Returns
    -------
    :class:`int`
        The year to which a file belongs.
    """
    from time import gmtime
    tm = gmtime(mtime)
    if fy and tm.tm_mon >= 10:
        return tm.tm_year + 1
    return tm.tm_year


def scan_directories(conf, data):
    """Scan the directories specified by the configuration file.

    Parameters
    ----------
    conf : :class:`dict`
        The configuration that applies to all directories.
    data : :class:`list`
        The specific directories to scan.

    Returns
    -------
    :class:`list`
        A list containing data structures summarizing data found.
    """
    import re
    from os import lstat, readlink, stat, walk
    from os.path import islink, join
    from .log import get_logger
    log = get_logger()
    filesystems = list()
    for f in conf['filesystems']:
        filesystems.append(re.compile(f))
    summary = list()
    for d in data:
        subdirs = list()
        dir_summary = {d['root']: dict()}
        log.debug('root = {root}'.format(**d))
        log.debug('category = {category}'.format(**d))
        log.debug('description = {description}'.format(**d))
        log.debug('group = {group}'.format(**d))
        if 'subdirs' in d:
            for sd in d['subdirs']:
                fsd = join(d['root'], sd['root'])
                subdirs.append(fsd)
                log.debug('subdir = {0}'.format(fsd))
                log.debug('description = {description}'.format(**sd))
                dir_summary[fsd] = dict()
        for dirpath, dirnames, filenames in walk(d['root'], topdown=True,
                                                 onerror=walk_error,
                                                 followlinks=False):
            log.debug("dirpath = {0}".format(dirpath))
            #
            # Detect symlinks that point to another filesystem so they
            # can be counted toward the total.
            #
            sum_files = dict()
            for dd in dirnames:
                fd = join(dirpath, dd)
                s = stat(fd)
                if s.st_gid != conf['gid'][d['group']]:
                    log.warning("{0} does not have correct group id!".format(fd))
                if islink(fd):
                    s = lstat(fd)
                    if s.st_gid != conf['gid'][d['group']]:
                        log.warning("{0} does not have correct group id!".format(fd))
                    rfd = readlink(fd)
                    y = year(s.st_mtime)
                    if y in sum_files:
                        sum_files[y]['number'] += 1
                        sum_files[y]['size'] += s.st_size
                    else:
                        sum_files[y] = {'number': 1, 'size': s.st_size}
                    if any([f.match(rfd) is not None for f in filesystems]):
                        log.info("Found filesystem link {0} -> {1}.".format(fd, rfd))
            for ff in filenames:
                #
                # os.stat() follows symlinks, but we also want to count the
                # symlink for counting inodes.
                #
                fff = join(dirpath, ff)
                s = stat(fff)
                if s.st_gid != conf['gid'][d['group']]:
                    log.warning("{0} does not have correct group id!".format(fff))
                y = year(s.st_mtime)
                if y in sum_files:
                    sum_files[y]['number'] += 1
                    sum_files[y]['size'] += s.st_size
                else:
                    sum_files[y] = {'number': 1, 'size': s.st_size}
                if islink(fff):
                    s = lstat(fff)
                    if s.st_gid != conf['gid'][d['group']]:
                        log.warning("{0} does not have correct group id!".format(fff))
                    rfff = readlink(fff)
                    y = year(s.st_mtime)
                    if y in sum_files:
                        sum_files[y]['number'] += 1
                        sum_files[y]['size'] += s.st_size
                    else:
                        sum_files[y] = {'number': 1, 'size': s.st_size}
                    log.info("Found file link {0} -> {1}.".format(fff, rfff))
            for y in sum_files:
                try:
                    dir_summary[d['root']][y]['number'] += sum_files[y]['number']
                    dir_summary[d['root']][y]['size'] += sum_files[y]['size']
                except KeyError:
                    dir_summary[d['root']][y] = {'number': sum_files[y]['number'],
                                                 'size': sum_files[y]['size']}
                for fsd in subdirs:
                    if dirpath.startswith(fsd):
                        try:
                            dir_summary[fsd][y]['number'] += sum_files[y]['number']
                            dir_summary[fsd][y]['size'] += sum_files[y]['size']
                        except KeyError:
                            dir_summary[fsd][y] = {'number': sum_files[y]['number'],
                                                   'size': sum_files[y]['size']}
        summary.append(dir_summary)
    return summary


def main():
    """Entry point for the :command:`desi_data_census` script.

    Returns
    -------
    :class:`int`
        Exit status that will be passed to :func:`sys.exit`.
    """
    import yaml
    from .log import get_logger, DEBUG, INFO
    options = get_options()
    #
    # Logging.
    #
    if options.verbose:
        log = get_logger(DEBUG)
        log.debug("Verbose logging is set.")
    else:
        log = get_logger()
    #
    # Configuration
    #
    log.info("Reading configuration from {0}.".format(options.config))
    with open(options.config) as y:
        config = yaml.load(y)
    log.debug(repr(config))
    summary = scan_directories(config['configuration'], config['data'])
    for s in summary:
        for root in s:
            for y in sorted(s[root].keys()):
                log.info('For FY{0:d}, {1} contains {2:d} bytes in {3:d} files.'.format(y, root, s[root][y]['size'], s[root][y]['number']))
    return 0


# * Directories to check:
#   - Imaging raw & reduced.
#   - spectro raw & reduced.
#   - work directories.
#   - non-footprint image data.
# * Check group id, readability.
# * Record mtime, size.  Convert mtime into just a year.
# * Shift to fiscal year.  FY starts in October.
# * Don't record filenames, just high-level directories.
# * Treat projecta as same system, follow symlinks to projecta
# * If a symlink is followed to another filesystem, os.walk() can't get back
#   to the original filesystem.
# * Symlinks to another subdirectory should only count as the symlink.  The
#   file itself belongs to the other subdirectory.
