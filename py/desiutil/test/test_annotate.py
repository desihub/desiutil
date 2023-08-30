# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.annotate.
"""
import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch, call
import numpy as np
from astropy.table import Table, QTable
from ..annotate import annotate_table, csv_unit_column, csv_units, yml_unit_key, yml_units, _options


class TestAnnotate(unittest.TestCase):
    """Test desiutil.annotate.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @patch('sys.argv', ['annotate_fits', '--verbose', 'fits_file.fits'])
    def test_options(self):
        """Test command-line arguments.
        """
        options = _options()
        self.assertTrue(options.verbose)
        self.assertIsNone(options.csv)
        self.assertEqual(options.extension, '1')
        self.assertEqual(options.fits, 'fits_file.fits')

    def test_csv_unit_column(self):
        """Test identification of unit column.
        """
        self.assertEqual(csv_unit_column(['name', 'unit', 'foo', 'bar']), 1)
        self.assertEqual(csv_unit_column(['name', 'Comments', 'foo', 'bar'], comment=True), 1)
        self.assertEqual(csv_unit_column(['Name', 'Type', 'Units', 'Comments', 'bar'], comment=True), 3)
        self.assertEqual(csv_unit_column(['Name', 'Type', 'Units', 'Description'], comment=True), 3)
        with self.assertRaises(IndexError) as e:
            c = csv_unit_column(['Name', 'stuff', 'foo', 'Comments'])
        self.assertEqual(e.exception.args[0], "No column matching 'unit' found!")
        with self.assertRaises(IndexError) as e:
            c = csv_unit_column(['Name', 'unit', 'foo', 'bar'], comment=True)
        self.assertEqual(e.exception.args[0], "No column matching 'comment' found!")

    @patch('desiutil.annotate.log')
    def test_csv_units(self, mock_log):
        """Test parsing of units in a CSV file.
        """
        c = """Name,Type,Unit,Comment
COLUMN1,int16,,This is a comment.
RA,float32,deg,Right Ascension
DEC,float32,deg,Declination"""
        unitsFile = os.path.join(self.tmp.name, 'test_one.csv')
        with open(unitsFile, 'w', newline='') as f:
            f.write(c)
        units, comments = csv_units(unitsFile)
        self.assertEqual(units['RA'], 'deg')
        self.assertEqual(units['COLUMN1'], '')
        self.assertEqual(comments['COLUMN1'], 'This is a comment.')

    @patch('desiutil.annotate.log')
    def test_csv_units_no_comment(self, mock_log):
        """Test parsing of units in a CSV file without comments.
        """
        c = """Name,Type,Unit
COLUMN1,int16,
RA,float32,deg
DEC,float32,deg"""
        unitsFile = os.path.join(self.tmp.name, 'test_two.csv')
        with open(unitsFile, 'w', newline='') as f:
            f.write(c)
        units, comments = csv_units(unitsFile)
        self.assertEqual(units['RA'], 'deg')
        self.assertEqual(units['COLUMN1'], '')
        self.assertFalse(bool(comments))

    @patch('desiutil.annotate.log')
    def test_csv_units_no_units(self, mock_log):
        """Test parsing of units in a CSV file with bad units.
        """
        c = """Name,Type,Foobar
COLUMN1,int16,
RA,float32,deg
DEC,float32,deg"""
        unitsFile = os.path.join(self.tmp.name, 'test_three.csv')
        with open(unitsFile, 'w', newline='') as f:
            f.write(c)
        with self.assertRaises(ValueError) as e:
            units, comments = csv_units(unitsFile)
        self.assertEqual(str(e.exception), f"{unitsFile} does not have a unit column!")

    def test_yml_unit_key(self):
        """Test identification of unit column in YAML.
        """
        self.assertEqual(yml_unit_key({'unit': {'RA': 'deg', 'DEC': 'deg', 'COLUMN': None}}), 'unit')
        self.assertEqual(yml_unit_key({'Units': {'RA': 'deg', 'DEC': 'deg', 'COLUMN': None}}), 'Units')
        self.assertEqual(yml_unit_key({'comment': {'RA': 'deg', 'DEC': 'deg', 'COLUMN': 'foo'}}, comment=True), 'comment')
        self.assertEqual(yml_unit_key({'DESCRIPTION': {'RA': 'deg', 'DEC': 'deg', 'COLUMN': 'foo'}}, comment=True), 'DESCRIPTION')
        with self.assertRaises(KeyError) as e:
            k = yml_unit_key({'RA': 'deg', 'DEC': 'deg', 'COLUMN': None})
        self.assertEqual(e.exception.args[0], "No key matching 'unit' found!")
        with self.assertRaises(KeyError) as e:
            k = yml_unit_key({'RA': 'deg', 'DEC': 'deg', 'COLUMN': None}, comment=True)
        self.assertEqual(e.exception.args[0], "No key matching 'comment' found!")

    @patch('desiutil.annotate.log')
    def test_yml_units(self, mock_log):
        """Test parsing of YAML input.
        """
        y = """unit:
    RA: deg
    DEC: deg
    COLUMN:
"""
        unitsFile = os.path.join(self.tmp.name, 'test_one.yml')
        with open(unitsFile, 'w', newline='') as f:
            f.write(y)
        units, comments = yml_units(unitsFile)
        self.assertEqual(units['RA'], 'deg')
        self.assertIsNone(units['COLUMN'])
        self.assertFalse(bool(comments))
        mock_log.warning.assert_not_called()

    @patch('desiutil.annotate.log')
    def test_yml_units_backward(self, mock_log):
        """Test parsing of older-style YAML input.
        """
        y = """RA: deg
DEC: deg
COLUMN:
"""
        unitsFile = os.path.join(self.tmp.name, 'test_one.yml')
        with open(unitsFile, 'w', newline='') as f:
            f.write(y)
        units, comments = yml_units(unitsFile)
        self.assertEqual(units['RA'], 'deg')
        self.assertIsNone(units['COLUMN'])
        self.assertFalse(bool(comments))
        mock_log.warning.assert_called_once_with(f'{unitsFile} does not have a unit column, assuming keys are columns!')

    @patch('desiutil.annotate.log')
    def test_yml_units_comments(self, mock_log):
        """Test parsing of YAML input with units and comments.
        """
        y = """unit:
    RA: deg
    DEC: deg
    COLUMN:
Comments:
    RA: deg
    DEC: deg
    COLUMN: dimensionless
"""
        unitsFile = os.path.join(self.tmp.name, 'test_one.yml')
        with open(unitsFile, 'w', newline='') as f:
            f.write(y)
        units, comments = yml_units(unitsFile)
        self.assertEqual(comments['RA'], 'deg')
        self.assertEqual(comments['COLUMN'], 'dimensionless')
        mock_log.warning.assert_not_called()

    @patch('desiutil.annotate.log')
    def test_annotate_table(self, mock_log):
        """Test adding units to table columns.
        """
        t = Table()
        t['a'] = [1.0, 4.0]
        t['b'] = [2.14, 5.67]
        t['c'] = ['x', 'y']
        t['d'] = np.array([123, 456], dtype=np.uint64)
        u = {'a': 'm', 'b': 'deg', 'c': '', 'd': '', 'e': 'arcsec'}
        tt = annotate_table(t, u)
        self.assertEqual(tt['a'].unit, 'm')
        self.assertEqual(tt['b'].unit, 'deg')
        mock_log.debug.assert_has_calls([call("t['%s'].unit = '%s'", 'a', 'm'),
                                         call("t['%s'].unit = '%s'", 'b', 'deg')])
        mock_log.info.assert_has_calls([call("Not setting blank unit for column '%s'.", 'c'),
                                        call("Not setting blank unit for column '%s'.", 'd'),
                                        call("Column '%s' not present in table.", 'e')])

    @patch('desiutil.annotate.log')
    def test_annotate_table_inplace(self, mock_log):
        """Test adding units to table columns.
        """
        t = Table()
        t['a'] = [1.0, 4.0]
        t['b'] = [2.14, 5.67]
        t['c'] = ['x', 'y']
        t['d'] = np.array([123, 456], dtype=np.uint64)
        u = {'a': 'm', 'b': 'deg', 'c': '', 'd': '', 'e': 'arcsec'}
        tt = annotate_table(t, u, inplace=True)
        self.assertEqual(t['a'].unit, 'm')
        self.assertEqual(t['b'].unit, 'deg')
        self.assertIs(t, tt)

    @patch('desiutil.annotate.log')
    def test_annotate_qtable(self, mock_log):
        """Test adding units to qtable columns.
        """
        t = QTable()
        t['a'] = [1.0, 4.0]
        t['b'] = [2.14, 5.67]
        t['c'] = ['x', 'y']
        t['d'] = np.array([123, 456], dtype=np.uint64)
        u = {'a': 'm', 'b': 'deg', 'c': '', 'd': '', 'e': 'arcsec'}
        tt = annotate_table(t, u)
        self.assertEqual(tt['a'].unit, 'm')
        self.assertEqual(tt['b'].unit, 'deg')
        mock_log.debug.assert_has_calls([call("t['%s'].unit = '%s'", 'a', 'm'),
                                         call("t['%s'].unit = '%s'", 'b', 'deg')])
        mock_log.info.assert_has_calls([call("Not setting blank unit for column '%s'.", 'c'),
                                        call("Not setting blank unit for column '%s'.", 'd'),
                                        call("Column '%s' not present in table.", 'e')])

    @patch('desiutil.annotate.log')
    def test_annotate_qtable_with_units_present(self, mock_log):
        """Test adding units to table columns with existing units.
        """
        t = QTable()
        t['a'] = [1.0, 4.0]
        t['b'] = [2.14, 5.67]
        t['c'] = ['x', 'y']
        t['d'] = np.array([123, 456], dtype=np.uint64)
        t['a'].unit = 'm'
        u = {'a': 'cm', 'b': 'deg', 'c': '', 'd': '', 'e': 'arcsec'}
        tt = annotate_table(t, u)
        self.assertEqual(tt['a'].unit, 'cm')
        self.assertEqual(tt['b'].unit, 'deg')
        mock_log.debug.assert_has_calls([call("t['%s'].unit = '%s'", 'a', 'cm'),
                                         call("t.replace_column('%s', t['%s'].to('%s'))", 'a', 'a', 'cm'),
                                         call("t['%s'].unit = '%s'", 'b', 'deg')])
        mock_log.info.assert_has_calls([call("Not setting blank unit for column '%s'.", 'c'),
                                        call("Not setting blank unit for column '%s'.", 'd'),
                                        call("Column '%s' not present in table.", 'e')])

    @patch('desiutil.annotate.log')
    def test_annotate_qtable_with_units_present_bad_conversion(self, mock_log):
        """Test adding units to table columns with existing units.
        """
        t = QTable()
        t['a'] = [1.0, 4.0]
        t['b'] = [2.14, 5.67]
        t['c'] = ['x', 'y']
        t['d'] = np.array([123, 456], dtype=np.uint64)
        t['a'].unit = 'm'
        u = {'a': 'A', 'b': 'deg', 'c': '', 'd': '', 'e': 'arcsec'}
        tt = annotate_table(t, u)
        self.assertEqual(tt['a'].unit, 'm')
        self.assertEqual(tt['b'].unit, 'deg')
        mock_log.debug.assert_has_calls([call("t['%s'].unit = '%s'", 'a', 'A'),
                                         call("t.replace_column('%s', t['%s'].to('%s'))", 'a', 'a', 'A'),
                                         call("t['%s'].unit = '%s'", 'b', 'deg')])
        mock_log.info.assert_has_calls([call("Not setting blank unit for column '%s'.", 'c'),
                                        call("Not setting blank unit for column '%s'.", 'd'),
                                        call("Column '%s' not present in table.", 'e')])
        mock_log.error.assert_has_calls([call("Cannot add or replace unit '%s' to column '%s'!", 'A', 'a')])
