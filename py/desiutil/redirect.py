# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
=================
desiutil.redirect
=================

Utilities for redirecting stdout / stderr to files.

"""

import os
import sys
import time
import io
import traceback
import logging
import ctypes

from contextlib import contextmanager

from .log import get_logger, _desiutil_log_root


# C file descriptors for stderr and stdout, used in redirection
# context manager.

libc = ctypes.CDLL(None)
c_stdout = None
c_stderr = None
try:
    # Linux systems
    c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')
    c_stderr = ctypes.c_void_p.in_dll(libc, 'stderr')
except:
    try:
        # Darwin
        c_stdout = ctypes.c_void_p.in_dll(libc, '__stdoutp')
        c_stderr = ctypes.c_void_p.in_dll(libc, '__stdoutp')
    except:
        # Neither!
        pass

@contextmanager
def stdouterr_redirected(to=None, comm=None):
    """Redirect stdout and stderr to a file.

    The general technique is based on:

    http://stackoverflow.com/questions/5081657
    http://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/

    If the optional communicator is specified, then each process redirects to
    a different temporary file.  Upon exit from the context the rank zero
    process concatenates these in order to the final file result.

    If the enclosing code raises an exception, the traceback is printed to the
    log file.

    Args:
        to (str): The output file name.
        comm (mpi4py.MPI.Comm): The optional MPI communicator.

    """
    nproc = 1
    rank = 0
    MPI = None
    if comm is not None:
        # If we are already using MPI (comm is set), then we can safely
        # import mpi4py.
        from mpi4py import MPI
        nproc = comm.size
        rank = comm.rank

    # The currently active POSIX file descriptors
    fd_out = sys.stdout.fileno()
    fd_err = sys.stderr.fileno()

    # Save the original file descriptors so we can restore them later
    saved_fd_out = os.dup(fd_out)
    saved_fd_err = os.dup(fd_err)

    # The DESI loggers.
    desi_loggers = _desiutil_log_root

    def _redirect(out_to, err_to):
        # Flush the C-level buffers
        if c_stdout is not None:
            libc.fflush(c_stdout)
        if c_stderr is not None:
            libc.fflush(c_stderr)

        # This closes the python file handles, and marks the POSIX
        # file descriptors for garbage collection- UNLESS those
        # are the special file descriptors for stderr/stdout.
        sys.stdout.close()
        sys.stderr.close()

        # Close fd_out/fd_err if they are open, and copy the
        # input file descriptors to these.
        os.dup2(out_to, fd_out)
        os.dup2(err_to, fd_err)

        # Create a new sys.stdout / sys.stderr that points to the
        # redirected POSIX file descriptors.  In Python 3, these
        # are actually higher level IO objects.
        if sys.version_info[0] < 3:
            sys.stdout = os.fdopen(fd_out, "wb")
            sys.stderr = os.fdopen(fd_err, "wb")
        else:
            # Python 3 case
            sys.stdout = io.TextIOWrapper(os.fdopen(fd_out, 'wb'))
            sys.stderr = io.TextIOWrapper(os.fdopen(fd_err, 'wb'))

        # update DESI logging to use new stdout
        for name, logger in desi_loggers.items():
            hformat = None
            while len(logger.handlers) > 0:
                h = logger.handlers[0]
                if hformat is None:
                    hformat = h.formatter._fmt
                logger.removeHandler(h)
            # Add the current stdout.
            ch = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(hformat, datefmt='%Y-%m-%dT%H:%M:%S')
            ch.setFormatter(formatter)
            logger.addHandler(ch)

    def _open_redirect(filename):
        # Open python file, which creates low-level POSIX file
        # descriptor.
        file_handle = open(filename, "w")

        # Redirect stdout/stderr to this new file descriptor.
        _redirect(out_to=file_handle.fileno(), err_to=file_handle.fileno())
        return file_handle

    def _close_redirect(handle):
        # Close python file handle, which will mark POSIX file descriptor for
        # garbage collection.  That is fine since we are about to overwrite those.
        if handle is not None:
            handle.close()

        # Flush python handles for good measure
        sys.stdout.flush()
        sys.stderr.flush()

        try:
            # Restore old stdout and stderr
            _redirect(out_to=saved_fd_out, err_to=saved_fd_err)
        except:
            pass

    # Redirect both stdout and stderr to the same file

    if to is None:
        to = "/dev/null"

    if rank == 0:
        log = get_logger()
        log.info("Begin log redirection to {} at {}".format(to, time.asctime()))

    # Try to open the redirected file.

    pto = to
    if to != "/dev/null" and comm is not None:
        pto = "{}_{}".format(to, rank)

    fail_open = 0
    file = None
    try:
        file = _open_redirect(pto)
    except:
        log = get_logger()
        log.error(
            "Failed to open redirection file %s at %s", pto, time.asctime())
        )
        fail_open = 1

    if comm is not None:
        fail_open = comm.allreduce(fail_open, op=MPI.SUM)

    if fail_open > 0:
        # Something went wrong on one or more processes, try to recover and exit
        if rank == 0:
            log = get_logger()
            log.error(
                "Failed to start redirect to %s at %s", to, time.asctime())
            )

        _close_redirect(file)

        # All processes raise an exception for the calling code to handle
        msg = "Failed to start output redirect to {}".format(to)
        raise RuntimeError(msg)

    # Output should now be redirected.  Run the code.

    fail_run = 0
    try:
        yield # Allow code to be run with the redirected output
    except:
        # We have an unhandled exception.  Print a stack trace to the log.
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        print("".join(lines), flush=True)
        fail_run = 1

    # Check if any processes failed to run their code
    if comm is not None:
        fail_run = comm.allreduce(fail_run, op=MPI.SUM)

    _close_redirect(file)

    if comm is not None:
        # Concatenate per-process files if we have multiple processes.
        comm.barrier()
        if rank == 0:
            with open(to, "w") as outfile:
                for p in range(nproc):
                    outfile.write(
                        "================= Process {} =================\n".format(p)
                    )
                    fname = "{}_{}".format(to, p)
                    with open(fname) as infile:
                        outfile.write(infile.read())
                    os.remove(fname)
        comm.barrier()

    if rank == 0:
        log = get_logger()
        log.info("End log redirection to %s at %s", to, time.asctime()))

    # flush python handles for good measure
    sys.stdout.flush()
    sys.stderr.flush()

    if fail_run > 0:
        msg = "{} processes raised an exception while logs were redirected".format(
            fail_run
        )
        if rank == 0:
            log = get_logger()
            log.error(msg)
        raise RuntimeError(msg)

    return
