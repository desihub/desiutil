# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.io.
"""
import unittest
import os
import stat
import sys
from tempfile import TemporaryDirectory
import numpy as np
from astropy.table import Table
from ..io import combine_dicts, decode_table, encode_table, yamlify, unlock_file


class TestIO(unittest.TestCase):
    """Test desiutil.io
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_endecode_table(self):
        """Test encoding / decoding round-trip with numpy structured array.
        """
        data = np.zeros(4, dtype=[(str('x'), 'U4'), (str('y'), 'f8')])
        data['x'] = 'ab'  # purposefully have fewer characters than width
        data['y'] = np.arange(len(data))
        t1 = encode_table(data)
        self.assertEqual(t1['x'].dtype.kind, 'S')
        self.assertEqual(t1['y'].dtype.kind, data['y'].dtype.kind)
        self.assertTrue(np.all(t1['y'] == data['y']))
        t2 = decode_table(t1, native=False)
        self.assertEqual(t2['x'].dtype.kind, 'U')
        self.assertEqual(t2['x'].dtype, data['x'].dtype)
        self.assertEqual(t2['y'].dtype.kind, data['y'].dtype.kind)
        self.assertTrue(np.all(t2['x'] == data['x']))
        self.assertTrue(np.all(t2['y'] == data['y']))

        # have to give an encoding
        with self.assertRaises(UnicodeError):
            tx = encode_table(data, encoding=None)

        del t1.meta['ENCODING']
        with self.assertRaises(UnicodeError):
            tx = decode_table(t1, encoding=None, native=False)

        # Test encoding / decoding round-trip with Table
        data = Table()
        data['x'] = np.asarray(['a', 'bb', 'ccc'], dtype='U')
        data['y'] = np.arange(len(data['x']))

        t1 = encode_table(data)
        self.assertEqual(t1['x'].dtype.kind, 'S')
        self.assertEqual(t1['y'].dtype.kind, data['y'].dtype.kind)
        self.assertTrue(np.all(t1['y'] == data['y']))
        t2 = decode_table(t1, native=False)
        self.assertEqual(t2['x'].dtype.kind, 'U')
        self.assertEqual(t2['y'].dtype.kind, data['y'].dtype.kind)
        self.assertTrue(np.all(t2['x'] == data['x']))
        self.assertTrue(np.all(t2['y'] == data['y']))

        # Non-default encoding with non-ascii unicode
        data['x'][0] = 'µ'
        t1 = encode_table(data, encoding='utf-8')
        self.assertEqual(t1.meta['ENCODING'], 'utf-8')
        t2 = decode_table(t1, encoding=None, native=False)
        self.assertEqual(t2.meta['ENCODING'], 'utf-8')
        self.assertTrue(np.all(t2['x'] == data['x']))
        with self.assertRaises(UnicodeEncodeError):
            tx = encode_table(data, encoding='ascii')
        with self.assertRaises(UnicodeDecodeError):
            with self.assertWarnsRegex(UserWarning, r"(?m)data\.metadata\['ENCODING'\]=='utf-8' does not match option 'ascii';\nuse encoding=None to use data\.metadata\['ENCODING'\] instead") as uw:
                tx = decode_table(t1, encoding='ascii', native=False)

        # Table can specify encoding if option encoding=None
        data['x'][0] = 'p'
        data.meta['ENCODING'] = 'utf-8'
        t1 = encode_table(data, encoding=None)
        self.assertEqual(t1.meta['ENCODING'], 'utf-8')
        t2 = decode_table(t1, native=False, encoding=None)
        self.assertEqual(t2.meta['ENCODING'], 'utf-8')

        # conflicting encodings print warning but still proceed
        with self.assertWarnsRegex(UserWarning, r"(?m)data\.metadata\['ENCODING'\]=='utf-8' does not match option 'ascii';\nuse encoding=None to use data\.metadata\['ENCODING'\] instead") as uw:
            t1 = encode_table(data, encoding='ascii')
        self.assertEqual(t1.meta['ENCODING'], 'ascii')
        with self.assertWarnsRegex(UserWarning, r"(?m)data\.metadata\['ENCODING'\]=='ascii' does not match option 'utf-8';\nuse encoding=None to use data\.metadata\['ENCODING'\] instead") as uw:
            t2 = decode_table(t1, encoding='utf-8', native=False)
        self.assertEqual(t2.meta['ENCODING'], 'utf-8')

        # native=True should retain native str type
        data = Table()
        data['x'] = np.asarray(['a', 'bb', 'ccc'], dtype='S')
        data['y'] = np.arange(len(data['x']))
        native_str_kind = np.str_('a').dtype.kind
        tx = decode_table(data, native=True)
        self.assertIsInstance(tx['x'][0], str)

        # Test roundtype with 2D array and unsigned ints
        data = np.zeros(4, dtype=[(str('x'), ('U8', 3)), (str('y'), 'u8')])
        data['y'] = np.arange(len(data))
        data['x'][0] = ['a', 'bb', 'c']
        data['x'][1] = ['x', 'yy', 'z']
        t1 = encode_table(data)
        self.assertEqual(t1['x'].dtype.kind, 'S')
        self.assertEqual(t1['y'].dtype.kind, data['y'].dtype.kind)
        self.assertTrue(np.all(t1['y'] == data['y']))
        t2 = decode_table(t1, native=False)
        self.assertEqual(t2['x'].dtype.kind, 'U')
        self.assertEqual(t2['x'].dtype, data['x'].dtype)
        self.assertEqual(t2['y'].dtype.kind, data['y'].dtype.kind)
        self.assertTrue(np.all(t2['x'] == data['x']))
        self.assertTrue(np.all(t2['y'] == data['y']))

    def test_yamlify(self):
        """Test yamlify
        """
        fdict = {'name': 'test', 'num': np.int32(3),
                 1: 'expid', 'flt32': np.float32(3.), 'flt64': np.float64(2.),
                 'num2': np.int64(4), 'bool': np.bool_(True),
                 'lst': ['tst2', np.int16(2)],
                 'tup': (1, 3), 'dct': {'a': 'tst3', 'b': np.float32(6.)},
                 'npstring' : np.str_('abcd'),
                 'array': np.zeros(10)}
        self.assertIsInstance(fdict['name'], str)
        # Run
        ydict = yamlify(fdict)
        self.assertIsInstance(ydict['flt32'], float)
        self.assertIsInstance(ydict['array'], list)
        for key in ydict.keys():
            if isinstance(key, str):
                # This looks a little silly, but in fact, some of the keys
                # are integers not strings.
                self.assertIsInstance(key, str)
            else:
                self.assertIsInstance(key, int)

    def test_combinedicts(self):
        """Test combining dicts
        """
        # Merge two dicts with a common key
        dict1 = {'a': {'b': 2, 'c': 3}}
        dict2 = {'a': {'d': 4}}
        dict3 = combine_dicts(dict1, dict2)
        self.assertEqual(dict3, {'a': {'b': 2, 'c': 3, 'd': 4}})
        # Shouldn't modify originals
        self.assertEqual(dict1, {'a': {'b': 2, 'c': 3}})
        self.assertEqual(dict2, {'a': {'d': 4}})
        # Merge two dicts with different keys
        dict1 = {'a': 2}
        dict2 = {'b': 4}
        dict3 = combine_dicts(dict1, dict2)
        self.assertEqual(dict3, {'a': 2, 'b': 4})
        self.assertEqual(dict1, {'a': 2})
        self.assertEqual(dict2, {'b': 4})
        # Overlapping leafs that are scalars should raise an error
        dict1 = {'a': 2}
        dict2 = {'a': 4}
        with self.assertRaises(ValueError):
            dict3 = combine_dicts(dict1, dict2)
        # Overlapping leafs with a scalar/dict mix raise an error
        dict1 = {'a': {'b': 3}}
        dict2 = {'a': {'b': 2, 'c': 3}}
        with self.assertRaises(ValueError):
            combine_dicts(dict1, dict2)
        with self.assertRaises(ValueError):
            combine_dicts(dict2, dict1)
        # Deep merge
        dict1 = {'a': {'b': {'x': 1, 'y': 2}}}
        dict2 = {'a': {'b': {'p': 3, 'q': 4}}}
        dict3 = combine_dicts(dict1, dict2)
        self.assertEqual(dict3, {'a': {'b': {'x': 1, 'y': 2, 'p': 3, 'q': 4}}})
        self.assertEqual(dict1, {'a': {'b': {'x': 1, 'y': 2}}})
        self.assertEqual(dict2, {'a': {'b': {'p': 3, 'q': 4}}})

    def test_unlock_file(self):
        """Test the permission unlock file manager.
        """
        fff = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        www = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
        with TemporaryDirectory() as dirname:
            filename = os.path.join(dirname, 'tempfile')
            with open(filename, 'wb') as f:
                f.write(b'Content\n')
            s0 = os.stat(filename)
            ro = stat.S_IFMT(s0.st_mode) | fff
            os.chmod(filename, ro)
            s1 = os.stat(filename)
            self.assertEqual(stat.S_IMODE(s1.st_mode), fff)
            with unlock_file(filename, 'ab') as f:
                f.write(b'More content\n')
                s2 = os.stat(filename)
                self.assertEqual(stat.S_IMODE(s2.st_mode), fff | stat.S_IWUSR)
            s3 = os.stat(filename)
            self.assertEqual(stat.S_IMODE(s3.st_mode), fff)
            filename = os.path.join(dirname, 'newfile')
            with unlock_file(filename, 'wb') as f:
                f.write(b'Some content\n')
            s0 = os.stat(filename)
            self.assertEqual(stat.S_IMODE(s0.st_mode) & www, 0)
