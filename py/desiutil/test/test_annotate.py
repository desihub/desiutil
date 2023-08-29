# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.annotate.
"""
import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from ..annotate import csv_unit_column, csv_units, _options


class TestAnnotate(unittest.TestCase):
    """Test desiutil.annotate.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @patch('sys.argv', ['annotate_fits', '--verbose'])
    def test_options(self):
        """Test command-line arguments.
        """
        options = _options()
        self.assertTrue(options.verbose)
        self.assertIsNone(options.csv)
        self.assertEqual(options.extension, '0')

    def test_csv_unit_column(self):
        """Test identification of unit column.
        """
        self.assertEqual(csv_unit_column(['name', 'unit', 'foo', 'bar']), 1)
        self.assertEqual(csv_unit_column(['name', 'Comments', 'foo', 'bar'], comment=True), 1)
        self.assertEqual(csv_unit_column(['Name', 'Type', 'Units', 'Comments', 'bar'], comment=True), 3)
        self.assertEqual(csv_unit_column(['Name', 'Type', 'Units', 'Description'], comment=True), 3)
        with self.assertRaises(IndexError) as e:
            c = csv_unit_column(['Name', 'stuff', 'foo', 'Comments'])
        self.assertEqual(str(e.exception), "No column matching 'unit' found!")
        with self.assertRaises(IndexError) as e:
            c = csv_unit_column(['Name', 'unit', 'foo', 'bar'], comment=True)
        self.assertEqual(str(e.exception), "No column matching 'comment' found!")

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
