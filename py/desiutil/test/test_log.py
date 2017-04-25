# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.log.
"""
from __future__ import absolute_import, print_function
import unittest
import desiutil.log as dul


class TestLog(unittest.TestCase):
    """Test desispec.log
    """

    def setUp(self):
        """Reset the cached logging object for each test.
        """
        from os import environ
        try:
            self.desi_level = environ['DESI_LOGLEVEL']
        except KeyError:
            self.desi_level = None
        dul.desi_logger = None

    def run_logs(self, **kwargs):
        """Loop over log levels.
        """
        for level in (None, dul.DEBUG, dul.INFO, dul.WARNING, dul.ERROR):
            logger = dul.get_logger(level, **kwargs)
            print("With the requested debugging level={0}:".format(level))
            if self.desi_level is not None and (self.desi_level != ""):
                print(("    (but overuled by env. " +
                       "DESI_LOGLEVEL='{0}')").format(self.desi_level))
            print("--------------------------------------------------")
            logger.debug("This is a debugging message.")
            logger.info("This is an informational message.")
            logger.warning("This is a warning message.")
            logger.error("This is an error message.")
            logger.critical("This is a critical error message.")

    def test_log(self):
        """Test basic logging functionality.
        """
        self.run_logs()

    def test_log_with_desi_loglevel(self):
        """Test basic logging functionality with DESI_LOGLEVEL set.
        """
        from os import environ
        desi_level_cache = self.desi_level
        for lvl in ('warning', 'foobar'):
            self.desi_level = environ['DESI_LOGLEVEL'] = lvl
            self.run_logs()
        if desi_level_cache is None:
            del environ['DESI_LOGLEVEL']
            self.desi_level = None
        else:
            environ['DESI_LOGLEVEL'] = desi_level_cache
            self.desi_level = desi_level_cache

    def test_log_with_timestamp(self):
        """Test logging with timestamps.
        """
        self.run_logs(timestamp=True)

    def test_log_with_delimiter(self):
        """Test logging with alternate delimiter.
        """
        self.run_logs(delimiter=' -- ')


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
