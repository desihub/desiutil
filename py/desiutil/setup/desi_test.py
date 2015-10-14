# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import unittest
from setuptools.compat import PY3
from setuptools.py31compat import unittest_main
from setuptools.command.test import test as BaseTest
from pkg_resources import _namespace_packages
from distutils.log import INFO
#
# Note, need to explicitly add object as a superclass, because BaseTest
# inherits from an old-style class.  Ugly, but it allows the use of
# super().
#
class DesiTest(BaseTest,object):
    """Add coverage to test commands.
    """
    description = "run unit tests after in-place build"
    user_options = [
        ('test-module=', 'm', "Run 'test_suite' in specified module"),
        ('test-suite=', 's',
         "Test suite to run (e.g. 'some_module.test_suite')"),
        ('test-runner=', 'r', "Test runner to use"),
        ('coverage', 'c', 'Create a coverage report. Requires the coverage package.')
    ]
    boolean_options = ['coverage']
    def initialize_options(self):
        self.coverage = False
        super(DesiTest,self).initialize_options()
    def finalize_options(self):
        if self.coverage:
            try:
                import coverage
            except ImportError:
                raise ImportError("--coverage requires that the coverage package is installed.")
        super(DesiTest,self).finalize_options()
    def run_tests(self):
        # Purge modules under test from sys.modules. The test loader will
        # re-import them from the build location. Required when 2to3 is used
        # with namespace packages.
        if PY3 and getattr(self.distribution, 'use_2to3', False):
            module = self.test_args[-1].split('.')[0]
            if module in _namespace_packages:
                del_modules = []
                if module in sys.modules:
                    del_modules.append(module)
                module += '.'
                for name in sys.modules:
                    if name.startswith(module):
                        del_modules.append(name)
                list(map(sys.modules.__delitem__, del_modules))
        if self.coverage:
            self.announce("Coverage selected!", level=INFO)
            import coverage
            cov = coverage.coverage(data_file=os.path.abspath(".coverage"), config_file=os.path.abspath(".coveragerc"))
            cov.start()

        result = unittest_main(
            None, None, [unittest.__file__] + self.test_args,
            testLoader=self._resolve_as_ep(self.test_loader),
            testRunner=self._resolve_as_ep(self.test_runner),
            exit=False
            )
        if self.coverage:
            cov.stop()
            if result.result.wasSuccessful():
                self.announce('Saving coverage data in .coverage...', level=INFO)
                cov.save()
                self.announce('Saving HTML coverage report in htmlcov...', level=INFO)
                cov.html_report(directory=os.path.abspath('htmlcov'))
