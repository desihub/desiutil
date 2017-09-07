# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
desiutil.test.test_brick
========================

Test desiutil.brick.
"""
from __future__ import absolute_import, division, unicode_literals
# The line above will help with 2to3 support.
import unittest
import os
import numpy as np
from .. import brick as B


class TestBrick(unittest.TestCase):
    """Test desiutil.brick.
    """

    def setUp(self):
        n = 10
        self.ra = np.linspace(0, 3, n) - 1.5
        self.dec = np.linspace(0, 3, n) - 1.5
        #ADM note that these are the correct brickIDs for bricksize=0.25
        self.brickids = np.array(
            [323162, 324603, 327484, 328926, 330367, 331808, 333250, 334691,
             337572, 339014])
        self.brickqs = np.array([0, 3, 2, 0, 3, 2, 0, 3, 2, 0])
        #ADM note that these are the correct brick names for bricksize=0.5
        self.names = np.array(
            ['3587m015', '3587m010', '3592m010', '3597m005', '3597p000',
            '0002p000', '0007p005', '0007p010', '0012p010', '0017p015'])
        #ADM some brick areas
        self.areas = np.array(
            [0.062478535,  0.062485076,  0.062494595,  0.062497571,  0.062499356,
             0.062499356,  0.062497571,  0.062494595,  0.062485076,  0.062478535], dtype='<f4')

    def test_repr(self):
        """Test string representation.
        """
        b = B.Bricks()
        self.assertEqual(repr(b), "Bricks(bricksize=0.25)")

    def test_brickvertices_scalar(self):
        """Test scalar to brick vertex conversion.
        """
        b = B.Bricks()
        ra, dec = 0, 0
        bverts = b.brickvertices(ra,dec)
        self.assertTrue( (np.min(bverts[:,0]) <= ra) & (np.max(bverts[:,0]) >= ra) )
        self.assertTrue( (np.min(bverts[:,1]) <= dec) & (np.max(bverts[:,1]) >= dec) )

    def test_brickvertices_array(self):
        """Test array to brick vertex conversion.
        """
        b = B.Bricks()
        bverts = b.brickvertices(self.ra, self.dec)
        #ADM have to wraparound the negative RAs for "between" tests in RA
        rawrap = self.ra % 360
        self.assertTrue( np.all( (np.min(bverts[:,:,0],axis=1) <= rawrap) & (np.max(bverts[:,:,0],axis=1) >= rawrap) ) )
        self.assertTrue( np.all( (np.min(bverts[:,:,1],axis=1) <= self.dec) & (np.max(bverts[:,:,1],axis=1) >= self.dec) ) )

    def test_brickvertices_wrap(self):
        """Test RA wrap and poles for brick vertices.
        """
        b = B.Bricks()
        b1 = b.brickvertices(1, 0)
        b2 = b.brickvertices(361, 0)
        self.assertTrue(np.all(b1 == b2))

        b1 = b.brickvertices(-0.5, 0)
        b2 = b.brickvertices(359.5, 0)
        self.assertTrue(np.all(b1 == b2))

        b1 = b.brickvertices(0, 90)
        b2 = b.brickvertices(90, 90)
        self.assertTrue(np.all(b1 == b2))
        self.assertEqual(np.max(b1[:,0])-np.min(b1[:,0]), 360.)
        self.assertTrue(np.all(b1[:,1] <= 90.))

        b1 = b.brickvertices(0, -90)
        b2 = b.brickvertices(90, -90)
        self.assertTrue(np.all(b1 == b2))
        self.assertEqual(np.max(b1[:,0])-np.min(b1[:,0]), 360.)
        self.assertTrue(np.all(b1[:,1] >= -90.))

    def test_uneven_bricksize(self):
        # Brick sizes that evenly divide 180 degrees work fine
        b = B.Bricks(bricksize=0.25)
        r,d = b.brick_radec(0., 90.)
        self.assertTrue(d <= 90.)

        # Strange brick size
        b = B.Bricks(bricksize=0.23)
        r,d = b.brick_radec(0., 90.)
        self.assertTrue(d <= 90.)

        # If one row spans Dec=0, the number of bricks in that row may
        # be set incorrectly.
        # This happens for lots of different values, as low as 0.1 deg
        bricksize = 9.97
        b = B.Bricks(bricksize=bricksize)
        a = b.brickarea(0., 0.)
        self.assertTrue(np.sqrt(a) <= bricksize)
        v = b.brickvertices(0., 0.)
        # First two vertices are the bottom edge
        d0,d1 = v[0,1],v[1,1]
        self.assertTrue(d0 == d1)
        d2 = v[2,1]
        # Third vertex is positive Dec.
        self.assertTrue((d0 < 0) and (d2 > 0))
        # Thus the vertex spans Dec=0
        # Measure the brick width at Dec=0 (the widest point)
        r0,r1 = v[0,0],v[1,0]
        self.assertTrue(np.abs(r1 - r0) <= bricksize)

    def test_brickarea_scalar(self):
        """Test scalar to brick area conversion.
        """
        b = B.Bricks()
        barea = b.brickarea(0, 0)
        self.assertEqual(barea, np.array([0.0624999515],dtype='<f4')[0])

    def test_brickarea_array(self):
        """Test array to brick area conversion.
        """
        b = B.Bricks()
        bareas = b.brickarea(self.ra, self.dec)
        self.assertEqual(len(bareas), len(self.ra))
        self.assertTrue((bareas == self.areas).all())

    def test_brickarea_wrap(self):
        """Test RA wrap and poles for brick areas.
        """
        b = B.Bricks()
        b1 = b.brickarea(1, 0)
        b2 = b.brickarea(361, 0)
        self.assertEqual(b1, b2)

        b1 = b.brickarea(-0.5, 0)
        b2 = b.brickarea(359.5, 0)
        self.assertEqual(b1, b2)

        b1 = b.brickarea(0, 90)
        b2 = b.brickarea(90, 90)
        self.assertEqual(b1, b2)
        self.assertEqual(b1, np.array([0.049087364],dtype='<f4')[0])

        b1 = b.brickarea(0, -90)
        b2 = b.brickarea(90, -90)
        self.assertEqual(b1, b2)
        self.assertEqual(b1, np.array([0.049087364],dtype='<f4')[0])

    def test_brickq_scalar(self):
        """Test scalar to BRICKQ conversion.
        """
        b = B.Bricks()
        bq = b.brickq(0, -90)
        self.assertEqual(bq, 1)
        bq = b.brickq(0, 90)
        self.assertEqual(bq, 0)
        bq = b.brickq(0, 0)
        self.assertEqual(bq, 0)

    def test_brickq_array(self):
        """Test array to BRICKQ conversion.
        """
        b = B.Bricks()
        bqs = b.brickq(self.ra, self.dec)
        self.assertEqual(len(bqs), len(self.ra))
        self.assertTrue((bqs == self.brickqs).all())

    def test_brickq_wrap(self):
        """Test RA wrap and poles for BRICKQs.
        """
        b = B.Bricks()
        b1 = b.brickq(1, 0)
        b2 = b.brickq(361, 0)
        self.assertEqual(b1, b2)

        b1 = b.brickq(-0.5, 0)
        b2 = b.brickq(359.5, 0)
        self.assertEqual(b1, b2)

        b1 = b.brickq(0, 90)
        b2 = b.brickq(90, 90)
        self.assertEqual(b1, b2)
        self.assertEqual(b1, 0)

        b1 = b.brickq(0, -90)
        b2 = b.brickq(90, -90)
        self.assertEqual(b1, b2)
        self.assertEqual(b1, 1)

    def test_brickid_scalar(self):
        """Test scalar to BRICKID conversion.
        """
        b = B.Bricks()
        bid = b.brickid(0, 0)
        self.assertEqual(bid, 330368)

    def test_brickid_array(self):
        """Test array to BRICKID conversion.
        """
        b = B.Bricks()
        bids = b.brickid(self.ra, self.dec)
        self.assertEqual(len(bids), len(self.ra))
        self.assertTrue((bids == self.brickids).all())

    def test_brickid_wrap(self):
        """Test RA wrap and poles for BRICKIDs.
        """
        b = B.Bricks()
        b1 = b.brickid(1, 0)
        b2 = b.brickid(361, 0)
        self.assertEqual(b1, b2)

        b1 = b.brickid(-0.5, 0)
        b2 = b.brickid(359.5, 0)
        self.assertEqual(b1, b2)

        b1 = b.brickid(0, 90)
        b2 = b.brickid(90, 90)
        self.assertEqual(b1, b2)
        self.assertEqual(b1, 662174)

        b1 = b.brickid(0, -90)
        b2 = b.brickid(90, -90)
        self.assertEqual(b1, b2)
        self.assertEqual(b1, 1)

    def test_brickname_scalar(self):
        """Test scalar to brick name conversion.
        """
        b = B.brickname(0, 0, bricksize=0.5)
        self.assertEqual(b, '0002p000')

    def test_brickname_array(self):
        """Test array to brick name conversion.
        """
        bricknames = B.brickname(self.ra, self.dec, bricksize=0.5)
        self.assertEqual(len(bricknames), len(self.ra))
        self.assertTrue((bricknames == self.names).all())

    def test_brickname_wrap(self):
        """Test RA wrap and poles for bricknames.
        """
        b1 = B.brickname(1, 0)
        b2 = B.brickname(361, 0)
        self.assertEqual(b1, b2)

        b1 = B.brickname(-0.5, 0)
        b2 = B.brickname(359.5, 0)
        self.assertEqual(b1, b2)

        b1 = B.brickname(0, 90)
        b2 = B.brickname(90, 90)
        self.assertEqual(b1, b2)
        self.assertEqual(b1, '1800p900')

        b1 = B.brickname(0, -90)
        b2 = B.brickname(90, -90)
        self.assertEqual(b1, b2)
        self.assertEqual(b1, '1800m900')

    def test_brickname_list(self):
        """Test list to brick name conversion.
        """
        bricknames = B.brickname(self.ra.tolist(), self.dec.tolist(), bricksize=0.5)
        self.assertEqual(len(bricknames), len(self.ra))
        self.assertTrue((bricknames == self.names).all())

    def test_bricksize(self):
        """Test the bricksize attribute.
        """
        B._bricks = None
        blat = B.brickname(0, 0, bricksize=0.5)
        self.assertEqual(B._bricks.bricksize, 0.5)
        blat = B.brickname(0, 0, bricksize=0.25)
        self.assertEqual(B._bricks.bricksize, 0.25)
        B._bricks = None

    def test_brick_radec_scalar(self):
        """Test scalar to brick RA,Dec conversion.
        """
        b = B.Bricks(bricksize=1.)
        ra,dec = b.brick_radec(0., 0.)
        self.assertEqual(ra, 0.5)
        self.assertEqual(dec, 0.)

    def test_brick_radec_array(self):
        """Test array to brick RA,Dec conversion.
        """
        b = B.Bricks(bricksize=1.)
        ra,dec = b.brick_radec(np.array([0., 1.]), np.array([0.,0.]))
        self.assertEqual(len(ra), 2)
        self.assertEqual(len(dec), 2)
        self.assertEqual(ra[0], 0.5)
        self.assertEqual(dec[0], 0.)
        self.assertEqual(ra[1], 1.5)
        self.assertEqual(dec[1], 0.)

    def test_to_table(self):
        """Test conversion to table.
        """
        t = B.Bricks().to_table()
        self.assertEqual(t.meta['bricksize'], 0.25)
        self.assertEqual(len(t), 662174)

    @unittest.skipIf('DTILING_DIR' not in os.environ,
                     "Skipping test that requires dtiling code.")
    def test_IDL_bricks(self):
        """Compare Python bricks to IDL bricks.
        """
        from glob import glob
        from astropy.io import fits
        brickfiles = glob(os.path.join(os.environ['DTILING_DIR'],
                                       'bricks-*.fits'))
        bricksizes = [os.path.basename(b).split('-')[1].replace('.fits', '') for b in brickfiles]
        for i, f in enumerate(brickfiles):
            with fits.open(f) as hdulist:
                dtiling_data = hdulist[1].data
            b = B.Bricks(bricksize=float(bricksizes[i]))
            bricknames = b.brickname(dtiling_data['RA'], dtiling_data['DEC'])
            brickids = b.brickid(dtiling_data['RA'], dtiling_data['DEC'])
            brickqs = b.brickq(dtiling_data['RA'], dtiling_data['DEC'])
            brickareas = b.brickarea(dtiling_data['RA'], dtiling_data['DEC'])
            brick_ra, brick_dec = b.brick_radec(dtiling_data['RA'], dtiling_data['DEC'])
            brickvertices = b.brickvertices(dtiling_data['RA'], dtiling_data['DEC'])
            self.assertTrue((bricknames == dtiling_data['BRICKNAME']).all())
            self.assertTrue((brickids == dtiling_data['BRICKID']).all())
            self.assertTrue((brickqs == dtiling_data['BRICKQ']).all())
            self.assertTrue(np.allclose(brickareas, dtiling_data['AREA'], rtol=1e-7, atol=1e-9))
            self.assertTrue(np.allclose(brick_ra, dtiling_data['RA'], rtol=1e-7, atol=1e-9))
            self.assertTrue(np.allclose(brick_dec, dtiling_data['DEC'], rtol=1e-7, atol=1e-9))
            dtiling_vertices = np.reshape(np.vstack([dtiling_data['RA1'],
                                                     dtiling_data['DEC1'],
                                                     dtiling_data['RA2'],
                                                     dtiling_data['DEC1'],
                                                     dtiling_data['RA2'],
                                                     dtiling_data['DEC2'],
                                                     dtiling_data['RA1'],
                                                     dtiling_data['DEC2']]).T,
                                          (len(dtiling_data['RA1']), 4, 2))
            self.assertTrue(np.allclose(brickvertices, dtiling_vertices, rtol=1e-7, atol=1e-9))

    @unittest.skipIf('DTILING_DIR' not in os.environ,
                     "Skipping test that requires dtiling code.")
    def test_IDL_tables(self):
        """Test equality of Tables generated by IDL and Python.
        """
        from glob import glob
        from astropy.table import Table
        brickfiles = glob(os.path.join(os.environ['DTILING_DIR'],
                                       'bricks-*.fits'))
        bricksizes = [os.path.basename(b).split('-')[1].replace('.fits', '') for b in brickfiles]
        for i, f in enumerate(brickfiles):
            dtiling_table = Table.read(f)
            brick_table = B.Bricks(bricksize=float(bricksizes[i])).to_table()
            self.assertEqual(len(brick_table), len(dtiling_table))
            for n in dtiling_table.colnames:
                if dtiling_table[n].dtype.kind == 'f':
                    self.assertTrue(np.allclose(brick_table[n],
                                                dtiling_table[n],
                                                rtol=1e-7, atol=1e-9))
                else:
                    self.assertTrue((brick_table[n] == dtiling_table[n]).all())


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
