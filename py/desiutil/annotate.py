# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
=================
desiutil.annotate
=================

Tools for adding units and comments to FITS files.
"""
import csv
import os
import sys
from argparse import ArgumentParser
from astropy.io import fits
from . import __version__ as desiutilVersion
from .log import get_logger, DEBUG


log = None


def csv_unit_column(header, comment=False):
    """Find the column that contains unit descriptions, or comments.

    Parameters
    ----------
    header : iterable
        The column names from a CSV file.
    comment : :class:`bool`, optional
        If ``True``, look for a column matching 'comment'.

    Returns
    -------
    :class:`int`
        The index of `header` that matches.

    Raises
    ------
    IndexError
        If no match was found.
    """
    search = ('unit', )
    if comment:
        search = ('comment', 'description')
    for i, column in enumerate(header):
        for s in search:
            if s in column.lower():
                return i
    raise IndexError(f"No column matching '{search[0]}' found!")


def csv_units(filename):
    """Parse a CSV file that contains column names and units and optionally comments.

    Table column names are assumed to be in the first column of the CSV file.
    Any column with the name "Unit(s)" (case-insensitive) is assumed to contain FITS-style units.
    Any column with the name "Comment(s)" (case-insensitive) is assumed to be the comment.

    Parameters
    ----------
    filename : :class:`str` or :class:`pathlib.Path`
        Read column definitions from `filename`.

    Returns
    -------
    :class:`tuple`
        A tuple containing two :class:`dict` objects for units and comments.
        If no comments are detected, the comments :class:`dict` will be empty.

    Raises
    ------
    ValueError
        If `filename` does not at least contain a "unit" column.
    """
    units = dict()
    comments = dict()
    header = None
    data = list()
    log.debug("filename = '%s'", filename)
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if header is None:
                header = row
            else:
                data.append(row)
    log.debug(header)
    try:
        u = csv_unit_column(header)
    except IndexError:
        raise ValueError(f"{filename} does not have a unit column!")
    try:
        c = csv_unit_column(header, comment=True)
    except IndexError:
        c = None
    for row in data:
        log.debug("units['%s'] = '%s'", row[0], row[u])
        units[row[0]] = row[u]
        if c:
            log.debug("comments['%s'] = '%s'", row[0], row[c])
            comments[row[0]] = row[c]
    return (units, comments)


def _options():
    """Parse command-line options.
    """
    parser = ArgumentParser(description="Add units or comments to a FITS file.",
                            prog=os.path.basename(sys.argv[0]))
    parser.add_argument('-c', '--comments', action='store', dest='comments', metavar='COMMENTS',
                        help="COMMENTS should have the form COLUMN='comment':COLUMN='comment'.")
    parser.add_argument('-C', '--csv', action='store', dest='csv', metavar='CSV',
                        help="Read annotations from CSV file.")
    parser.add_argument('-e', '--extension', dest='extension', action='store', metavar='EXT', default='1',
                        help="Update FITS extension EXT, which can be a number or an EXTNAME. If not specified, HDU 1 will be updated, which is standard for simple binary tables.")
    parser.add_argument('-t', '--test', dest='test', action='store_true',
                        help='Test mode; show what would be done but do not change any files.')
    parser.add_argument('-u', '--units', action='store', dest='units', metavar='UNITS',
                        help="UNITS should have the form COLUMN='unit':COLUMN='unit'.")
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='Print extra debugging information.')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + desiutilVersion)
    options = parser.parse_args()
    return options


def main():
    """Entry-point for command-line scripts.

    Returns
    -------
    :class:`int`
        An integer suitable for passing to :func:`sys.exit`.
    """
    global log
    options = _options()
    if options.test or options.verbose:
        log = get_logger(DEBUG)
    else:
        log = get_logger()
    if options.csv:
        units, comments = csv_units(options.csv)
    else:
        if options.units:
            units = dict(tuple(c.split('=')) for c in options.units.split(':'))
        else:
            log.warning("No units have been specified!")
            units = dict()
        if options.comments:
            comments = dict(tuple(c.split('=')) for c in options.comments.split(':'))
        else:
            log.debug("No comments have been specified.")
            comments = dict()
    log.debug(units)
    log.debug(comments)
    return 0
