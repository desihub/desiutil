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
import yaml
from astropy.io import fits
from astropy.table import Table, QTable
from astropy.units import UnitConversionError
from . import __version__ as desiutilVersion
from .log import get_logger, DEBUG


log = None


def find_column_name(columns, prefix=('unit', )):
    """Find the column that contains unit descriptions, or comments.

    Parameters
    ----------
    columns : iterable
        The column names from a CSV or similar file.
    prefix : :class:`tuple`, optional
        Search for a column matching one or more items in `prefix`.
        The search is case-insensitive.

    Returns
    -------
    :class:`int`
        The index of `columns` that matches.

    Raises
    ------
    IndexError
        If no match was found.
    """
    for i, column in enumerate(columns):
        for s in prefix:
            if s in column.lower():
                return i
    raise IndexError(f"No column matching '{prefix[0]}' found!")


def find_key_name(data, prefix=('unit', )):
    """
    Parameters
    ----------
    data : :class:`dict`
        A dictionary resulting from a parsed YAML file.
    prefix : :class:`tuple`, optional
        Search for a column matching one or more items in `prefix`.
        The search is case-insensitive.

    Returns
    -------
    :class:`str`
        The key of `data` that matches.

    Raises
    ------
    KeyError
        If no match was found.
    """
    for key in data.keys():
        for s in prefix:
            if s in key.lower():
                return key
    raise KeyError(f"No key matching '{prefix[0]}' found!")


def load_csv_units(filename):
    """Parse a CSV file that contains column names and units and optionally comments.

    Table column names are assumed to be in the first column of the CSV file.
    Any column with the name "Unit(s)" (case-insensitive) is assumed to contain FITS-style units.
    Any column with the name "Comment(s)" (case-insensitive) or "Description(s)" is assumed to be the comment.

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
        u = find_column_name(header)
    except IndexError:
        raise ValueError(f"{filename} does not have a unit column!")
    try:
        c = find_column_name(header, prefix=('comment', 'description'))
    except IndexError:
        c = None
    for row in data:
        log.debug("units['%s'] = '%s'", row[0], row[u])
        units[row[0]] = row[u]
        if c:
            log.debug("comments['%s'] = '%s'", row[0], row[c])
            comments[row[0]] = row[c]
    return (units, comments)


def load_yml_units(filename):
    """Parse a YAML file that contains column names and units and optionally comments.

    The YAML file should contain a dictionary with a keyword like 'units' and,
    optionally, a keyword like 'comments' or 'description.

    For backwards-compatibility, the YAML file can be simply a dictionary
    containing column names.

    Parameters
    ----------
    filename : :class:`str` or :class:`pathlib.Path`
        Read column definitions from `filename`.

    Returns
    -------
    :class:`tuple`
        A tuple containing two :class:`dict` objects for units and comments.
        If no comments are detected, the comments :class:`dict` will be empty.
    """
    comments = dict()
    # log.debug("y = yaml.safe_load('%s')", filename)
    with open(filename, newline='') as f:
        y = yaml.safe_load(f)
    try:
        u = find_key_name(y)
    except KeyError:
        log.warning(f"{filename} does not have a unit column, assuming keys are columns!")
        u = None
    try:
        c = find_key_name(y, prefix=('comment', 'description'))
    except KeyError:
        c = None
    if u:
        units = y[u]
    else:
        units = y
    if c:
        comments = y[c]
    return (units, comments)


def annotate_table(table, units, inplace=False):
    """Add annotations to `table`.

    Parameters
    ----------
    table : :class:`astropy.table.Table` or :class:`astropy.table.QTable`
        A data table.
    units : :class:`dict`
        Mapping of table columns to units.
    inplace : :class:`bool`, optional
        If ``True``, modify `table` directly instead of returning a copy.

    Returns
    -------
    :class:`astropy.table.Table`
        An updated version of `table`.

    Notes
    -----
    Currently :class:`~astropy.table.Table` does not support the concept
    of column-specific comments, especially in a way where the comments
    could be written to a file. If this ever changes, this function could
    be extended to add comments.
    """
    if inplace:
        t = table
    else:
        if isinstance(table, QTable):
            t = QTable(table)  # copy=True is the default.
        else:
            t = Table(table)
    for colname in t.colnames:
        if colname not in units:
            log.info("Column '%s' not found in units argument.", colname)
    for column in units:
        if column in t.colnames:
            if len(units[column]) > 0:
                try:
                    log.debug("t['%s'].unit = '%s'", column, units[column])
                    t[column].unit = units[column]
                except AttributeError:
                    #
                    # Can't change .unit if it is already set. Try to convert.
                    #
                    try:
                        log.debug("t.replace_column('%s', t['%s'].to('%s'))", column, column, units[column])
                        t.replace_column(column, t[column].to(units[column]))
                    except UnitConversionError:
                        log.error("Cannot add or replace unit '%s' to column '%s'!", units[column], column)
            else:
                log.debug("Not setting blank unit for column '%s'.", column)
        else:
            log.debug("Column '%s' not present in table.", column)
    return t


def annotate(filename, extension, units=None, comments=None):
    """Add annotations to `filename`.

    If `units` or `comments` is an empty dictionary, it will be ignored.

    Parameters
    ----------
    filename : :class:`str`
        Name of FITS file.
    extension : :class:`str` or :class:`int
        Name or number of extension in `filename`.
    units : :class:`dict`, optional
        Mapping of table columns to units.
    comments : :class:`dict`, optional
        Mapping of table columns to comments.

    Returns
    -------
    :class:`astropy.io.fits.HDUList`
        An updated version of the file.
    """
    new_hdus = list()
    with fits.open(filename, mode='readonly', memmap=False, lazy_load_hdus=False, uint=False, disable_image_compression=True, do_not_scale_image_data=True, character_as_bytes=True, scale_back=True) as hdulist:
        log.debug(hdulist._open_kwargs)
        kwargs = hdulist._open_kwargs.copy()
        for h in hdulist:
            hc = h.copy()
            if hasattr(h, '_do_not_scale_image_data'):
                hc._do_not_scale_image_data = h._do_not_scale_image_data
            if hasattr(h, '_bzero'):
                hc._bzero = h._bzero
            if hasattr(h, '_bscale'):
                hc._bzero = h._bscale
            if hasattr(h, '_scale_back'):
                hc._scale_back = h._scale_back
            if hasattr(h, '_uint'):
                hc._uint = h._uint
            #
            # Work around header comments not copied for BinTableHDU.
            #
            if isinstance(h, fits.BinTableHDU):
                for key in h.header.keys():
                    hc.header.comments[key] = h.header.comments[key]
            #
            # Work around disappearing BZERO and BSCALE keywords.
            #
            if isinstance(h, fits.ImageHDU) and 'BZERO' in h.header and 'BSCALE' in h.header:
                if 'BZERO' not in hc.header or 'BSCALE' not in hc.header:
                    iscale = h.header.index('BSCALE')
                    izero = h.header.index('BZERO')
                    if izero > iscale:
                        hc.header.insert(iscale - 1, ('BSCALE', h.header['BSCALE'], h.header.comments['BSCALE']), after=True)
                        hc.header.insert(iscale, ('BZERO', h.header['BZERO'], h.header.comments['BZERO']), after=True)
                    else:
                        hc.header.insert(izero - 1, ('BZERO', h.header['BZERO'], h.header.comments['BZERO']), after=True)
                        hc.header.insert(izero, ('BSCALE', h.header['BSCALE'], h.header.comments['BSCALE']), after=True)
            new_hdus.append(hc)
    new_hdulist = fits.HDUList(new_hdus)
    new_hdulist._open_kwargs = kwargs
    log.debug(new_hdulist._open_kwargs)
    try:
        ext = int(extension)
    except ValueError:
        ext = extension
    try:
        hdu = new_hdulist[ext]
    except (IndexError, KeyError):
        raise
    return new_hdulist


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
    parser.add_argument('-o', '--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite the input FITS file.')
    parser.add_argument('-t', '--test', dest='test', action='store_true',
                        help='Test mode; show what would be done but do not change any files.')
    parser.add_argument('-u', '--units', action='store', dest='units', metavar='UNITS',
                        help="UNITS should have the form COLUMN='unit':COLUMN='unit'.")
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='Print extra debugging information.')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + desiutilVersion)
    parser.add_argument('-Y', '--yaml', action='store', dest='yaml', metavar='YAML',
                        help="Read annotations from YAML file.")
    parser.add_argument('fits', metavar='INPUT_FITS', help='FITS file to modify.')
    parser.add_argument('output', metavar='OUTPUT_FITS', nargs='?',
                        help='Write to new FITS file. If --overwrite is specified, this value is ignored.')
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
        units, comments = load_csv_units(options.csv)
    elif options.yaml:
        units, comments = load_yml_units(options.yaml)
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
    log.debug("units = %s", units)
    log.debug("comments = %s", comments)
    hdulist = annotate(options.fits, options.extension, units, comments)
    if options.overwrite and options.output:
        output = options.output
    elif options.overwrite:
        output = options.fits
    elif options.output:
        output = options.output
    else:
        log.error("--overwrite not specified and no output file specified!")
        return 1
    try:
        hdulist.writeto(output, output_verify='warn', overwrite=options.overwrite, checksum=False)
    except OSError as e:
        if 'overwrite' in e.args[0]:
            log.error("Output file exists and --overwrite was not specified!")
        else:
            log.error(e.args[0])
        return 1
    return 0
