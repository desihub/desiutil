# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.redirect.

Note that desiutil is not MPI-aware, so we only run MPI unit tests if the
'RUN_MPI_TESTS' environment variable is set.  This way we can run those
tests on machines where MPI is available, but skip them when running on
CI environments, etc.

"""
import os
import re
import unittest
import tempfile

from ..redirect import stdouterr_redirected


class TestRedirect(unittest.TestCase):
    """Test desiutil.redirect
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
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

    def tearDown(self):
        pass

    def generate_output(self, error=False):
        if error:
            raise RuntimeError("Error!")
        else:
            for i in range(self.n_lines):
                print("{}".format(i))

    def check_serial(self, file):
        with open(file, "r") as f:
            for line_num, line_str in enumerate(f):
                check_num = int(line_str.split()[0])
                self.assertTrue(line_num == check_num)

    def check_mpi(self, file):
        pstr_pat = re.compile("=+ Process (\d+) =+.*")
        fail = False
        if self.rank == 0:
            try:
                with open(file, "r") as f:
                    cur_p = -1
                    p_off = 0
                    for line in f:
                        mat = pstr_pat.match(line)
                        if mat is not None:
                            # Starting a new process section, verify they are in
                            # rank order.
                            new_p = int(mat.group(1))
                            self.assertTrue(new_p == cur_p + 1)
                            p_off = 0
                            cur_p = new_p
                        else:
                            check_num = int(line.split()[0])
                            self.assertTrue(p_off == check_num)
                            p_off += 1
            except:
                fail = True
        fail = self.comm.bcast(fail, root=0)
        if fail:
            raise RuntimeError("MPI redirect output not correct")
        self.comm.barrier()

    def test_serial(self):
        outfile = os.path.join(self.test_dir, "redirect_serial.log")
        with stdouterr_redirected(to=outfile):
            self.generate_output()
        self.check_serial(outfile)

    def test_serial_error(self):
        outfile = os.path.join(self.test_dir, "redirect_serial_error.log")
        try:
            with stdouterr_redirected(to=outfile):
                self.generate_output(error=True)
        except:
            print("Successfully handled exception")
        else:
            raise RuntimeError("Did not successfully handle exception")

    def test_mpi(self):
        if not self.have_mpi:
            return
        outfile = os.path.join(self.test_dir, "redirect_mpi.log")
        with stdouterr_redirected(to=outfile, comm=self.comm):
            self.generate_output()
        self.check_mpi(outfile)

    def test_mpi_error(self):
        if not self.have_mpi:
            return
        outfile = os.path.join(self.test_dir, "redirect_mpi_error.log")
        try:
            with stdouterr_redirected(to=outfile, comm=self.comm):
                if self.rank == self.nproc - 1:
                    self.generate_output(error=True)
                else:
                    self.generate_output()
        except:
            print("Successfully handled exception")
            if self.rank == 0:
                with open(outfile, "r") as f:
                    for line in f:
                        print(line, flush=True)
        else:
            raise RuntimeError("Did not successfully handle exception")


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
