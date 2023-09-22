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
from warnings import warn
import yaml
from astropy.io import fits
from astropy.table import Table, QTable
from astropy.units import Unit, UnitConversionError
from . import __version__ as desiutilVersion
from .log import get_logger, DEBUG


class FITSUnitWarning(UserWarning):
    """Warnings related to invalid FITS units.
    """
    pass


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


def validate_unit(unit, error=False):
    """Check units for consistency with FITS standard, while allowing
    some special exceptions.

    Parameters
    ----------
    unit : :class:`str`
        The unit to parse.
    error : :class:`bool`, optional
        If ``True``, failure to interpret the unit raises an
        exception.

    Returns
    -------
    :class:`str`
        If a special exception is detected, the name of the unit
        is returned.  Otherwise, ``None``.

    Raises
    ------
    :exc:`ValueError`
        If `error` is set and `unit` can't be parsed.
    """
    if unit is None:
        return None
    acceptable_units = ('maggie', 'maggy', 'mgy',
                        'electron/Angstrom',
                        'log(Angstrom)')
    try:
        au = Unit(unit, format='fits')
    except ValueError as e:
        m = str(e)
        bad_unit = m.split()[0]
        if any([u in bad_unit for u in acceptable_units]) and 'Numeric factor' not in m:
            return bad_unit
        else:
            if error:
                raise
            else:
                warn(m, FITSUnitWarning)
    return None


def check_comment_length(comments, error=True):
    """Ensure keyword comments are short enough that they will not be truncated.

    By experiment, :mod:`astropy.io.fits` will truncate comments longer than
    46 characters, however the warning it emits when it does so is not very
    informative.

    Parameters
    ----------
    comments : :class:`dict`
        Mapping of table columns to comments.
    error : :class:`bool`, optional
        If ``False`` just warn about long comments instead of raising an exception.

    Returns
    -------
    :class:`int`
        The number of long comments detected, although the value is only relevant
        if `error` is ``False``.

    Raises
    ------
    ValueError
        If any comment is too long.
    """
    log = get_logger()
    too_long = 46
    n_long = 0
    for key in comments:
        if len(comments[key]) > too_long:
            n_long += 1
            if error:
                log.error("Long comment detected for '%s'!", key)
            else:
                log.warning("Long comment detected for '%s', will be truncated to '%s'!",
                            key, comments[key][:too_long])
    if n_long > 0 and error:
        raise ValueError(f"{n_long:d} long comments detected!")
    return n_long


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
    log = get_logger()
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
    log = get_logger()
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
    log = get_logger()
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


def annotate_fits(filename, extension, output, units=None, comments=None,
                  truncate=False, overwrite=False):
    """Add annotations to HDU `extension` in FITS file `filename`.

    HDU `extension` must be a :class:`astropy.io.fits.BinTableHDU`.

    If `units` or `comments` is an empty dictionary, it will be ignored.

    Parameters
    ----------
    filename : :class:`str`
        Name of FITS file.
    extension : :class:`str` or :class:`int`
        Name or number of extension in `filename`.
    output : :class:`str`
        Name of file to write to.
    units : :class:`dict`, optional
        Mapping of table columns to units.
    comments : :class:`dict`, optional
        Mapping of table columns to comments.
    truncate : :class:`bool`, optional
        Allow long comments to be truncated when written out. The default
        is to raise an error if a comment is too long.
    overwrite : :class:`bool`, optional
        Pass this keyword to :meth:`astropy.io.fits.HDUList.writeto`.


    Returns
    -------
    :class:`astropy.io.fits.HDUList`
        An updated version of the file, equivalent to the data in `output`.

    Raises
    ------
    IndexError
        If the HDU specified (numerically) by `extension` does not exist.
    KeyError
        If the HDU specified (as an ``EXTNAME``) by `extension` does not exist.
    TypeError
        If the HDU specified is not supported by this function.
    ValueError
        If neither `units` nor `comments` are specified.

    Notes
    -----
    * Due to the way :func:`astropy.io.fits.open` manages memory, changes
      have to be written out while `filename` is still open,
      hence the mandatory `output` argument.
    * A FITS HDU checksum will always be added to the output, even if it
      was not already present.
    """
    log = get_logger()
    try:
        ext = int(extension)
    except ValueError:
        ext = extension
    if not units and not comments:
        raise ValueError("No input units or comments specified!")
    if comments:
        n_long = check_comment_length(comments, error=(not truncate))
    with fits.open(filename, mode='readonly') as hdulist:
        new_hdulist = hdulist.copy()
        try:
            hdu = new_hdulist[ext]
        except (IndexError, KeyError):
            raise
        if isinstance(hdu, fits.BinTableHDU) and not isinstance(hdu, fits.CompImageHDU):
            #
            # fits.CompImageHDU is a subclass of fits.BinTableHDU.
            #
            for i in range(1, 1000):
                ttype = f"TTYPE{i:d}"
                if ttype not in hdu.header:
                    break
                colname = hdu.header[ttype]
                if comments and colname in comments and comments[colname].strip():
                    if hdu.header.comments[ttype].strip():
                        log.warning("Overriding comment on column '%s': '%s' -> '%s'.", colname, hdu.header.comments[ttype].strip(), comments[colname].strip())
                    hdu.header[ttype] = (colname, comments[colname].strip())
                if units and colname in units and units[colname].strip():
                    tunit = f"TUNIT{i:d}"
                    if tunit in hdu.header and hdu.header[tunit].strip():
                        log.warning("Overriding units for column '%s': '%s' -> '%s'.", colname, hdu.header[tunit].strip(), units[colname].strip())
                        hdu.header[tunit] = (units[colname].strip(), colname+' units')
                    else:
                        hdu.header.insert(f"TFORM{i:d}", (tunit, units[colname].strip(), colname+' units'), after=True)
        else:
            raise TypeError("Adding units to objects other than fits.BinTableHDU is not supported!")
        hdu.add_checksum()
        new_hdulist.writeto(output, output_verify='warn', overwrite=overwrite, checksum=False)
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
    parser.add_argument('-D', '--disable-comments', action='store_true', dest='disable_comments',
                        help='Do not add comments, even if they are defined in one of the inputs.')
    parser.add_argument('-e', '--extension', dest='extension', action='store', metavar='EXT', default='1',
                        help="Update FITS extension EXT, which can be a number or an EXTNAME. If not specified, HDU 1 will be updated, which is standard for simple binary tables.")
    parser.add_argument('-o', '--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite the input FITS file.')
    parser.add_argument('-T', '--truncate-comments', dest='truncate', action='store_true',
                        help='Allow any long comments to be truncated when written out.')
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
    options = _options()
    if options.verbose:
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
    if options.disable_comments:
        log.info("Comments are disabled by user request.")
        comments = dict()
    if units:
        log.debug("Input Units")
        for k, v in units.items():
            log.debug("'%s': '%s'", k, v)
    if comments:
        log.debug("Input Comments")
        for k, v in comments.items():
            log.debug("'%s': '%s'", k, v)
    if options.overwrite and options.output:
        output = options.output
    elif options.overwrite:
        output = options.fits
    elif options.output:
        output = options.output
    else:
        log.critical("--overwrite not specified and no output file specified!")
        return 1
    try:
        hdulist = annotate_fits(options.fits, options.extension, output,
                                units, comments, truncate=options.truncate,
                                overwrite=options.overwrite)
    except OSError as e:
        if 'overwrite' in e.args[0]:
            log.critical("Output file exists and --overwrite was not specified!")
        else:
            log.critical(e.args[0])
        return 1
    except (IndexError, KeyError, TypeError, ValueError) as e:
        log.critical(str(e))
        return 1
    return 0
