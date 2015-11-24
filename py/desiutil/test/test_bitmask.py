# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.bitmask.
"""

import unittest
from desiutil.bitmask import BitMask, _MaskBit

import yaml
_bitdefs = yaml.load("""
#- CCD pixel mask
ccdmask:
    - [BAD,       0, "Pre-determined bad pixel (any reason)"]
    - [HOT,       1, "Hot pixel", {blat: 'foo'}]
    - [DEAD,      2, "Dead pixel"]
    - [SATURATED, 3, "Saturated pixel from object"]
    - [COSMIC,    4, "Cosmic ray"]
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
        self.ccdmask.names()

    def test_badname(self):
        """Test raising AttributeError for bad names.
        """
        with self.assertRaises(AttributeError):
            x = self.ccdmask.BLATFOO
        with self.assertRaises(AttributeError):
            bit = _MaskBit('BAD', 0, "comment", extra={'real': 'foo'})

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
        bit_repr = (
            "_MaskBit('BAD', 0, 'Pre-determined bad pixel (any reason)')",
            "_MaskBit('HOT', 1, 'Hot pixel')",
            "_MaskBit('DEAD', 2, 'Dead pixel')",
            "_MaskBit('SATURATED', 3, 'Saturated pixel from object')",
            "_MaskBit('COSMIC', 4, 'Cosmic ray')",)
        blat = repr(self.ccdmask)
        self.assertEqual(blat, ccdmask_repr)
        for i, name in enumerate(self.ccdmask.names()):
            self.assertEqual(str(self.ccdmask[name]), bit_str[i])
            self.assertEqual(repr(self.ccdmask[name]), bit_repr[i])

if __name__ == '__main__':
    unittest.main()
