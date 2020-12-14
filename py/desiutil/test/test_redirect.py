# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.redirect.

Note that desiutil is not MPI-aware, so we only run MPI unit tests if the
'RUN_MPI_TESTS' environment variable is set.  This way we can run those
tests on machines where MPI is available, but skip them when running on
CI environments, etc.

"""
import sys
import os
import re
import unittest
import tempfile
import shutil

import subprocess as sp

# This test requires desiutil to be installed for spawned scripts;
# skip if we are doing a test prior to a full installation.
not_installed = bool(sp.call(['python', '-c', 'import desiutil.redirect']))

test_serial_source = """
import sys
import os

from desiutil.redirect import stdouterr_redirected

def generate_output(error=False):
    if error:
        raise RuntimeError("Error!")
    else:
        for i in range(5):
            print("{}".format(i))

filename = sys.argv[1]
with_error = (sys.argv[2] == "1")

with stdouterr_redirected(to=filename):
    if with_error:
        generate_output(error=True)
    else:
        generate_output()

"""

test_mpi_source = """
from mpi4py import MPI
import sys
import os

from desiutil.redirect import stdouterr_redirected

def generate_output(error=False):
    if error:
        raise RuntimeError("Error!")
    else:
        for i in range(5):
            print("{}".format(i))

filename = sys.argv[1]
with_error = (sys.argv[2] == "1")

with stdouterr_redirected(to=filename, comm=MPI.COMM_WORLD):
    if with_error and MPI.COMM_WORLD.rank == MPI.COMM_WORLD.size - 1:
        generate_output(error=True)
    else:
        generate_output()

"""


class TestRedirect(unittest.TestCase):
    """Test desiutil.redirect"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        self.test_serial_script = os.path.join(self.test_dir, "run_serial.py")
        self.test_mpi_script = os.path.join(self.test_dir, "run_mpi.py")
        self.n_lines = 5
        self.have_mpi = False
        self.comm = None
        self.rank = 0
        self.nproc = 1
        if "RUN_MPI_TESTS" in os.environ:
            try:
                from mpi4py import MPI

                self.have_mpi = True
                self.comm = MPI.COMM_WORLD
                self.rank = self.comm.rank
                self.nproc = self.comm.size
            except:
                pass
        if self.rank == 0:
            with open(self.test_serial_script, "w") as f:
                f.write(test_serial_source)
            with open(self.test_mpi_script, "w") as f:
                f.write(test_mpi_source)

    def tearDown(self):
        pass

    def check_serial(self, file):
        with open(file, "r") as f:
            for line_num, line_str in enumerate(f):
                check_num = int(line_str.split()[0])
                self.assertTrue(line_num == check_num)

    @unittest.skipIf(not_installed, "stdout redirection tests require desiutil to be installed first")
    def test_serial(self):
        outfile = os.path.join(self.test_dir, "redirect_serial.log")
        com = ["python", self.test_serial_script, outfile, "0"]
        out = sp.run(
            com, check=True, universal_newlines=True, stdout=sp.PIPE, stderr=sp.STDOUT
        ).stdout
        self.check_serial(outfile)

    @unittest.skipIf(not_installed, "stdout redirection tests require desiutil to be installed first")
    def test_serial_error(self):
        outfile = os.path.join(self.test_dir, "redirect_serial_error.log")
        com = ["python", self.test_serial_script, outfile, "1"]
        try:
            out = sp.run(
                com,
                check=True,
                universal_newlines=True,
                stdout=sp.PIPE,
                stderr=sp.STDOUT,
            ).stdout
        except:
            print("Successfully handled exception")
        else:
            raise RuntimeError("Did not successfully handle exception")

    def test_mpi(self):
        if not self.have_mpi:
            return
        outfile = os.path.join(self.test_dir, "redirect_mpi.log")
        print("\nTo manually test MPI redirection, run:")
        print("  mpirun -np 2 python {} {} 0".format(self.test_mpi_script, outfile))
        print("And then inspect the {} output file\n".format(outfile))


def test_suite():
    """Allows testing of only this module with the command::

    python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
