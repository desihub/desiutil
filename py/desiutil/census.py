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


def scan_directories(conf, data):
    """Scan the directories specified by the configuration file.

    Parameters
    ----------
    conf : :class:`dict`
        The configuration that applies to all directories.
    data : :class:`list`
        The specific directories to scan.
    """
    from os import readlink, stat, walk
    from os.path import islink, join
    from .log import get_logger
    log = get_logger()
    for d in data:
        n_files = 0
        size_files = 0
        log.debug('root = {root}'.format(**d))
        log.debug('category = {category}'.format(**d))
        log.debug('description = {description}'.format(**d))
        log.debug('group = {group}'.format(**d))
        if 'subdirs' in d:
            log.debug(repr(d['subdirs']))
        for dirpath, dirnames, filenames in walk(d['root'], followlinks=True):
            log.debug("dirpath = {0}".format(dirpath))
            #
            # We want to follow *some* links, but not all.  If a link
            # is to another filesystem, we want to include that data.
            # Otherwise assume the link is an alias or data copied from
            # a previous release.
            #
            for dd in dirnames:
                fd = join(dirpath, dd)
                s = stat(fd)
                if dd.st_gid != conf['gid'][d['group']]
                    log.warning("{0} does not have correct group id!".format(fd))
                if islink(fd):
                    rfd = readlink(fd)
                    if not any([rfd.startswith(l) for l in conf['descend']]):
                        log.info("Skipping {0} -> {1}.".format(fd, rfd))
                        del dirnames[dirnames.index(dd)]
            n_files += len(filenames)
            s_files = 0
            for ff in filenames:
                fff = join(dirpath, ff)
                s = stat(fff)
                if s.st_gid != conf['gid'][d['group']]
                    log.warning("{0} does not have correct group id!".format(fff))
                s_files += s.st_size
            size_files += s_files
        log.info('{0} contains {1:d} bytes in {2:d} files.'.format(d['root'], size_files, n_files))
    return


def main():
    """Entry point for the :command:`desi_data_census` script.

    Returns
    -------
    :class:`int`
        Exit status that will be passed to :func:`sys.exit`.
    """
    import yaml
    from .log import get_logger, DEBUG, INFO, WARNING
    options = get_options()
    #
    # Logging.
    #
    if options.verbose:
        log = get_logger(DEBUG)
        log.debug("Verbose logging is set.")
    else:
        log = get_logger(WARNING)
    #
    # Configuration
    #
    log.info("Reading configuration from {0}.".format(options.config))
    with open(options.config) as y:
        config = yaml.load(y)
    log.debug(repr(config))
    scan_directories(config['configuration'], config['data'])
    return 0


# * Directories to check:
#   - Imaging raw & reduced.
#   - spectro raw & reduced.
#   - work directories.
#   - non-footprint image data.
# * Check group id, readability.
# * Record mtime, size.
# * Shift to fiscal year.
# * Don't record filenames, just high-level directories.
# * Treat projecta as same system, follow symlinks to projecta
