# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.annotate.
"""
import os
import hashlib
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch, call
import numpy as np
from astropy.io import fits
from astropy.table import Table, QTable
from ..annotate import (FITSUnitWarning, annotate_fits, annotate_table, find_column_name,
                        find_key_name, validate_unit, check_comment_length, load_csv_units,
                        load_yml_units, _options)


class TestAnnotate(unittest.TestCase):
    """Test desiutil.annotate.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = TemporaryDirectory()
        cls.TMP = cls.tmp.name  # Override this to write to a non-temporary directory.
        cls.maxDiff = None  # Show more verbose differences on errors.
        rng = np.random.default_rng(seed=85719)
        hdu0 = fits.PrimaryHDU()
        hdu0.header.append(('EXTNAME', 'PRIMARY', 'extension name'))
        hdu0.add_checksum()
        image = rng.integers(0, 2**32, (500, 500), dtype=np.uint32)
        hdu1 = fits.ImageHDU(image, name='UNSIGNED')
        hdu1.add_checksum()
        targetid = rng.integers(0, 2**64, (20, ), dtype=np.uint64)
        ra = 360.0 * rng.random((20, ), dtype=np.float64)
        dec = 180.0 * rng.random((20, ), dtype=np.float64) - 90.0
        mag = -2.5 * np.log10(rng.random((20, ), dtype=np.float32))
        columns = fits.ColDefs([fits.Column(name='TARGETID', format='K', bzero=2**63, array=targetid),
                                fits.Column(name='RA', format='D', array=ra),
                                fits.Column(name='DEC', format='D', array=dec),
                                fits.Column(name='MAG', format='E', unit='mag', array=mag)])
        hdu2 = fits.BinTableHDU.from_columns(columns, name='BINTABLE', uint=True)
        hdu2.header.comments['TTYPE1'] = 'Target ID'
        hdu2.header.comments['TTYPE2'] = 'Right Ascension [J2000]'
        hdu2.header.comments['TTYPE3'] = 'Declination [J2000]'
        hdu2.add_checksum()
        image2 = rng.random((500, 500), dtype=np.float32)
        hdu3 = fits.ImageHDU(image, name='FLOAT')
        hdu3.header.append(('BUNIT', 'maggy', 'image unit'))
        hdu3.add_checksum()
        hdulist = fits.HDUList([hdu0, hdu1, hdu2, hdu3])
        cls.fits_file = os.path.join(cls.TMP, 'test_annotate.fits')
        hdulist.writeto(cls.fits_file, overwrite=True)
        with open(cls.fits_file, 'rb') as ff:
            data = ff.read()
        cls.fits_file_sha = hashlib.sha256(data).hexdigest()

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

    def test_find_column_name(self):
        """Test identification of unit column.
        """
        self.assertEqual(find_column_name(['name', 'unit', 'foo', 'bar']), 1)
        self.assertEqual(find_column_name(['name', 'Comments', 'foo', 'bar'], prefix=('comment', 'description')), 1)
        self.assertEqual(find_column_name(['Name', 'Type', 'Units', 'Comments', 'bar'], prefix=('comment', 'description')), 3)
        self.assertEqual(find_column_name(['Name', 'Type', 'Units', 'Description'], prefix=('comment', 'description')), 3)
        with self.assertRaises(IndexError) as e:
            c = find_column_name(['Name', 'stuff', 'foo', 'Comments'])
        self.assertEqual(e.exception.args[0], "No column matching 'unit' found!")
        with self.assertRaises(IndexError) as e:
            c = find_column_name(['Name', 'unit', 'foo', 'bar'], prefix=('comment', 'description'))
        self.assertEqual(e.exception.args[0], "No column matching 'comment' found!")

    def test_find_key_name(self):
        """Test identification of unit column in YAML.
        """
        self.assertEqual(find_key_name({'unit': {'RA': 'deg', 'DEC': 'deg', 'COLUMN': None}}), 'unit')
        self.assertEqual(find_key_name({'Units': {'RA': 'deg', 'DEC': 'deg', 'COLUMN': None}}), 'Units')
        self.assertEqual(find_key_name({'comment': {'RA': 'deg', 'DEC': 'deg', 'COLUMN': 'foo'}}, prefix=('comment', 'description')), 'comment')
        self.assertEqual(find_key_name({'DESCRIPTION': {'RA': 'deg', 'DEC': 'deg', 'COLUMN': 'foo'}}, prefix=('comment', 'description')), 'DESCRIPTION')
        with self.assertRaises(KeyError) as e:
            k = find_key_name({'RA': 'deg', 'DEC': 'deg', 'COLUMN': None})
        self.assertEqual(e.exception.args[0], "No key matching 'unit' found!")
        with self.assertRaises(KeyError) as e:
            k = find_key_name({'RA': 'deg', 'DEC': 'deg', 'COLUMN': None}, prefix=('comment', 'description'))
        self.assertEqual(e.exception.args[0], "No key matching 'comment' found!")

    def test_validate_unit(self):
        """Test function to validate units.
        """
        m = "'ergs' did not parse as fits unit: At col 0, Unit 'ergs' not supported by the FITS standard. Did you mean erg?"
        d = "'1/deg^2' did not parse as fits unit: Numeric factor not supported by FITS"
        f = "'1/nanomaggy^2' did not parse as fits unit: Numeric factor not supported by FITS"
        l = " If this is meant to be a custom unit, define it with 'u.def_unit'. To have it recognized inside a file reader or other code, enable it with 'u.add_enabled_units'. For details, see https://docs.astropy.org/en/latest/units/combining_and_defining.html"
        c = validate_unit(None)
        self.assertIsNone(c)
        c = validate_unit('erg')
        self.assertIsNone(c)
        with self.assertWarns(FITSUnitWarning) as w:
            c = validate_unit('ergs', error=False)
        self.assertEqual(str(w.warning), m + l)
        self.assertIsNone(c)
        with self.assertWarns(FITSUnitWarning) as w:
            c = validate_unit('1/deg^2')
        self.assertEqual(str(w.warning), d + l)
        self.assertIsNone(c)
        c = validate_unit('nanomaggies', error=True)
        self.assertEqual(c, "'nanomaggies'")
        with self.assertRaises(ValueError) as e:
            c = validate_unit('ergs', error=True)
        self.assertEqual(str(e.exception), m + l)
        with self.assertRaises(ValueError) as e:
            c = validate_unit('1/nanomaggy^2', error=True)
        self.assertEqual(str(e.exception), f + l)

    @patch('desiutil.annotate.get_logger')
    def test_check_comment_length(self, mock_log):
        comments = {'COLUMN1': 'x'*45,
                    'COLUMN2': 'y'*46,
                    'COLUMN3': 'z'*47,
                    'COLUMN4': 'w'*49}
        with self.assertRaises(ValueError) as e:
            n_long = check_comment_length(comments)
        self.assertEqual(str(e.exception), "2 long comments detected!")
        mock_log().error.assert_has_calls([call("'%s' comment too long: '%s'!", 'COLUMN3', comments['COLUMN3']),
                                           call("'%s' comment too long: '%s'!", 'COLUMN4', comments['COLUMN4'])])
        n_long = check_comment_length(comments, error=False)
        self.assertEqual(n_long, 2)
        mock_log().warning.assert_has_calls([call("Long comment detected for '%s', will be truncated to '%s'!",
                                                  'COLUMN3', 'z'*46),
                                             call("Long comment detected for '%s', will be truncated to '%s'!",
                                                  'COLUMN4', 'w'*46)])

    @patch('desiutil.annotate.get_logger')
    def test_load_csv_units(self, mock_log):
        """Test parsing of units in a CSV file.
        """
        c = """Name,Type,Unit,Comment
COLUMN1,int16,,This is a comment.
RA,float32,deg,Right Ascension
DEC,float32,deg,Declination"""
        unitsFile = os.path.join(self.TMP, 'test_one.csv')
        with open(unitsFile, 'w', newline='') as f:
            f.write(c)
        units, comments = load_csv_units(unitsFile)
        self.assertEqual(units['RA'], 'deg')
        self.assertEqual(units['COLUMN1'], '')
        self.assertEqual(comments['COLUMN1'], 'This is a comment.')

    @patch('desiutil.annotate.get_logger')
    def test_load_csv_units_no_comment(self, mock_log):
        """Test parsing of units in a CSV file without comments.
        """
        c = """Name,Type,Unit
COLUMN1,int16,
RA,float32,deg
DEC,float32,deg"""
        unitsFile = os.path.join(self.TMP, 'test_two.csv')
        with open(unitsFile, 'w', newline='') as f:
            f.write(c)
        units, comments = load_csv_units(unitsFile)
        self.assertEqual(units['RA'], 'deg')
        self.assertEqual(units['COLUMN1'], '')
        self.assertFalse(bool(comments))

    @patch('desiutil.annotate.get_logger')
    def test_load_csv_units_no_units(self, mock_log):
        """Test parsing of units in a CSV file with bad units.
        """
        c = """Name,Type,Foobar
COLUMN1,int16,
RA,float32,deg
DEC,float32,deg"""
        unitsFile = os.path.join(self.TMP, 'test_three.csv')
        with open(unitsFile, 'w', newline='') as f:
            f.write(c)
        with self.assertRaises(ValueError) as e:
            units, comments = load_csv_units(unitsFile)
        self.assertEqual(str(e.exception), f"{unitsFile} does not have a unit column!")

    @patch('desiutil.annotate.get_logger')
    def test_load_yml_units(self, mock_log):
        """Test parsing of YAML input.
        """
        y = """unit:
    RA: deg
    DEC: deg
    COLUMN:
"""
        unitsFile = os.path.join(self.TMP, 'test_one.yml')
        with open(unitsFile, 'w', newline='') as f:
            f.write(y)
        units, comments = load_yml_units(unitsFile)
        self.assertEqual(units['RA'], 'deg')
        self.assertIsNone(units['COLUMN'])
        self.assertFalse(bool(comments))
        mock_log().warning.assert_not_called()

    @patch('desiutil.annotate.get_logger')
    def test_load_yml_units_backward(self, mock_log):
        """Test parsing of older-style YAML input.
        """
        y = """RA: deg
DEC: deg
COLUMN:
"""
        unitsFile = os.path.join(self.TMP, 'test_one.yml')
        with open(unitsFile, 'w', newline='') as f:
            f.write(y)
        units, comments = load_yml_units(unitsFile)
        self.assertEqual(units['RA'], 'deg')
        self.assertIsNone(units['COLUMN'])
        self.assertFalse(bool(comments))
        mock_log().warning.assert_called_once_with(f'{unitsFile} does not have a unit column, assuming keys are columns!')

    @patch('desiutil.annotate.get_logger')
    def test_load_yml_units_comments(self, mock_log):
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
        unitsFile = os.path.join(self.TMP, 'test_one.yml')
        with open(unitsFile, 'w', newline='') as f:
            f.write(y)
        units, comments = load_yml_units(unitsFile)
        self.assertEqual(comments['RA'], 'deg')
        self.assertEqual(comments['COLUMN'], 'dimensionless')
        mock_log().warning.assert_not_called()

    @patch('desiutil.annotate.get_logger')
    def test_annotate_table(self, mock_log):
        """Test adding units to table columns.
        """
        t = Table()
        t['a'] = [1.0, 4.0]
        t['b'] = [2.14, 5.67]
        t['c'] = ['x', 'y']
        t['d'] = np.array([123, 456], dtype=np.uint64)
        t['f'] = np.array([-15, 76], dtype=np.int16)
        u = {'a': 'm', 'b': 'deg', 'c': '', 'd': '', 'e': 'arcsec'}
        tt = annotate_table(t, u)
        self.assertEqual(tt['a'].unit, 'm')
        self.assertEqual(tt['b'].unit, 'deg')
        mock_log().debug.assert_has_calls([call("t['%s'].unit = '%s'", 'a', 'm'),
                                           call("t['%s'].unit = '%s'", 'b', 'deg'),
                                           call("Not setting blank unit for column '%s'.", 'c'),
                                           call("Not setting blank unit for column '%s'.", 'd'),
                                           call("Column '%s' not present in table.", 'e')])
        mock_log().info.assert_called_once_with("Column '%s' not found in units argument.", 'f')

    @patch('desiutil.annotate.get_logger')
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

    @patch('desiutil.annotate.get_logger')
    def test_annotate_qtable(self, mock_log):
        """Test adding units to qtable columns.
        """
        t = QTable()
        t['a'] = [1.0, 4.0]
        t['b'] = [2.14, 5.67]
        t['c'] = ['x', 'y']
        t['d'] = np.array([123, 456], dtype=np.uint64)
        t['f'] = np.array([-15, 76], dtype=np.int16)
        u = {'a': 'm', 'b': 'deg', 'c': '', 'd': '', 'e': 'arcsec'}
        tt = annotate_table(t, u)
        self.assertEqual(tt['a'].unit, 'm')
        self.assertEqual(tt['b'].unit, 'deg')
        mock_log().debug.assert_has_calls([call("t['%s'].unit = '%s'", 'a', 'm'),
                                           call("t['%s'].unit = '%s'", 'b', 'deg'),
                                           call("Not setting blank unit for column '%s'.", 'c'),
                                           call("Not setting blank unit for column '%s'.", 'd'),
                                           call("Column '%s' not present in table.", 'e')])
        mock_log().info.assert_called_once_with("Column '%s' not found in units argument.", 'f')

    @patch('desiutil.annotate.get_logger')
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
        mock_log().debug.assert_has_calls([call("t['%s'].unit = '%s'", 'a', 'cm'),
                                           call("t.replace_column('%s', t['%s'].to('%s'))", 'a', 'a', 'cm'),
                                           call("t['%s'].unit = '%s'", 'b', 'deg'),
                                           call("Not setting blank unit for column '%s'.", 'c'),
                                           call("Not setting blank unit for column '%s'.", 'd'),
                                           call("Column '%s' not present in table.", 'e')])
        mock_log().info.assert_not_called()

    @patch('desiutil.annotate.get_logger')
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
        mock_log().debug.assert_has_calls([call("t['%s'].unit = '%s'", 'a', 'A'),
                                           call("t.replace_column('%s', t['%s'].to('%s'))", 'a', 'a', 'A'),
                                           call("t['%s'].unit = '%s'", 'b', 'deg'),
                                           call("Not setting blank unit for column '%s'.", 'c'),
                                           call("Not setting blank unit for column '%s'.", 'd'),
                                           call("Column '%s' not present in table.", 'e')])
        mock_log().info.assert_not_called()
        mock_log().error.assert_has_calls([call("Cannot add or replace unit '%s' to column '%s'!", 'A', 'a')])

    def test_identical_copy(self):
        """Test hdulist.copy().
        """
        new_hdulist_name = os.path.join(self.TMP, 'test_annotate_copy.fits')
        with fits.open(self.fits_file, mode='readonly') as hdulist:
            new_hdulist = hdulist.copy()
            new_hdulist.writeto(new_hdulist_name, overwrite=True)
        with open(new_hdulist_name, 'rb') as ff:
            data = ff.read()
        new_sha = hashlib.sha256(data).hexdigest()
        self.assertEqual(self.fits_file_sha, new_sha)

    @unittest.expectedFailure
    def test_identical_deepcopy(self):
        """Test hdulist.__deepcopy__().
        """
        new_hdulist_name = os.path.join(self.TMP, 'test_annotate_deepcopy.fits')
        with fits.open(self.fits_file, mode='readonly') as hdulist:
            new_hdulist = hdulist.__deepcopy__()
        new_hdulist.writeto(new_hdulist_name, overwrite=True)
        with open(new_hdulist_name, 'rb') as ff:
            data = ff.read()
        new_sha = hashlib.sha256(data).hexdigest()
        self.assertEqual(self.fits_file_sha, new_sha)

    @patch('desiutil.annotate.get_logger')
    def test_annotate_fits(self, mock_log):
        """Test adding units to a binary table.
        """
        new_hdulist_name = os.path.join(self.TMP, 'test_annotate_update1.fits')
        new_hdulist = annotate_fits(self.fits_file, 2, new_hdulist_name, units={'RA': 'deg', 'DEC': 'deg'}, overwrite=True)
        self.assertIn('TUNIT2', new_hdulist[2].header)
        self.assertIn('TUNIT3', new_hdulist[2].header)
        self.assertEqual(new_hdulist[2].header['TUNIT2'], 'deg')
        self.assertEqual(new_hdulist[2].header['TUNIT3'], 'deg')
        new_hdulist_name = os.path.join(self.TMP, 'test_annotate_update2.fits')
        new_hdulist = annotate_fits(self.fits_file, 2, new_hdulist_name, units={'MAG': 'nJy'}, overwrite=True)
        self.assertIn('TUNIT4', new_hdulist[2].header)
        self.assertEqual(new_hdulist[2].header['TUNIT4'], 'nJy')
        mock_log().warning.assert_called_once_with("Overriding units for column '%s': '%s' -> '%s'.", 'MAG', 'mag', 'nJy')

    @patch('desiutil.annotate.get_logger')
    def test_annotate_fits_comments(self, mock_log):
        """Test adding comments to a binary table.
        """
        new_hdulist_name = os.path.join(self.TMP, 'test_annotate_update_comments.fits')
        new_hdulist = annotate_fits(self.fits_file, 2, new_hdulist_name, comments={'RA': 'RA', 'DEC': 'DEC'}, overwrite=True, verbose=True)
        self.assertEqual(new_hdulist[2].header.comments['TTYPE2'], 'RA')
        self.assertEqual(new_hdulist[2].header.comments['TTYPE3'], 'DEC')
        mock_log().warning.assert_has_calls([call("Overriding comment on column '%s': '%s' -> '%s'.", 'RA', 'Right Ascension [J2000]', 'RA'),
                                             call("Overriding comment on column '%s': '%s' -> '%s'.", 'DEC', 'Declination [J2000]', 'DEC')])
        mock_log().debug.assert_has_calls([call('Set %s comment to "%s"', 'RA', 'RA'),
                                           call('Set %s comment to "%s"', 'DEC', 'DEC')])

    def test_annotate_fits_image(self):
        """Test adding units to an image.
        """
        new_hdulist_name = os.path.join(self.TMP, 'test_annotate_image1.fits')
        with self.assertRaises(TypeError) as e:
            new_hdulist = annotate_fits(self.fits_file, 1, new_hdulist_name, units={'bunit': 'ADU'}, overwrite=True)
        self.assertEqual(e.exception.args[0], "Adding units to objects other than fits.BinTableHDU is not supported!")

    def test_annotate_fits_missing(self):
        """Test adding units to a missing HDU.
        """
        new_hdulist_name = os.path.join(self.TMP, 'test_annotate_update.fits')
        with self.assertRaises(ValueError) as e:
            annotate_fits(self.fits_file, 2, new_hdulist_name)
        self.assertEqual(str(e.exception), "No input units or comments specified!")
        with self.assertRaises(IndexError) as e:
            annotate_fits(self.fits_file, 9, new_hdulist_name, units={'RA': 'deg', 'DEC': 'deg'})
        self.assertEqual(str(e.exception), "list index out of range")
        with self.assertRaises(KeyError) as e:
            annotate_fits(self.fits_file, 'MISSING', new_hdulist_name, units={'RA': 'deg', 'DEC': 'deg'})
        self.assertEqual(e.exception.args[0], "Extension 'MISSING' not found.")
