# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
============
desiutil.log
============

DESI-specific utility functions that wrap the standard :mod:`logging`
module.

This module is intended to support three different logging use patterns:

1. Just get an easy-to-use, pre-configured logging object.
2. Easily change the log level temporarily within a function.  This is
   provided by a context manager.
3. Change the default log level on the command-line.  This can actually be
   accomplished in two ways: the command-line interpreter can call
   :func:`~desiutil.log.get_logger` with the appropriate level, or
   the environment variable :envvar:`DESI_LOGLEVEL` can be set.

In addition, it is possible to add timestamps and change the delimiter of
log messages as needed.  See the optional arguments to
:func:`~desiutil.log.get_logger`.

Examples
--------

Simplest possible use:

>>> from desiutil.log import get_logger
>>> log = get_logger()
>>> log.info('This is some information.')

Temporarily change the log level with a context manager:

>>> from desiutil.log import get_logger, DesiLogContext, DEBUG
>>> log = get_logger()  # defaults to INFO
>>> log.info('This is some information.')
>>> log.debug("This won't be logged.")
>>> with DesiLogContext(log, DEBUG):
...     log.debug("This will be logged.")
>>> log.debug("This won't be logged.")

Create the logger with a different log level:

>>> from desiutil.log import get_logger, DEBUG
>>> if options.debug:
...     log = get_logger(DEBUG)
>>> else:
...     log = get_logger()

"""
from __future__ import absolute_import, division, print_function
import logging
from os import environ
from sys import stdout
from warnings import warn

desi_logger = None

# Just for convenience to avoid importing logging, we duplicate the logging levels
DEBUG = logging.DEBUG        # Detailed information, typically of interest only when diagnosing problems.
INFO = logging.INFO          # Confirmation that things are working as expected.
WARNING = logging.WARNING    # An indication that something unexpected happened, or indicative of some problem
                             # in the near future (e.g. "disk space low"). The software is still working as expected.
ERROR = logging.ERROR        # Due to a more serious problem, the software has not been able to perform some function.
CRITICAL = logging.CRITICAL  # A serious error, indicating that the program itself may be unable to continue running.

# see example of usage in test/test_log.py


class DesiLogWarning(UserWarning):
    """Warnings related to misconfiguration of the DESI logging object.
    """
    pass


class DesiLogContext(object):
    """Provides a context manager to temporarily change the log level of
    an existing logging object.

    Parameters
    ----------
    logger : :class:`logging.Logger`
        Logging object.
    level : :class:`int`, optional
        The logging level to set.  If it is not set, this whole class
        does nothing.
    """
    def __init__(self, logger, level=None):  # , handler=None, close=True):
        self.logger = logger
        self.level = level
        # self.handler = handler
        # self.close = close

    def __enter__(self):
        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        # if self.handler:
        #     self.logger.addHandler(self.handler)

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        # if self.handler:
        #     self.logger.removeHandler(self.handler)
        # if self.handler and self.close:
        #     self.handler.close()


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
      DEBUG, INFO, WARNING, ERROR or CRITICAL (upper or lower case),
      it overules the level argument.
    * If :envvar:`DESI_LOGLEVEL` is not set and `level` is ``None``,
      the default level is set to INFO.
    """
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
        dico = {"DEBUG": DEBUG,
                "INFO": INFO,
                "WARNING": WARNING,
                "ERROR": ERROR,
                "CRITICAL": CRITICAL}
        try:
            level = dico[desi_level.upper()]
        except KeyError:
            # Amusingly I would need the logger to dump a warning here
            # but this recursion can be problematic.
            message = ("Ignore DESI_LOGLEVEL='{0}' " +
                       "(only recognize {1}).").format(desi_level,
                                                       ', '.join(dico.keys()))
            warn(message, DesiLogWarning)

    if desi_logger is not None:
        if level is not None:
            desi_logger.setLevel(level)
        return desi_logger

    if level is None:
        level = INFO

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
