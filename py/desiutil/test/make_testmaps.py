# ADM For the record (and future updates):
# ADM This code was used to generate small dust maps for testing.
# ADM The hardcoded paths are for NERSC, but you can swap out any
# ADM path as needed (08/28/18).

from os.path import basename
import numpy as np
from astropy.io import fits
from time import time

dustdir = "/project/projectdirs/desi/software/edison/dust/v0_1/maps"
start = time()

for pole in ["ngp", "sgp"]:
    filepath = '{}/SFD_dust_4096_{}.fits'.format(dustdir, pole)
    data, hdr = fits.getdata(filepath, header=True)
    # ADM only test the first 10 pixel columns
    data = data[:, 0:10]
    fits.writeto('t/'+basename(filepath), data, header=hdr, overwrite=True)

print('Done...t={:.2f}s'.format(time()-start))
