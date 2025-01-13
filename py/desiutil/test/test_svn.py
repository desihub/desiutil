# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.svn.
"""
import unittest
from unittest.mock import call, DEFAULT, patch, Mock, PropertyMock
from ..svn import last_revision, last_tag, version


class TestSvn(unittest.TestCase):
    """Test desiutil.svn.
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_last_revision(self):
        """Test svn revision number determination.
        """
        from subprocess import PIPE
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            process.returncode = 0
            process.communicate.return_value = ('Unversioned', '')
            MockPopen.return_value = process
            calls = [call(['svnversion', '-n', '.'],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate()]
            n = last_revision()
            self.assertEqual(n, '0')
            MockPopen.assert_has_calls(calls)
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            process.returncode = 0
            process.communicate.return_value = ('123:345', '')
            MockPopen.return_value = process
            calls = [call(['svnversion', '-n', '.'],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate()]
            n = last_revision()
            self.assertEqual(n, '345')
            MockPopen.assert_has_calls(calls)
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            process.returncode = 0
            process.communicate.return_value = ('345M', '')
            MockPopen.return_value = process
            calls = [call(['svnversion', '-n', '.'],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate()]
            n = last_revision()
            self.assertEqual(n, '345')
            MockPopen.assert_has_calls(calls)

    def test_last_tag(self):
        """Test the processing of svn tag lists.
        """
        from subprocess import PIPE
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            process.returncode = 0
            process.communicate.return_value = ('0.0.1/\n0.0.2/\n0.0.3/\n', '')
            MockPopen.return_value = process
            calls = [call(['svn', '--non-interactive', 'ls', 'tags'],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate()]
            n = last_tag('tags')
            self.assertEqual(n, '0.0.3')
            MockPopen.assert_has_calls(calls)
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            process.returncode = 0
            process.communicate.return_value = ('0.0.1/\n0.0.2/\n0.0.3/\n', '')
            MockPopen.return_value = process
            calls = [call(['svn', '--non-interactive', '--username', 'foo', 'ls', 'tags'],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate()]
            n = last_tag('tags', 'foo')
            self.assertEqual(n, '0.0.3')
            MockPopen.assert_has_calls(calls)
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            process.returncode = 0
            process.communicate.return_value = ('', '')
            MockPopen.return_value = process
            calls = [call(['svn', '--non-interactive', '--username', 'foo', 'ls', 'tags'],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate()]
            n = last_tag('tags', 'foo')
            self.assertEqual(n, '0.0.0')
            MockPopen.assert_has_calls(calls)

    def test_version(self):
        """Test svn version parser.
        """
        with patch.multiple('desiutil.svn', last_tag=DEFAULT, last_revision=DEFAULT) as patches:
            with patch.dict('desiutil.install.known_products', {'foo': 'bar'}) as pd:
                patches['last_revision'].return_value = '0'
                patches['last_tag'].return_value = '1.2.3'
                v = version('foo')
                self.assertEqual(v, '1.2.3.dev0')
                v = version('bar', url='baz')
                self.assertEqual(v, '1.2.3.dev0')
                v = version('frobulate')
                self.assertEqual(v, '0.0.1.dev0')
