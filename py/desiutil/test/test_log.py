# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.log.
"""
from __future__ import absolute_import, print_function
import os
import re
import unittest
from logging import NullHandler
from logging.handlers import MemoryHandler
from warnings import catch_warnings, simplefilter

skipMock = False
try:
    from unittest.mock import patch
except ImportError:
    # Python 2
    skipMock = True

import desiutil.log as dul


class TestHandler(MemoryHandler):
    """Capture log messages in memory.
    """
    def __init__(self, capacity=1000000, flushLevel=dul.CRITICAL):
        nh = NullHandler()
        MemoryHandler.__init__(self, capacity,
                               flushLevel=flushLevel, target=nh)

    def shouldFlush(self, record):
        """Never flush, except manually.
        """
        return False


class TestLog(unittest.TestCase):
    """Test desispec.log
    """

    @classmethod
    def setUpClass(cls):
        """Cache DESI_LOGLEVEL if it is set.
        """
        cls.desi_loglevel = None
        if 'DESI_LOGLEVEL' in os.environ:
            cls.desi_loglevel = os.environ['DESI_LOGLEVEL']
            del os.environ['DESI_LOGLEVEL']
        cls.fmtre = re.compile(r"""
        ^(DEBUG|INFO|WARNING|ERROR|CRITICAL)              # level
        (:|\s--\s)                                        # delimiter
        test_log\.py                                      # the module
        (:|\s--\s)                                        # delimiter
        (\d+)                                             # line number
        (:|\s--\s)                                        # delimiter
        (run_logs|test_log_context)                       # function
        ((:|\s--\s)\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}|)  # optional timetamp
        :\s                                               # start of message
        """, re.VERBOSE)

    @classmethod
    def tearDown(self):
        """Restore DESI_LOGLEVEL, if necessary.
        """
        if cls.desi_loglevel is not None:
            os.environ['DESI_LOGLEVEL'] = cls.desi_loglevel

    def setUp(self):
        """Reset the cached logging object for each test.
        """
        dul.desi_logger = None

    def tearDown(self):
        pass

    def assertLog(self, logger, order=-1, message=''):
        """Examine the log messages.
        """
        handler = logger.handlers[0]
        record = handler.buffer[order]
        self.assertEqual(record.getMessage(), message)
        formatted = handler.format(record)
        if not skipMock:
            # Cheating on Python 3 detection.
            self.assertRegex(formatted, self.fmtre)

    def get_logger(self, level, **kwargs):
        """Get the actual logging object, but swap out its default handler.
        """
        logger = dul.get_logger(level, **kwargs)
        # actual_level = logger.level
        while len(logger.handlers) > 0:
            h = logger.handlers[0]
            fmt = h.formatter
            logger.removeHandler(h)
        mh = TestHandler()
        mh.setFormatter(fmt)
        logger.addHandler(mh)
        # logger.setLevel(actual_level)
        return logger

    def run_logs(self, **kwargs):
        """Loop over log levels.
        """
        try:
            desi_loglevel = os.environ['DESI_LOGLEVEL']
        except KeyError:
            desi_loglevel = None
        for level in (None, dul.DEBUG, dul.INFO, dul.WARNING, dul.ERROR, dul.CRITICAL):
            with catch_warnings(record=True) as w:
                simplefilter('always')
                logger = self.get_logger(level, **kwargs)
                if desi_loglevel is None:
                    if level is None:
                        self.assertEqual(logger.level, dul.INFO)
                    else:
                        self.assertEqual(logger.level, level)
                else:
                    if desi_loglevel == 'foobar':
                        self.assertEqual(len(w), 1)
                        self.assertTrue(issubclass(w[-1].category,
                                                   UserWarning))
                        # print(w[-1].message)
                        self.assertTrue("Ignore DESI_LOGLEVEL='foobar'" in str(w[-1].message))
                    else:
                        self.assertEqual(logger.level, dul.WARNING)
            logger.debug("This is a debugging message.")
            logger.info("This is an informational message.")
            logger.warning("This is a warning message.")
            logger.error("This is an error message.")
            logger.critical("This is a critical error message.")
            if desi_loglevel is None or desi_loglevel == 'foobar':
                if level is None:
                    pass
                    # Should be the same as INFO.
                    self.assertLog(logger, 0, "This is an informational message.")
                    self.assertLog(logger, 1, "This is a warning message.")
                    self.assertLog(logger, 2, "This is an error message.")
                    self.assertLog(logger, 3, "This is a critical error message.")
                if level == dul.DEBUG:
                    self.assertLog(logger, 0, "This is a debugging message.")
                    self.assertLog(logger, 1, "This is an informational message.")
                    self.assertLog(logger, 2, "This is a warning message.")
                    self.assertLog(logger, 3, "This is an error message.")
                    self.assertLog(logger, 4, "This is a critical error message.")
                if level == dul.INFO:
                    self.assertLog(logger, 0, "This is an informational message.")
                    self.assertLog(logger, 1, "This is a warning message.")
                    self.assertLog(logger, 2, "This is an error message.")
                    self.assertLog(logger, 3, "This is a critical error message.")
                if level == dul.WARNING:
                    self.assertLog(logger, 0, "This is a warning message.")
                    self.assertLog(logger, 1, "This is an error message.")
                    self.assertLog(logger, 2, "This is a critical error message.")
                if level == dul.ERROR:
                    self.assertLog(logger, 0, "This is an error message.")
                    self.assertLog(logger, 1, "This is a critical error message.")
                if level == dul.CRITICAL:
                    self.assertLog(logger, 0, "This is a critical error message.")
            else:
                self.assertLog(logger, 0, "This is a warning message.")
                self.assertLog(logger, 1, "This is an error message.")
                self.assertLog(logger, 2, "This is a critical error message.")
            logger.handlers[0].flush()
            dul.desi_logger = None

    def test_log(self):
        """Test basic logging functionality.
        """
        self.run_logs()

    @unittest.skipIf(skipMock, "Skipping test that requires unittest.mock.")
    def test_log_with_desi_loglevel(self):
        """Test basic logging functionality with DESI_LOGLEVEL set.
        """
        for lvl in ('warning', 'foobar'):
            with patch.dict('os.environ', {'DESI_LOGLEVEL': lvl}):
                self.run_logs()

    def test_log_with_timestamp(self):
        """Test logging with timestamps.
        """
        self.run_logs(timestamp=True)

    def test_log_with_delimiter(self):
        """Test logging with alternate delimiter.
        """
        self.run_logs(delimiter=' -- ')

    def test_log_context(self):
        """Test logging within a temporary context.
        """
        logger = self.get_logger(dul.WARNING)
        logger.debug("This is a debugging message.")
        logger.warning("This is a warning message.")
        self.assertLog(logger, 0, "This is a warning message.")
        with dul.DesiLogContext(logger, dul.DEBUG):
            logger.debug("This is a debugging message.")
            logger.info("This is an informational message.")
            logger.warning("This is a warning message.")
        self.assertLog(logger, 1, "This is a debugging message.")
        self.assertLog(logger, 2, "This is an informational message.")
        self.assertLog(logger, 3, "This is a warning message.")
        logger.debug("This is a debugging message.")
        logger.info("This is an informational message.")
        logger.warning("This is a warning message.")
        self.assertLog(logger, 4, "This is a warning message.")


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
