# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.log.
"""
from __future__ import absolute_import, print_function
import os
import re
import unittest
from logging import getLogger, NullHandler
from logging.handlers import MemoryHandler
from warnings import catch_warnings, simplefilter
import ..log as dul


skipMock = False
try:
    from unittest.mock import patch
except ImportError:
    # Python 2
    skipMock = True


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
    """Test desiutil.log
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
        (:|\s--\s)\s                                      # start of message
        """, re.VERBOSE)

    @classmethod
    def tearDownClass(cls):
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
        root_logger = getLogger(logger.name.rsplit('.', 1)[0])
        handler = root_logger.handlers[0]
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
        root_logger = getLogger(logger.name.rsplit('.', 1)[0])
        while len(root_logger.handlers) > 0:
            h = root_logger.handlers[0]
            fmt = h.formatter
            root_logger.removeHandler(h)
        mh = TestHandler()
        mh.setFormatter(fmt)
        root_logger.addHandler(mh)
        return logger

    def run_logs(self, **kwargs):
        """Loop over log levels.
        """
        str2level = {'debug': dul.DEBUG, 'info': dul.INFO, 'warning': dul.WARNING, 'error': dul.ERROR, 'critical': dul.CRITICAL}
        try:
            desi_loglevel = os.environ['DESI_LOGLEVEL']
        except KeyError:
            desi_loglevel = None
        for level in (None, dul.DEBUG, dul.INFO, dul.WARNING, dul.ERROR, dul.CRITICAL,
                      'debug', 'info', 'warning', 'error', 'critical'):
            with catch_warnings(record=True) as w:
                simplefilter('always')
                if desi_loglevel is None:
                    logger = self.get_logger(level, **kwargs)
                    if level is None:
                        self.assertEqual(logger.level, dul.INFO)
                    elif level in ('debug', 'info', 'warning', 'error', 'critical'):
                        self.assertEqual(logger.level, str2level[level])
                    else:
                        self.assertEqual(logger.level, level)
                else:
                    logger = self.get_logger(None, **kwargs)
                    if desi_loglevel == 'foobar':
                        self.assertEqual(len(w), 1)
                        self.assertTrue(issubclass(w[-1].category,
                                                   UserWarning))
                        # print(w[-1].message)
                        self.assertIn("Invalid level='FOOBAR' ignored.", str(w[-1].message))
                    else:
                        self.assertEqual(logger.level, dul.WARNING)
            logger.debug("This is a debugging message.")
            logger.info("This is an informational message.")
            logger.warning("This is a warning message.")
            logger.error("This is an error message.")
            logger.critical("This is a critical error message.")
            if desi_loglevel is None:
                if level is None:
                    # Should be the same as INFO.
                    self.assertLog(logger, 0, "This is an informational message.")
                    self.assertLog(logger, 1, "This is a warning message.")
                    self.assertLog(logger, 2, "This is an error message.")
                    self.assertLog(logger, 3, "This is a critical error message.")
                if level == dul.DEBUG or level == 'debug':
                    self.assertLog(logger, 0, "This is a debugging message.")
                    self.assertLog(logger, 1, "This is an informational message.")
                    self.assertLog(logger, 2, "This is a warning message.")
                    self.assertLog(logger, 3, "This is an error message.")
                    self.assertLog(logger, 4, "This is a critical error message.")
                if level == dul.INFO or level == 'info':
                    self.assertLog(logger, 0, "This is an informational message.")
                    self.assertLog(logger, 1, "This is a warning message.")
                    self.assertLog(logger, 2, "This is an error message.")
                    self.assertLog(logger, 3, "This is a critical error message.")
                if level == dul.WARNING or level == 'warning':
                    self.assertLog(logger, 0, "This is a warning message.")
                    self.assertLog(logger, 1, "This is an error message.")
                    self.assertLog(logger, 2, "This is a critical error message.")
                if level == dul.ERROR or level == 'error':
                    self.assertLog(logger, 0, "This is an error message.")
                    self.assertLog(logger, 1, "This is a critical error message.")
                if level == dul.CRITICAL or level == 'critical':
                    self.assertLog(logger, 0, "This is a critical error message.")
            elif desi_loglevel == 'foobar':
                # Should be the same as INFO.
                self.assertLog(logger, 0, "This is an informational message.")
                self.assertLog(logger, 1, "This is a warning message.")
                self.assertLog(logger, 2, "This is an error message.")
                self.assertLog(logger, 3, "This is a critical error message.")
            else:
                self.assertLog(logger, 0, "This is a warning message.")
                self.assertLog(logger, 1, "This is an error message.")
                self.assertLog(logger, 2, "This is a critical error message.")
            getLogger(logger.name.rsplit('.', 1)[0]).handlers[0].flush()

    def test_log(self):
        """Test basic logging functionality.
        """
        self.run_logs()

    def test_log_multiple(self):
        """Test multiple calls to return the logger.
        """
        log1 = dul.get_logger()
        log2 = dul.get_logger()
        self.assertIs(log1, log2)

    def test_log_singleton(self):
        """Test the default pseudo-singleton created by the module.
        """
        log2 = dul.get_logger()
        self.assertIs(log2, dul.log)

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
        with catch_warnings(record=True) as w:
            simplefilter('always')
            with dul.DesiLogContext(logger):
                logger.debug("This is a debugging message.")
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category,
                            UserWarning))
            # print(w[-1].message)
            self.assertTrue("This context manager will not actually do anything!" in str(w[-1].message))


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
