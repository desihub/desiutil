# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.git.
"""
import unittest
from unittest.mock import call, patch, Mock, PropertyMock
from ..git import last_tag, version


class TestGit(unittest.TestCase):
    """Test desiutil.git.
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_last_tag(self):
        """Test determination of the last git tag.
        """
        with patch('requests.get') as MockGet:
            result = Mock()
            result.json.return_value = [{'ref': '1.2.3'}]
            MockGet.return_value = result
            t = last_tag('foo', 'bar')
            self.assertEqual(t, '1.2.3')
            MockGet.assert_called_with("https://api.github.com/repos/foo/bar/git/refs/tags/")
            with patch('os.path.basename') as MockBasename:
                MockBasename.side_effect = KeyError('Mock!')
                t = last_tag('foo', 'bar')
                self.assertEqual(t, '0.0.0')

    def test_version(self):
        """Test automated determination of git version.
        """
        from subprocess import PIPE
        #
        # Normal operation.
        #
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            process.returncode = 0
            process.communicate.side_effect = [('1.9.8-12-g39272f3-dirty', ''),
                                               ('598', '')]
            MockPopen.return_value = process
            calls = [call(['git', "describe", "--tags", "--dirty", "--always"],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate(),
                     call(['git', "rev-list", "--count", "HEAD"],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate()]
            v = version()
            self.assertEqual(v, '1.9.8.dev598')
            MockPopen.assert_has_calls(calls)
        #
        # Non-zero returncode
        #
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            type(process).returncode = PropertyMock(return_value=1)
            # process.returncode = 1
            process.communicate.side_effect = [('1.9.8-12-g39272f3-dirty', ''),
                                               ('598', '')]
            MockPopen.return_value = process
            calls = [call(['git', "describe", "--tags", "--dirty", "--always"],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate()]
            v = version()
            self.assertEqual(v, '0.0.1.dev0')
            MockPopen.assert_has_calls(calls)
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            type(process).returncode = PropertyMock(side_effect=(0, 1))
            process.communicate.side_effect = [('1.9.8-12-g39272f3-dirty', ''),
                                               ('598', '')]
            MockPopen.return_value = process
            calls = [call(['git', "describe", "--tags", "--dirty", "--always"],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate(),
                     call(['git', "rev-list", "--count", "HEAD"],
                          universal_newlines=True, stdout=PIPE, stderr=PIPE),
                     call().communicate()]
            v = version()
            self.assertEqual(v, '0.0.1.dev0')
            MockPopen.assert_has_calls(calls)
        #
        # Raise exceptions
        #
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            process.returncode = 0
            process.communicate.side_effect = [('1.9.8-12-g39272f3-dirty', ''),
                                               ('598', '')]
            MockPopen.side_effect = OSError("Mock!")
            v = version()
            self.assertEqual(v, '0.0.1.dev0')
        with patch('subprocess.Popen') as MockPopen:
            process = Mock()
            process.returncode = 0
            process.communicate.side_effect = [('1.9.8-12-g39272f3-dirty', ''),
                                               ('598', '')]
            MockPopen.side_effect = [process, OSError("Mock!")]
            v = version()
            self.assertEqual(v, '0.0.1.dev0')
