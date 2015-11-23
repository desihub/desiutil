# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""test desiutil.svn
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
from os import environ
from os.path import abspath, dirname, isdir, join
from subprocess import Popen, PIPE
from shutil import rmtree
from ..svn import last_revision, last_tag, version


class TestSvn(unittest.TestCase):
    """Test desiutil.svn.
    """

    @classmethod
    def setUpClass(cls):
        # Data directory
        cls.data_dir = join(dirname(__file__), 't')
        # Set up a dummy svn repository.
        cls.svn_path = join(abspath(cls.data_dir), 'svn_test')
        cls.svn_checkout_path = join(abspath(cls.data_dir), 'svn_test_co')
        p = Popen(['which', 'svnadmin'], stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        cls.has_subversion = p.returncode == 0
        if cls.has_subversion:
            try:
                cls.svn_url = 'file://' + cls.svn_path
                p = Popen(['svnadmin', 'create', cls.svn_path],
                          stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()
                assert p.returncode == 0
                p = Popen(['svn', 'mkdir', cls.svn_url + '/trunk',
                          cls.svn_url + '/tags', cls.svn_url + '/branches',
                          '-m', "Create initial structure."],
                          stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()
                assert p.returncode == 0
                p = Popen(['svn', 'mkdir',
                          cls.svn_url + '/tags/0.0.1',
                          cls.svn_url + '/tags/0.1.0',
                          cls.svn_url + '/tags/0.1.1',
                          cls.svn_url + '/tags/0.2.0',
                          cls.svn_url + '/tags/0.2.1',
                          '-m', "Create tags."],
                          stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()
                assert p.returncode == 0
                p = Popen(['svn', 'checkout', cls.svn_url,
                          cls.svn_checkout_path],
                          stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()
                assert p.returncode == 0
            except AssertionError:
                cls.has_subversion = False
                rmtree(cls.svn_path)
                rmtree(cls.svn_checkout_path)
        # Create an environment variable pointing to a dummy product.
        if isdir(cls.svn_checkout_path):
            if 'SVN_TEST_DIR' in environ:
                cls.old_svn_test_dir = environ['SVN_TEST_DIR']
            else:
                cls.old_svn_test_dir = None
            environ['SVN_TEST_DIR'] = cls.svn_checkout_path

    @classmethod
    def tearDownClass(cls):
        # Clean up svn repository.
        if cls.has_subversion:
            rmtree(cls.svn_path)
            rmtree(cls.svn_checkout_path)
        if cls.old_svn_test_dir is None:
            del environ['SVN_TEST_DIR']
        else:
            environ['SVN_TEST_DIR'] = cls.old_svn_test_dir

    def test_last_revision(self):
        """Test svn revision number determination.
        """
        n = last_revision('frobulate')
        self.assertEqual(n, '0')
        if self.has_subversion:
            if 'FROBULATE' in environ:
                old_frob = environ['FROBULATE']
            else:
                old_frob = None
            environ['FROBULATE'] = self.data_dir
            n = last_revision('frobulate')
            self.assertEqual(n, '0')
            if old_frob is None:
                del environ['FROBULATE']
            else:
                environ['FROBULATE'] = old_frob

    def test_last_tag(self):
        """Test the processing of svn tag lists.
        """
        if self.has_subversion:
            tag = last_tag(self.svn_url + '/tags')
            self.assertEqual(tag, '0.2.1')
            tag = last_tag(self.svn_url + '/tags', username=environ['USER'])
            self.assertEqual(tag, '0.2.1')
            tag = last_tag(self.svn_url + '/branches')
            self.assertEqual(tag, '0.0.0')

    def test_version(self):
        """Test svn version parser.
        """
        v = version('svn_test', url=self.svn_url)
        self.assertEqual(v, '0.2.1.dev0',
                         'Failed to extract version, got {0}.'.format(v))
        v = version('foo_bar')
        self.assertEqual(v, '0.0.1.dev0', ('Failed to return default ' +
                         'version, got {0}.').format(v))
        # if self.has_subversion:
        #     v = version('svn_test',url=self.svn_url))
        #     self.assertEqual(v,'0.2.1.dev2')
        #     v = version('svn_test',url=self.svn_url)
        #     self.assertEqual(v,'0.2.1.dev2')
