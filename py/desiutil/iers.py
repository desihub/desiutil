# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
=============
desiutil.iers
=============

Utilities for overriding astropy IERS functionality (:mod:`astropy.utils.iers`),
especially for preventing unnecessary downloads of IERS data files in a
high performance computing environment.
"""
import os
import warnings
import numpy as np
from astropy.table import Table
from astropy.time import Time
import astropy.utils.iers
try:
    from astropy.utils.data import get_pkg_data_path
except ImportError:
    # Astropy < 4.3
    from astropy.utils.data import _find_pkg_data_path as get_pkg_data_path
from .log import get_logger


#
# Global flag for frozen state.
#
_iers_is_frozen = False
#
# Workaround for offline primary IERS server.
#
# astropy.utils.iers.Conf.iers_auto_url.set('ftp://cddis.gsfc.nasa.gov/pub/products/iers/finals2000A.all')
astropy.utils.iers.conf.iers_auto_url = 'ftp://cddis.gsfc.nasa.gov/pub/products/iers/finals2000A.all'
astropy.utils.iers.conf.auto_download = False


def freeze_iers(name='iers_frozen.ecsv', ignore_warnings=True):
    """Use a frozen IERS table saved with this package.

    This should be called at the beginning of a script that calls
    astropy time and coordinates functions which refer to the UT1-UTC
    and polar motions tabulated by IERS.  The purpose is to ensure
    identical results across systems and astropy releases, to avoid a
    potential network download, and to eliminate some astropy warnings.

    After this call, the loaded table will be returned by
    :func:`astropy.utils.iers.IERS_Auto.open()` and treated like a
    a normal IERS table by all astropy code.  Specifically, this method
    registers an instance of a custom IERS_Frozen class that inherits from
    IERS_B and overrides
    :meth:`astropy.utils.iers.IERS._check_interpolate_indices` to prevent
    any IERSRangeError being raised.

    See https://docs.astropy.org/en/stable/utils/iers.html for details.

    This function returns immediately after the first time it is called,
    so it it safe to insert anywhere that consistent IERS models are
    required, and subsequent calls with different args will have no
    effect.

    The :func:`desiutil.plots.plot_iers` function is useful for inspecting
    IERS tables and how they are extrapolated to DESI survey dates.

    Parameters
    ----------
    name : :class:`str`, optional
        Name of the file to load the frozen IERS table from. Should normally
        be relative and then refers to this package's data/ directory.
        Must end with the .ecsv extension.
    ignore_warnings : :class:`bool`, optional
        Ignore ERFA and IERS warnings about future dates generated by
        astropy time and coordinates functions. Specifically, ERFA warnings
        containing the string "dubious year" are filtered out, as well
        as AstropyWarnings related to IERS table extrapolation.
    """
    global _iers_is_frozen
    log = get_logger()
    if _iers_is_frozen:
        log.debug('IERS table already frozen.')
        return
    log.info('Freezing IERS table used by astropy time, coordinates.')

    # Validate the save_name extension.
    _, ext = os.path.splitext(name)
    if ext != '.ecsv':
        raise ValueError('Expected .ecsv extension for {0}.'.format(name))

    # Locate the file in our package data/ directory.
    if not os.path.isabs(name):
        name = get_pkg_data_path(os.path.join('data', name))
    if not os.path.exists(name):
        raise ValueError('No such IERS file: {0}.'.format(name))

    # Clear any current IERS table.
    astropy.utils.iers.IERS.close()
    # Initialize the global IERS table. We load the table by
    # hand since the IERS open() method hardcodes format='cds'.
    try:
        table = Table.read(name, format='ascii.ecsv').filled()
    except IOError:
        raise RuntimeError('Unable to load IERS table from {0}.'.format(name))

    # Define a subclass of IERS_B that overrides _check_interpolate_indices
    # to prevent any IERSRangeError being raised.
    class IERS_Frozen(astropy.utils.iers.IERS_B):
        def _check_interpolate_indices(self, indices_orig, indices_clipped,
                                       max_input_mjd):
            pass

    # Create and register an instance of this class from the table.
    iers = IERS_Frozen(table)
    astropy.utils.iers.IERS.iers_table = iers
    astropy.utils.iers.IERS_B.iers_table = iers
    # Prevent any attempts to automatically download updated IERS-A tables.
    astropy.utils.iers.conf.auto_download = False
    astropy.utils.iers.conf.auto_max_age = None
    astropy.utils.iers.conf.iers_auto_url = 'frozen'
    astropy.utils.iers.conf.iers_auto_url_mirror = 'frozen'
    if ignore_warnings:
        astropy.utils.iers.conf.iers_degraded_accuracy = 'ignore'
    else:
        astropy.utils.iers.conf.iers_degraded_accuracy = 'warn'
    # Sanity check.
    # In Astropy 7 this appears to be broken due to the iers_frozen.ecsv being out of date.
    # The *format* of that file no longer matches what is expected by astropy.util.iers.
    try:
        auto_class = astropy.utils.iers.IERS_Auto.open()
        if auto_class is not iers:
            raise RuntimeError('Frozen IERS is not installed as the default ({0} v. {1}).'.format(auto_class.__class__, iers.__class__))
    except KeyError:
        # Temporary Astropy 7/IERS workaround.
        warnings.warn("Temporarily skipping IERS integrity check.", UserWarning)

    if ignore_warnings:
        try:
            warnings.filterwarnings('ignore',
                                    category=astropy._erfa.core.ErfaWarning,
                                    message=r'ERFA function \"[a-z0-9_]+\" yielded [0-9]+ of \"dubious year')
        except AttributeError:
            # Astropy >= 4.2
            from erfa import ErfaWarning
            warnings.filterwarnings('ignore',
                                    category=ErfaWarning,
                                    message=r'ERFA function \"[a-z0-9_]+\" yielded [0-9]+ of \"dubious year')

        warnings.filterwarnings('ignore',
                                category=astropy.utils.exceptions.AstropyWarning,
                                message=r'Tried to get polar motions for times after IERS data')
        warnings.filterwarnings('ignore',
                                category=astropy.utils.exceptions.AstropyWarning,
                                message=r'\(some\) times are outside of range covered by IERS')

    # Shortcircuit any subsequent calls to this function.
    _iers_is_frozen = True


def update_iers(save_name='iers_frozen.ecsv', num_avg=1000):
    """Update the IERS table used by astropy time, coordinates.

    Downloads the current IERS-A table, replaces the last entry (which is
    repeated for future times) with the average of the last ``num_avg``
    entries, and saves the table in ECSV format.

    This should only be called every few months, *e.g.*, with major releases.
    The saved file should then be copied to this package's data/ directory
    and committed to the git repository.

    Requires a network connection in order to download the current IERS-A table.
    Prints information about the update process.

    The :func:`desiutil.plots.plot_iers` function is useful for inspecting
    IERS tables and how they are extrapolated to DESI survey dates.

    Parameters
    ----------
    save_name : :class:`str`, optional
        Name where frozen IERS table should be saved. Must end with the
        .ecsv extension.
    num_avg : :class:`int`, optional
        Number of rows from the end of the current table to average and
        use for calculating UT1-UTC offsets and polar motion at times
        beyond the table.
    """
    log = get_logger()
    # Validate the save_name extension.
    _, ext = os.path.splitext(save_name)
    if ext != '.ecsv':
        raise ValueError('Expected .ecsv extension for {0}.'.format(save_name))

    # Download the latest IERS_A table
    if astropy.utils.iers.conf.iers_auto_url == 'frozen':
        raise ValueError("Attempting to update a frozen IERS A table!")
    iers = astropy.utils.iers.IERS_A.open(astropy.utils.iers.conf.iers_auto_url)
    last = Time(iers['MJD'][-1], format='mjd').datetime
    log.info('Updating to current IERS-A table with coverage up to %s.',
             last.date())

    # Loop over the columns used by the astropy IERS routines.
    for name in 'UT1_UTC', 'PM_x', 'PM_y':
        # Replace the last entry with the mean of recent samples.
        mean_value = np.mean(iers[name][-num_avg:].value)
        unit = iers[name].unit
        iers[name][-1] = mean_value * unit
        log.info('Future %7s = %.3f', name, mean_value * unit)

    # Strip the original table metadata since ECSV cannot handle it.
    # We only need a single keyword that is checked by IERS_Auto.open().
    iers.meta = dict(data_url='frozen')

    # Save the table. The IERS-B table provided with astropy uses the
    # ascii.cds format but astropy cannot write this format.
    iers.write(save_name, format='ascii.ecsv', overwrite=True)
    log.info('Wrote updated table to %s.', save_name)
