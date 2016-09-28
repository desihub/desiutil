# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.git.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
from ..git import version


class TestGit(unittest.TestCase):
    """Test desiutil.git.
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_version(self):
        """Test automated determination of git version.
        """
        v = version('/no/such/executable')
        self.assertEqual(v, '0.0.1.dev0')
        v = version('false')
        self.assertEqual(v, '0.0.1.dev0')
        v = version('echo')
        self.assertEqual(v, 'describe .devrev-list --count HEAD')


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
