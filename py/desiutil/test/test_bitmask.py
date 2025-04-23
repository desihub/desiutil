# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.bitmask.
"""
import unittest
from ..bitmask import BitMask, _MaskBit
import yaml
import numpy as np

_bitdefyaml = """\
ccdmask:
  - [BAD,              0, "Pre-determined bad pixel (any reason)"]
  - [HOT,              1, "Hot pixel", {'blat': 'foo'}]
  - [DEAD,             2, "Dead pixel"]
  - [SATURATED,        3, "Saturated pixel from object"]
  - [COSMIC,           4, "Cosmic ray"]"""
_bitdefs = yaml.safe_load(_bitdefyaml)

# Has extra that isn't a dict
_baddef1 = yaml.safe_load("""
#- CCD pixel mask
ccdmask:
    - [BAD,       0, "Pre-determined bad pixel (any reason)"]
    - [HOT,       1, "Hot pixel", 1]
""")


class TestBitMask(unittest.TestCase):
    """Test desiutil.bitmask.
    """

    def setUp(self):
        self.ccdmask = BitMask('ccdmask', _bitdefs)

    def tearDown(self):
        pass

    def test_names(self):
        """Test consistency for names to bits to masks.
        """
        m = self.ccdmask
        for name in m.names():
            self.assertEqual(m.mask(name), 2**m.bitnum(name),
                             'Failed matching mask to bitnum for ' + name)
            self.assertEqual(m.mask(name), m.mask(m.bitnum(name)),
                             'Failed matching mask to name for ' + name)
            self.assertEqual(m.bitname(m.bitnum(name)), name,
                             'Failed bit name->num->name roundtrip for ' +
                             name)
            self.assertEqual(m[name], m[name].mask)
            self.assertEqual(m.bitname(name), m[name].name)
            self.assertEqual(m.bitnum(name), m[name].bitnum)
            c = m.comment(name)

        names = m.names(m.COSMIC | m.BAD | 2**13)
        self.assertTrue('COSMIC' in names)
        self.assertTrue('BAD' in names)
        self.assertTrue('UNKNOWN13' in names)

    def test_mask(self):
        """Test options for blat.mask().
        """
        for i in range(4):
            self.assertEqual(self.ccdmask.mask(i), 2**i)

        m = self.ccdmask
        self.assertEqual(m.mask('BAD|COSMIC'), m.BAD | m.COSMIC)

    def test_access(self):
        """Miscellaneous stuff that should work.
        """
        self.assertEqual(self.ccdmask._name, 'ccdmask')
        self.assertEqual(self.ccdmask['HOT'].blat, 'foo')
        self.assertEqual(self.ccdmask.HOT.blat, 'foo')
        self.assertEqual(self.ccdmask.HOT.name, 'HOT')
        self.assertEqual(self.ccdmask.HOT.bitnum, 1)
        self.assertEqual(self.ccdmask.HOT.mask, 2)
        self.assertEqual(self.ccdmask.HOT, 2)
        self.assertEqual(self.ccdmask.HOT.comment, "Hot pixel")
        self.assertListEqual(self.ccdmask.names(), ['BAD', 'HOT', 'DEAD', 'SATURATED', 'COSMIC'])

    def test_badname(self):
        """Test raising AttributeError for bad names.
        """
        with self.assertRaises(AttributeError):
            x = self.ccdmask.BLATFOO

        # Attribute already in use
        with self.assertRaises(AttributeError):
            bit = _MaskBit('BAD', 0, "comment", extra={'real': 'foo'})

        # has extra that isn't a dict
        with self.assertRaises(ValueError):
            blat = BitMask('ccdmask', _baddef1)

    def test_str(self):
        """Verify yaml-ness of string representation"""
        bitmask = BitMask('ccdmask', yaml.safe_load(str(self.ccdmask)))
        self.assertListEqual(bitmask.names(), self.ccdmask.names())
        for name in bitmask.names():
            self.assertEqual(bitmask[name].mask, self.ccdmask[name].mask)
            self.assertEqual(bitmask[name].comment, self.ccdmask[name].comment)
            self.assertEqual(bitmask[name].bitnum, self.ccdmask[name].bitnum)
            self.assertEqual(bitmask[name]._extra, self.ccdmask[name]._extra)

    def test_highbit(self):
        _bitdefs = dict(ccdmask=list())
        _bitdefs['ccdmask'].append(['LOWEST',   0, "bit 0"])
        _bitdefs['ccdmask'].append(['HIGHEST', 63, "bit 63"])
        mask = BitMask('ccdmask', _bitdefs)
        self.assertEqual(mask.names(1), ['LOWEST'])
        self.assertEqual(mask.names(2**63), ['HIGHEST'])

    def test_uint64(self):
        _bitdefs = dict(ccdmask=list())
        _bitdefs['ccdmask'].append(['BAD',   0, "badness"])
        _bitdefs['ccdmask'].append(['HOT',   1, "hothot"])
        _bitdefs['ccdmask'].append(['TEST', 16, "testing"])
        _bitdefs['ccdmask'].append(['BIG31', 31, "blat31..."])
        _bitdefs['ccdmask'].append(['BIGGER32', 32, "blat32..."])
        _bitdefs['ccdmask'].append(['WOW62', 62, "blat62..."])
        _bitdefs['ccdmask'].append(['BIGGEST63', 63, "blat63..."])

        num2name = dict([(m[1], m[0]) for m in _bitdefs['ccdmask']])
        mask = BitMask('ccdmask', _bitdefs)

        allmasks = 2**63 | 2**62 | 2**32 | 2**31 | 2**16 | 2**1 | 2**0

        self.assertListEqual(mask.names(allmasks),
                             ['BAD', 'HOT', 'TEST', 'BIG31', 'BIGGER32', 'WOW62', 'BIGGEST63'])
        self.assertListEqual(mask.names(np.uint64(allmasks)),
                             ['BAD', 'HOT', 'TEST', 'BIG31', 'BIGGER32', 'WOW62', 'BIGGEST63'])
        self.assertListEqual(mask.names(np.uint64(allmasks).astype(np.int64)),
                             ['BAD', 'HOT', 'TEST', 'BIG31', 'BIGGER32', 'WOW62', 'BIGGEST63'])

        for i in range(64):
            if i in num2name:
                n = [num2name[i]]
            else:
                n = ['UNKNOWN' + str(i)]
            names = mask.names(2**i)
            self.assertListEqual(names, n)
            names = mask.names(np.uint64(2**i))
            self.assertListEqual(names, n)
            # Allow testing of negative numbers while avoiding overflow errors.
            names = mask.names(np.uint64(2**i).astype(np.int64))
            self.assertListEqual(names, n)
            # Test with length 1 arrays.
            names = mask.names(np.array([2**i], dtype=np.uint64))
            self.assertListEqual(names, n)
            names = mask.names(np.array([2**i], dtype=np.uint64).astype(np.int64))
            self.assertListEqual(names, n)

        # Arrays of more than one element should throw ValueError.
        with self.assertRaises(ValueError):
            names = mask.names(np.array([2**10, 2**20], dtype=np.uint64))
        # Try with an unexpected type
        with self.assertRaises(ValueError):
            names = mask.names(float(2**32))

    def test_print(self):
        """Test string representations.
        """
        ccdmask_repr = """ccdmask:
    - [BAD             ,  0, "Pre-determined bad pixel (any reason)"]
    - [HOT             ,  1, "Hot pixel"]
    - [DEAD            ,  2, "Dead pixel"]
    - [SATURATED       ,  3, "Saturated pixel from object"]
    - [COSMIC          ,  4, "Cosmic ray"]"""
        bit_str = (
            ("BAD              bit 0 mask 0x1 - Pre-determined bad pixel " +
             "(any reason)"),
            "HOT              bit 1 mask 0x2 - Hot pixel",
            "DEAD             bit 2 mask 0x4 - Dead pixel",
            "SATURATED        bit 3 mask 0x8 - Saturated pixel from object",
            "COSMIC           bit 4 mask 0x10 - Cosmic ray")
        bit_repr = ('1', '2', '4', '8', '16')
        blat = repr(self.ccdmask)
        self.assertEqual(blat, _bitdefyaml)
        for i, name in enumerate(self.ccdmask.names()):
            self.assertEqual(str(self.ccdmask[name]), bit_str[i])
            self.assertEqual(repr(self.ccdmask[name]), bit_repr[i])

    def test_numpy_compat(self):
        """Test compatibility with Numpy 1 and Numpy 2.
        """
        signed_array_16 = np.zeros((10,), dtype=np.int16)
        signed_array_32 = np.zeros((10,), dtype=np.int32)
        signed_array_64 = np.zeros((10,), dtype=np.int64)
        unsigned_array_16 = np.zeros((10,), dtype=np.uint16)
        unsigned_array_32 = np.zeros((10,), dtype=np.uint32)
        unsigned_array_64 = np.zeros((10,), dtype=np.uint64)
        for array in (signed_array_16, signed_array_32, signed_array_64,
                      unsigned_array_16, unsigned_array_32, unsigned_array_64):
            new_array = array.copy()
            new_array |= self.ccdmask.COSMIC
            new_array |= self.ccdmask.HOT
            self.assertTrue((new_array == (array + 18)).all())
            self.assertTrue((np.bitwise_and(new_array, self.ccdmask.HOT) != 0).all())
            self.assertTrue((np.bitwise_and(self.ccdmask.HOT, new_array) != 0).all())
            out_array = array.copy()
            np.bitwise_xor(new_array, self.ccdmask.BAD, out=out_array)
            self.assertTrue((out_array == (array + 19)).all())
            with self.assertRaises(TypeError):
                result = np.bitwise_or(0, self.ccdmask.COSMIC)
            with self.assertRaises(TypeError):
                result = np.bitwise_or(self.ccdmask.COSMIC, 0)
