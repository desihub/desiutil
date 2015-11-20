"""
test desiutil.maskbits
"""

import unittest
from desiutil.maskbits import BitMask

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
    
    #- Which bitmasks to test
    def setUp(self):
        self.ccdmask = BitMask('ccdmask', _bitdefs)
            
    def test_names(self):
        """
        Test consistency for names to bits to masks
        """
        m = self.ccdmask
        for name in m.names():
            self.assertEqual(m.mask(name), 2**m.bitnum(name), 'Failed matching mask to bitnum for '+name)
            self.assertEqual(m.mask(name), m.mask(m.bitnum(name)), 'Failed matching mask to name for '+name)
            self.assertEqual(m.bitname(m.bitnum(name)), name, 'Failed bit name->num->name roundtrip for '+name)
            c = m.comment(name)
        
        names = m.names(m.COSMIC|m.BAD | 2**13)
        self.assertTrue('COSMIC' in names)
        self.assertTrue('BAD' in names)
        self.assertTrue('UNKNOWN13' in names)
        
        foo = m.extra('HOT')
        
    def test_badname(self):
        with self.assertRaises(AttributeError):
            x = self.ccdmask.BLATFOO
            
    def test_print(self):
        print self.ccdmask
        
if __name__ == '__main__':
    unittest.main()