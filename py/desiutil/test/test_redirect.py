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
from unittest.mock import call, patch, MagicMock
import tempfile
import shutil
import subprocess as sp
import desiutil.redirect as r


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
    """Test desiutil.redirect
    """

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.python_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        r._libc = None
        r._c_stdout = None
        r._c_stderr = None
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
            except ImportError:
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

    def test_serial(self):
        with patch.dict(os.environ, {'PYTHONPATH': self.python_path}):
            outfile = os.path.join(self.test_dir, "redirect_serial.log")
            com = ["python", self.test_serial_script, outfile, "0"]
            out = sp.run(
                com, check=True, universal_newlines=True, stdout=sp.PIPE, stderr=sp.STDOUT
            ).stdout
        self.check_serial(outfile)

    def test_serial_error(self):
        with patch.dict(os.environ, {'PYTHONPATH': self.python_path}):
            outfile = os.path.join(self.test_dir, "redirect_serial_error.log")
            com = ["python", self.test_serial_script, outfile, "1"]
            with self.assertRaises(sp.CalledProcessError) as cm:
                out = sp.run(com, check=True, universal_newlines=True, stdout=sp.PIPE, stderr=sp.STDOUT).stdout

    def test_mpi(self):
        if not self.have_mpi:
            return
        outfile = os.path.join(self.test_dir, "redirect_mpi.log")
        print("\nTo manually test MPI redirection, run:")
        print("  mpirun -np 2 python {} {} 0".format(self.test_mpi_script, outfile))
        print("And then inspect the {} output file\n".format(outfile))

    @patch('desiutil.redirect.ctypes')
    def test__get_libc_linux(self, mock_ctypes):
        """Test standard library information in a simulated Linux environment.
        """
        mock_ctypes.CDLL.return_value = 'Linux'

        def side_effect(*args):
            return args[1]

        mock_ctypes.c_void_p.in_dll.side_effect = side_effect
        lib, out, err = r._get_libc()
        self.assertEqual(lib, 'Linux')
        self.assertEqual(out, 'stdout')
        self.assertEqual(err, 'stderr')
        mock_ctypes.CDLL.assert_called_once_with(None)
        mock_ctypes.c_void_p.in_dll.assert_has_calls([call(lib, "stdout"), call(lib, "stderr")])

    @patch('desiutil.redirect.ctypes')
    def test__get_libc_darwin(self, mock_ctypes):
        """Test standard library information in a simulated Darwin environment.
        """
        mock_ctypes.CDLL.return_value = 'Darwin'

        def side_effect(*args):
            if args[1] == 'stdout':
                raise ValueError("Darwin!")
            else:
                return args[1]

        mock_ctypes.c_void_p.in_dll.side_effect = side_effect
        lib, out, err = r._get_libc()
        self.assertEqual(lib, 'Darwin')
        self.assertEqual(out, '__stdoutp')
        self.assertEqual(err, '__stderrp')
        mock_ctypes.CDLL.assert_called_once_with(None)
        mock_ctypes.c_void_p.in_dll.assert_has_calls([call(lib, "__stdoutp"), call(lib, "__stderrp")])

    @patch('desiutil.redirect.ctypes')
    def test__get_libc_unknown(self, mock_ctypes):
        """Test standard library information in a simulated Unknown environment.
        """
        mock_ctypes.CDLL.return_value = 'Unknown'
        mock_ctypes.c_void_p.in_dll.side_effect = ValueError('Unknown!')
        lib, out, err = r._get_libc()
        self.assertEqual(lib, 'Unknown')
        self.assertIsNone(out)
        self.assertIsNone(err)
        mock_ctypes.CDLL.assert_called_once_with(None)
