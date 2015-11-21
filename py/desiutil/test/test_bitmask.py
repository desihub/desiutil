"""
test desiutil.maskbits
"""

import unittest
from desiutil.bitmask import BitMask

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


class TestBitMasks(unittest.TestCase):

    def setUp(self):
        self.ccdmask = BitMask('ccdmask', _bitdefs)

    def test_names(self):
        """
        Test consistency for names to bits to masks
        """
        m = self.ccdmask
        for name in m.names():
            self.assertEqual(m.mask(name), 2**m.bitnum(name),
                             'Failed matching mask to bitnum for '+name)
            self.assertEqual(m.mask(name), m.mask(m.bitnum(name)),
                             'Failed matching mask to name for '+name)
            self.assertEqual(m.bitname(m.bitnum(name)), name,
                             'Failed bit name->num->name roundtrip for '+name)
            self.assertEqual(m[name], m[name].mask)
            self.assertEqual(m.bitname(name), m[name].name)
            self.assertEqual(m.bitnum(name), m[name].bitnum)
            c = m.comment(name)

        names = m.names(m.COSMIC | m.BAD | 2**13)
        self.assertTrue('COSMIC' in names)
        self.assertTrue('BAD' in names)
        self.assertTrue('UNKNOWN13' in names)

    def test_mask(self):
        '''test options for blat.mask()'''
        for i in range(4):
            self.assertEqual(self.ccdmask.mask(i), 2**i)

        m = self.ccdmask
        self.assertEqual(m.mask('BAD|COSMIC'), m.BAD | m.COSMIC)

    def test_access(self):
        '''Misc stuff that should work'''
        self.assertEqual(self.ccdmask['HOT'].blat, 'foo')
        self.assertEqual(self.ccdmask.HOT.blat, 'foo')
        self.assertEqual(self.ccdmask.HOT.name, 'HOT')
        self.assertEqual(self.ccdmask.HOT.bitnum, 1)
        self.assertEqual(self.ccdmask.HOT.mask, 2)
        self.assertEqual(self.ccdmask.HOT, 2)
        self.assertEqual(self.ccdmask.HOT.comment, "Hot pixel")
        self.ccdmask.names()

    def test_badname(self):
        with self.assertRaises(AttributeError):
            x = self.ccdmask.BLATFOO

    def test_print(self):
        blat = self.ccdmask.__repr__()
        for name in self.ccdmask.names():
            foo = self.ccdmask[name].__str__()

if __name__ == '__main__':
    unittest.main()
