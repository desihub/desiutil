# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
============
desiutil.log
============

Utility functions to dump log messages. We can have something specific for
DESI in the future but for now we use the standard Python.
"""
from __future__ import absolute_import, division, print_function
import logging

desi_logger = None

# Just for convenience to avoid importing logging, we duplicate the logging levels
DEBUG = logging.DEBUG        # Detailed information, typically of interest only when diagnosing problems.
INFO = logging.INFO          # Confirmation that things are working as expected.
WARNING = logging.WARNING    # An indication that something unexpected happened, or indicative of some problem
                             # in the near future (e.g. "disk space low"). The software is still working as expected.
ERROR = logging.ERROR        # Due to a more serious problem, the software has not been able to perform some function.
CRITICAL = logging.CRITICAL  # A serious error, indicating that the program itself may be unable to continue running.

# see example of usage in test/test_log.py


def get_logger(level=None, timestamp=False, delimiter=':'):
    """Returns a default DESI logger.

    Parameters
    ----------
    level : :class:`int`, optional
        Debugging level.
    timestamp : :class:`bool`, optional
        If set, include a time stamp in the log message.
    delimiter : :class:`str`, optional
        Use this string to separate fields in the log messages, default ':'.

    Returns
    -------
    :class:`logging.Logger`
        A logging object configured with the DESI defaults.

    Notes
    -----
    * If environment variable :envvar:`DESI_LOGLEVEL` exists and has value
      DEBUG, INFO, WARNING or ERROR (upper or lower case), it overules the level
      argument.
    * If :envvar:`DESI_LOGLEVEL` is not set and `level` is ``None``,
      the default level is set to INFO.
    """
    from os import environ
    from sys import stdout
    global desi_logger
    try:
        desi_level = environ["DESI_LOGLEVEL"]
    except KeyError:
        desi_level = None
    if desi_level is not None and (desi_level != ""):
        #
        # Forcing the level to the value of DESI_LOGLEVEL,
        # ignoring the requested logging level.
        #
        desi_level = desi_level.upper()
        dico = {"DEBUG": DEBUG,
                "INFO": INFO,
                "WARNING": WARNING,
                "ERROR": ERROR}
        try:
            level = dico[desi_level]
        except KeyError:
            # Amusingly I would need the logger to dump a warning here
            # but this recursion can be problematic.
            message = ("Ignore DESI_LOGLEVEL='{0}' " +
                       "(only recognize {1}).").format(desi_level,
                                                       ', '.join(dico.keys()))
            print(message)

    if level is None:
        level = INFO

    if desi_logger is not None :
        if level is not None :
            desi_logger.setLevel(level)
        return desi_logger

    desi_logger = logging.getLogger("DESI")

    desi_logger.setLevel(level)

    while len(desi_logger.handlers) > 0:
        h = desi_logger.handlers[0]
        desi_logger.removeHandler(h)

    ch = logging.StreamHandler(stdout)

    fmtfields = ['%(levelname)s', '%(filename)s', '%(lineno)s', '%(funcName)s']
    if timestamp:
        fmtfields.append('%(asctime)s')
    fmt = delimiter.join(fmtfields)

    formatter = logging.Formatter(fmt + ': %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

    ch.setFormatter(formatter)

    desi_logger.addHandler(ch)

    return desi_logger
