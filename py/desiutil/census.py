# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
===============
desiutil.census
===============

Determine the number of files and size in DESI data file systems.

Notes
-----

* Directories to check:

  - Imaging raw & reduced.
  - spectro raw & reduced.
  - Work directories.
  - Non-Footprint image data.

* Check group id, readability.
* Count number of files and size.
* Extract year from mtime. Shift to fiscal year.  FY starts in October.
* Don't record filenames, just high-level directories.
* Treat projecta as same system, follow symlinks to projecta
* If a symlink is followed to another filesystem, :func:`os.walk` can't get back
  to the original filesystem.
* Symlinks to another subdirectory should only count as the symlink.  The
  file itself belongs to the other subdirectory.
* Physical directories count toward inode and size total.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class ScannedFile(object):
    """Simple object to store results of a file scan.

    Attributes
    ----------
    filename : :class:`str`
        Name of the file.
    size : :class:`int`
        Size in bytes of the file.
    year : :class:`int`
        Year the file was modified.
    islink : :class:`bool`
        Is the file a symbolic link?
    isexternal : :class:`bool`
        If the file is a symbolic link, does it link outside the tree being
        scanned?
    linkname : :class:`str`
        If the file is a symbolic link, it points to this file.
    linksize : :class:`int`
        If the file is a symbolic link, this is the size of the link *itself*,
        and the size attribute is the size of the file it *points to*.
    linkyear : :class:`int`
        Year the link *itself* was modified.
    """
    def __init__(self, filename, size, year):
        self.filename = filename
        self.size = size
        self.year = year
        self.islink = False
        self.isexternal = False
        self.linkname = None
        self.linksize = None
        self.linkyear = None
        return


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
    parser.add_argument('-o', '--output', action='store', metavar='FILE',
                        default='desi_data_census.csv',
                        help="Output CSV file (default ./%(default)s).")
    parser.add_argument('-r', '--raw-output', action='store', dest='raw',
                        metavar='FILE', default='desi_data_census.yml',
                        help="Dump raw data to FILE (default ./%(default)s)")
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
    from collections import OrderedDict
    from os import walk
    from os.path import basename, dirname, isdir, join
    from .log import get_logger
    log = get_logger()
    summary = list()
    for d in data:
        subdirs = list()
        dir_summary = OrderedDict()
        dir_summary[d['root']] = dict()
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
        auxilliary_links = dict()
        for dirpath, dirnames, filenames in walk(d['root'], topdown=True,
                                                 onerror=walk_error,
                                                 followlinks=False):
            sum_files, ext = scan_directory(dirpath, dirnames, filenames,
                                            conf['gid'][d['group']])
            for y in sum_files:
                try:
                    dir_summary[d['root']][y]['number'] += sum_files[y]['number']
                    dir_summary[d['root']][y]['size'] += sum_files[y]['size']
                except KeyError:
                    dir_summary[d['root']][y] = {'number': sum_files[y]['number'],
                                                 'size': sum_files[y]['size']}
                for fsd in subdirs:
                    if in_path(fsd, dirpath):
                        try:
                            dir_summary[fsd][y]['number'] += sum_files[y]['number']
                            dir_summary[fsd][y]['size'] += sum_files[y]['size']
                        except KeyError:
                            dir_summary[fsd][y] = {'number': sum_files[y]['number'],
                                                   'size': sum_files[y]['size']}
            for key in ext:
                log.debug("External link detected: {0} -> {1}.".format(key, ext[key]))
                for primary, aux in conf['filesystems'].items():
                    log.debug("primary = {0}; aux = {1}".format(primary, aux))
                    for k in subdirs + [d['root']]:
                        if ext[key].startswith(aux) and in_path(k, ext[key].replace(aux, primary)):
                            log.info("Found link to auxilliary filesystem: {0} -> {1}.".format(key, ext[key]))
                            if isdir(key):
                                log.info("Found link to directory on auxilliary filesystem: {0} -> {1}. Data belongs to {2}.".format(key, ext[key], k))
                                if ext[key] in auxilliary_links:
                                    auxilliary_links[ext[key]].append(k)
                                else:
                                    auxilliary_links[ext[key]] = [k]
                            else:
                                log.info("Found link to single file on auxilliary filesystem: {0} -> {1}. Data belongs to {2}.".format(key, ext[key], k))
                                f = scan_file(dirname(ext[key]), basename(ext[key]), conf['gid'][d['group']])
                                try:
                                    dir_summary[k][f.year]['number'] += 1
                                    dir_summary[k][f.year]['size'] += f.size
                                except KeyError:
                                    dir_summary[k][f.year] = {'number': 1, 'size': f.size}
                if ext[key] in auxilliary_links:
                    if len(auxilliary_links[ext[key]]) > 2:
                        log.warning("Extraneous auxilliary links found for {0} -> {1}.".format(key, ext[key]))
                    if auxilliary_links[ext[key]][1] != d['root']:
                        log.warning("Malformed auxilliary link found for {0} -> {1}.".format(key, ext[key]))
        #
        # Check auxilliary links *after* the first os.walk() has completed.
        #
        for aux_root in auxilliary_links:
            aux_fsd = auxilliary_links[aux_root][0]
            for aux_dirpath, aux_dirnames, aux_filenames in walk(aux_root, topdown=True, onerror=walk_error, followlinks=False):
                sum_files, ext = scan_directory(aux_dirpath, aux_dirnames, aux_filenames, conf['gid'][d['group']])
                for aux_y in sum_files:
                    try:
                        dir_summary[d['root']][aux_y]['number'] += sum_files[aux_y]['number']
                        dir_summary[d['root']][aux_y]['size'] += sum_files[aux_y]['size']
                    except KeyError:
                        dir_summary[d['root']][aux_y] = {'number': sum_files[aux_y]['number'],
                                                         'size': sum_files[aux_y]['size']}
                    try:
                        dir_summary[aux_fsd][aux_y]['number'] += sum_files[aux_y]['number']
                        dir_summary[aux_fsd][aux_y]['size'] += sum_files[aux_y]['size']
                    except KeyError:
                        dir_summary[aux_fsd][aux_y] = {'number': sum_files[aux_y]['number'],
                                                       'size': sum_files[aux_y]['size']}
        summary.append(dir_summary)
    return summary


def scan_directory(dirpath, dirnames, filenames, gid):
    """Count number and size of files in a single directory hierarchy.

    Parameters
    ----------
    dirpath : :class:`str`
        Current directory, returned by :func:`os.walk`.
    dirnames : :class:`list`
        List of directories in `dirpath`.
    filenames : :class:`list`
        List of files in `dirpath`.
    gid : :class:`int`
        Group ID number that should be associated with this directory.

    Returns
    -------
    :func:`tuple`
        A tuple containing two dictionaries: the summary results organized
        by year, and a summary of links to external directories.
    """
    from .log import get_logger
    log = get_logger()
    summary = dict()
    external = dict()
    log.debug("dirpath = {0}".format(dirpath))
    for k in dirnames + filenames:
        f = scan_file(dirpath, k, gid)
        if f.isexternal:
            external[f.filename] = f.linkname
        else:
            if f.year in summary:
                summary[f.year]['number'] += 1
                summary[f.year]['size'] += f.size
            else:
                summary[f.year] = {'number': 1, 'size': f.size}
        if f.islink:
            if f.linkyear in summary:
                summary[f.linkyear]['number'] += 1
                summary[f.linkyear]['size'] += f.linksize
            else:
                summary[f.linkyear] = {'number': 1, 'size': f.linksize}
    return (summary, external)


def scan_file(dirpath, filename, gid):
    """Analyze a single file or directory.

    Parameters
    ----------
    dirpath : :class:`str`
        Current directory, returned by :func:`os.walk`.
    filename : :class:`str`
        Base name of current file.
    gid : :class:`int`
        Group ID number that should be associated with this directory.

    Returns
    -------
    :class:`ScannedFile`
        A simple object containing the metadata relating to the file.
    """
    from os import lstat, stat
    from os.path import islink, join, realpath
    from .log import get_logger
    log = get_logger()
    fd = join(dirpath, filename)
    log.debug("os.stat('{0}')".format(fd))
    s = stat(fd)
    if s.st_gid != gid:
        log.warning("{0} does not have correct group id!".format(fd))
    f = ScannedFile(fd, s.st_size, year(s.st_mtime))
    if islink(fd):
        f.islink = True
        log.debug("os.lstat('{0}')".format(fd))
        s = lstat(fd)
        if s.st_gid != gid:
            log.warning("{0} does not have correct group id!".format(fd))
        f.linkname = realpath(fd)
        f.linksize = s.st_size
        f.linkyear = year(s.st_mtime)
        if in_path(dirpath, f.linkname):
            log.debug("Found internal link {0.filename} -> {0.linkname}.".format(f))
        else:
            f.isexternal = True
            log.debug("Found external link {0.filename} -> {0.linkname}.".format(f))
    return f


def in_path(root, path):
    """Check if `path` is in the same directory hierarchy as `root`.

    Parameters
    ----------
    root : :class:`str`
        Root directory.
    path : :class:`str`
        Filename, could be a file or a directory.

    Returns
    -------
    :class:`bool`
        ``True`` if `path` is in `root`.
    """
    from os.path import commonpath
    return commonpath([root, path]).startswith(root)


def output_csv(summary, filename):
    """Convert data into CSV file.

    Parameters
    ----------
    summary : :class:`list`
        A data structure.
    filename : :class:`str`
        Name of the file to write to.

    Returns
    -------
    :class:`list`
        The data written to the CSV file, as a list of rows.
    """
    import csv
    directories = list()
    years = set()
    for s in summary:
        for root in s:
            directories.append(root)
            years.update(set(s[root].keys()))
    number = dict()
    size = dict()
    for d in directories:
        number[d] = dict()
        size[d] = dict()
        for y in years:
            number[d][y] = 0
            size[d][y] = 0
    for s in summary:
        for root in s:
            for y in sorted(years):
                try:
                    previous_number = number[root][y-1]
                except KeyError:
                    previous_number = 0
                try:
                    previous_size = size[root][y-1]
                except KeyError:
                    previous_size = 0
                try:
                    this_number = s[root][y]['number']
                except KeyError:
                    this_number = 0
                try:
                    this_size = s[root][y]['size']
                except KeyError:
                    this_size = 0
                number[root][y] = this_number + previous_number
                size[root][y] = this_size + previous_size
    data = [['Directory'] + ['FY{0:d} Number,FY{0:d} Size'.format(y) for y in sorted(years)]]
    for d in directories:
        row = [d]
        for y in sorted(years):
            row.append(str(number[d][y]))
            row.append(str(size[d][y]))
        data.append(row)
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)
    return data


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
    with open(options.raw, 'w') as y:
        yaml.dump(summary, y, default_flow_style=False)
    data = output_csv(summary, options.output)
    return 0
