# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.log.
"""
from __future__ import absolute_import, print_function
import unittest
import desiutil.log as l

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
        l.desi_logger = None

    def test_log(self):
        """Test basic logging functionality.
        """
        for level in (None, l.DEBUG, l.INFO, l.WARNING, l.ERROR):
            logger = l.get_logger(level)
            print("With the requested debugging level={0}:".format(level))
            if self.desi_level is not None and (self.desi_level != "" ):
                print("    (but overuled by env. DESI_LOGLEVEL='{0}')".format(self.desi_level))
            print("--------------------------------------------------")
            logger.debug("This is a debugging message.")
            logger.info("This is an informational message.")
            logger.warning("This is a warning message.")
            logger.error("This is an error message.")
            logger.critical("This is a critical error message.")

    def test_log_with_desi_loglevel(self):
        """Test basic logging functionality with DESI_LOGLEVEL set.
        """
        from os import environ
        desi_level_cache = self.desi_level
        for lvl in ('warning', 'foobar'):
            self.desi_level = environ['DESI_LOGLEVEL'] = lvl
            for level in (None, l.DEBUG, l.INFO, l.WARNING, l.ERROR):
                logger = l.get_logger(level)
                print("With the requested debugging level={0}:".format(level))
                if self.desi_level is not None and (self.desi_level != "" ):
                    print("    (but overuled by env. DESI_LOGLEVEL='{0}')".format(self.desi_level))
                print("--------------------------------------------------")
                logger.debug("This is a debugging message.")
                logger.info("This is an informational message.")
                logger.warning("This is a warning message.")
                logger.error("This is an error message.")
                logger.critical("This is a critical error message.")
        if desi_level_cache is None:
            del environ['DESI_LOGLEVEL']
            self.desi_level = None
        else:
            environ['DESI_LOGLEVEL'] = desi_level_cache
            self.desi_level = desi_level_cache

    def test_log_with_timestamp(self):
        """Test logging with timestamps.
        """
        for level in (None, l.DEBUG, l.INFO, l.WARNING, l.ERROR):
            logger = l.get_logger(level, timestamp=True)
            print("With the requested debugging level={0}:".format(level))
            if self.desi_level is not None and (self.desi_level != "" ) :
                print("    (but overuled by env. DESI_LOGLEVEL='{0}'):".format(self.desi_level))
            print("--------------------------------------------------")
            logger.debug("This is a debugging message.")
            logger.info("This is an informational message.")
            logger.warning("This is a warning message.")
            logger.error("This is an error message.")
            logger.critical("This is a critical error message.")

    def test_log_with_delimiter(self):
        """Test logging with alternate delimiter.
        """
        for level in (None, l.DEBUG, l.INFO, l.WARNING, l.ERROR):
            logger = l.get_logger(level, delimiter=' -- ')
            print("With the requested debugging level={0}:".format(level))
            if self.desi_level is not None and (self.desi_level != "" ) :
                print("    (but overuled by env. DESI_LOGLEVEL='{0}'):".format(self.desi_level))
            print("--------------------------------------------------")
            logger.debug("This is a debugging message.")
            logger.info("This is an informational message.")
            logger.warning("This is a warning message.")
            logger.error("This is an error message.")
            logger.critical("This is a critical error message.")


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
