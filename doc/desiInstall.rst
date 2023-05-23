===========
desiInstall
===========

Introduction
============

This document describes the desiInstall process and the logic behind it.

The primary purpose of :command:`desiInstall` is to install DESI software **at NERSC**.
Using it to install software at locations other than NERSC is theoretically
possible, but not supported.

Basic Invocation of desiInstall
===============================

:command:`desiInstall` is invoked with the product and version to be installed::

    desiInstall desiutil 3.0.3

The version should correspond to a tag in the repository corresponding to
the product.

Branches can also be installed, and the resulting install will be a
checkout of the repository, set to the requested branch.  This is specified
by prepending ``branches/`` to the version name::

    desiInstall desiutil branches/branch-compile

Finally, for Subversion repositories, ``trunk`` is a shorthand for ``branches/trunk``;
for GitHub repositories, ``main`` is a shorthand for ``branches/main``.  All
other branch names *must* be prepended with ``branches/``.

Configuring desiInstall
=======================

:command:`desiInstall` has many options, which are best viewed by typing
``desiInstall --help``.

In addition, :command:`desiInstall` both reads and sets several environment variables.

Environment variables that strongly affect the behavior of :command:`desiInstall`.

:envvar:`DESICONDA`
    This variable contains the path to the `DESI+Anaconda infrastructure`_.
:envvar:`DESICONDA_VERSION`
    This variable should contain the version of the `DESI+Anaconda infrastructure`_.
:envvar:`DESIUTIL`
    This variable contains the path to the installed version of desiutil_.
    It is needed to find the ``etc/desiutil.module`` file.
:envvar:`NERSC_HOST`
    This will automatically be set on NERSC systems.  Although it is fine
    to manipulate this variable during unit tests, for general user and
    production purposes, it should be considered strictly read-only.
:envvar:`USER`
    This variable is read to determine the username to pass to, *e.g.*,
    :command:`svn`.

Environment variables that are *set* by :command:`desiInstall` for use by
:command:`pip install` or :command:`make`.

:envvar:`INSTALL_DIR`
    This variable is *set* by :command:`desiInstall` to the directory that will contain
    the final, installed version of the software package.
:envvar:`PRODUCT_VERSION`
    This variable is *set* by :command:`desiInstall`, with ``PRODUCT`` replaced by the
    actual name of the software being installed, *e.g.*,
    :envvar:`DESISPEC_VERSION`.
:envvar:`WORKING_DIR`
    This variable is *set* by :command:`desiInstall` to the path containing a downloaded,
    expanded software package.

Environment variables related to the Modules infrastructure that may be
manipulated by setting up Modules, or loading Module files.

:envvar:`LOADEDMODULES`
    This variable contains a list of the Module files currently loaded.  It
    may be manipulated by :mod:`desiutil.modules`.
:envvar:`MODULE_VERSION`
    This variable is set on some NERSC systems and is needed to determine the
    full path to :command:`modulecmd`.
:envvar:`MODULE_VERSION_STACK`
    This variable is set on some NERSC systems may be set by
    :mod:`desiutil.modules` for compatibility.
:envvar:`MODULEPATH`
    This variable contains a list of directories containing Module files.
    It may be manipulated by :mod:`desiutil.modules`.
:envvar:`MODULESHOME`
    This variable points to the Modules infrastructure.  If it is not set,
    it typically means that the system has no Modules infrastructure. This
    is needed to find the executable program that reads Module files.
:envvar:`PYTHONPATH`
    Obviously this is important for any Python package!  :envvar:`PYTHONPATH`
    may be manipulated by :mod:`desiutil.modules`.
:envvar:`TCLSH`
    May be used to determine the full path to :command:`modulecmd.tcl` on
    systems with a pure-TCL Modules infrastructure.

.. _desiutil: https://github.com/desihub/desiutil

Directory Structure Assumed by the Install
==========================================

:command:`desiInstall` is primarily intended to run in a production environment that
supports Module files, *i.e.* at NERSC.

:command:`desiInstall` *does not install a Modules infrastructure for you.* You have to
do this yourself, if your system does not already have this.

For the purposes of this section, we define ``$product_root`` as the
directory that :command:`desiInstall` will be writing to.  For standard NERSC installs it
defaults to a pre-defined value. ``$product_root`` may contain the following
directories:

code/
    This contains the installed code, the result of :command:`pip install .`
    or :command:`make install`.  The code is always placed in a ``product/version``
    directory.  So for example, the full path to :command:`desiInstall` might be
    ``$product_root/code/desiutil/1.8.0/bin/desiInstall``.
modulefiles/
    This contains the the Module files installed by :command:`desiInstall`.  A Module
    file is almost always named ``product/version``.  For example, the
    Module file for desiutil might be ``$product_root/modulefiles/desiutil/1.8.0``.

The ``--root`` option can override the built-in default value of ``$product_root``,
which is useful for testing::

    desiInstall --root $SCRATCH/test_install desispec 0.20.0

In the example above, desispec would be installed in
``$SCRATCH/test_install/code/desispec/0.20.0``,
with a corresponding Module file at
``$SCRATCH/test_install/modulefiles/desispec/0.20.0``

Within a ``$product_root/code/product/version`` directory, you might see the
following:

bin/
    Contains command-line executables, including Python or Shell scripts.
data/
    Rarely, packages need data files that cannot be incorporated into the
    package structure itself, so it will be installed here.  desimodel_ is
    an example of this.
etc/
    Miscellaneous metadata and configuration.  In most packages this only
    contains a template Module file.
lib/pythonX.Y/site-packages/
    Contains installed Python code.  ``X.Y`` would be, *e.g.*, ``3.6`` or ``3.8``.
py/
    Sometimes we need to install a git checkout rather than an installed package.
    If so, the Python code will live in *this* directory not the ``lib/``
    directory, and the product's Module file will be adjusted accordingly.

.. _desimodel: https://github.com/desihub/desimodel

Stages of the Install
=====================

Input Validation
----------------

:command:`desiInstall` checks the command-line input, verifying that the user has
specified a product and a version to install.

Product/Version Parsing
-----------------------

Because of the structures of the DESI code repositories, it is sometimes necessary
to specify a directory name along with the product name.  :command:`desiInstall` contains
a list of known products, but it is not necessarily complete. :command:`desiInstall` parses
the input to determine the base name and base version to install.  At this
stage :command:`desiInstall` also determines whether a branch install [#]_ has
been requested.

The internal list of known products can be added to or overridden on the
command line::

    desiInstall -p new_product:https://github.com/me/new_product new_product 1.2.3

    desiInstall -p desiutil:https://github.com/alternate_repository/desiutil desiutil 1.9.9

The ``-p`` option can be specified multiple times, though in practice, it only
matters to the product actually being installed.

.. [#] In this document, "branch" refers to anything that is not a tagged version.
   This could include default branches such as "trunk" in Subversion repositories,
   or any default branch in a git repository.

Product Existence
-----------------

After the product name and version have been determined, :command:`desiInstall`
constructs the full URL pointing to the product/version and runs the code
necessary to verify that the product/version really exists.  Typically, this
will be :command:`svn ls`, unless a GitHub install is detected.

Download Code
-------------

The code is downloaded, using :command:`svn export` for standard (tag) installs, or
:command:`svn checkout` for branch installs.  For GitHub installs, :command:`desiInstall`
will look for a release tarball, or do a :command:`git clone` for tag or branch
installs.  :command:`desiInstall` will set the environment variable :envvar:`WORKING_DIR`
to point to the directory containing this downloaded code.

Determine Build Type
--------------------

The downloaded code is scanned to determine the build type.  There are several
possible build types that are mutually exclusive.  They are derived in this
order and the first matching method is used:

py
    If a setup.py file is detected, :command:`desiInstall` will attempt to execute
    :command:`pip install .`.  This build type can be suppressed with the
    command line option ``--compile-c``.
make
    If a Makefile is detected, :command:`desiInstall` will attempt to execute
    :command:`make install`.
src
    If a Makefile is not present, but a src/ directory is,
    :command:`desiInstall` will attempt to execute :command:`make -C src all`.
plain
    If no other build type is detected, the downloaded code
    is simply copied to the final install directory.

**It is the responsibility of the code developer to understand these build
types and choose the one appropriate for the package being developed.**

Determine Install Directory
---------------------------

The install directory is where the code will live permanently.  If the
install is taking place at NERSC, the top-level install directory is
predetermined based on the value of :envvar:`NERSC_HOST`::

    /global/common/software/desi/${NERSC_HOST}/desiconda/${DESICONDA_VERSION}

The actual install directory is determined by appending ``/code/product/verson``
to the combining the top-level directory listed above.

If the install directory already exists, :command:`desiInstall` will exit, unless the
``--force`` parameter is supplied on the command line.

:command:`desiInstall` will set the environment variable :envvar:`INSTALL_DIR` to point to the
install directory.

.. _`DESI+Anaconda infrastructure`: https://github.com/desihub/desiconda
.. _desiconda: https://github.com/desihub/desiconda

Module Infrastructure
---------------------

:command:`desiInstall` sets up the Modules infrastructure by running code in
:mod:`desiutil.modules` that is *based on* the Python init file supplied by
the Modules infrastructure.

Find Module File
----------------

:command:`desiInstall` will search for a module file in ``$WORKING_DIR/etc``.  If that
module file is not found, :command:`desiInstall` will use the file that comes with
desiutil_ (*i.e.*, this product's own module file).

Load Dependencies
-----------------

:command:`desiInstall` will scan the module file identified in the previous stage, and
will module load any dependencies found in the file.

Configure Module File
---------------------

:command:`desiInstall` will scan :envvar:`WORKING_DIR` to determine the details that need
to be added to the module file.  The final module file will then be written
into the DESI module directory at NERSC.  If ``--default`` is specified
on the command line, an appropriate .version file will be created. Module
files are always installed with world-read permissions.

Load Module
-----------

:command:`desiInstall` will load the module file just created to set up any environment
variables needed by the install.  At this point it is also safe to assume that
the environment variables :envvar:`WORKING_DIR` and :envvar:`INSTALL_DIR` exist.
It will also set :envvar:`PRODUCT_VERSION`, where ``PRODUCT`` will be replaced
by the actual name of the package, *e.g.*, :envvar:`DESIMODEL_VERSION`.

Create site-packages
--------------------

If the build-type 'py' is detected, a site-packages directory will be
created in :envvar:`INSTALL_DIR`.  If necessary, this directory will be
added to Python's :data:`sys.path`.

Can We Just Copy the Download?
------------------------------

If the build-type is *only* 'plain', or if a branch install is
requested, the downloaded code will be copied to :envvar:`INSTALL_DIR`.
Further Python or C/C++ install steps described below will be skipped.

Run pip
-------

If the build-type 'py' is detected, :command:`pip install .` will be run
at this point.

Build C/C++ Code
----------------

If the build-type 'make' is detected, :command:`make install` will be run in
:envvar:`WORKING_DIR`.  If the build-type 'src' is detected, :command:`make -C src all`
will be run in :envvar:`INSTALL_DIR`.

Download Extra Data
-------------------

If :command:`desiInstall` detects ``etc/product_data.sh``, where ``product`` should be
replaced by the actual name of the package, it will download extra data
not bundled with the code.  The script should download data *directly* to
:envvar:`INSTALL_DIR`. The script should *only* be used
with :command:`desiInstall` and unit tests.  Note that here are other, better ways to
install and manipulate data that is bundled *with* a Python package.

Compile in Branch Installs
--------------------------

In a few cases (fiberassign_, specex_) code needs to be compiled even when
installing a branch.  If :command:`desiInstall` detects a branch install *and*
the script ``etc/product_compile.sh`` exists, :command:`desiInstall` will run this
script, supplying the Python executable path as a single command-line argument.
The script itself is intended to be a thin wrapper on *e.g.*::

    #!/bin/bash
    py=$1
    ${py} setup.py build_ext --inplace


.. _fiberassign: https://github.com/desihub/fiberassign
.. _specex: https://github.com/desihub/specex

Fix Permissions
---------------

The permissions of :envvar:`INSTALL_DIR` will be recursively set to standard
values under these circumstances:

1. World-read, unless ``--no-world`` is specified on the command line.
2. Unwriteable to all, unless a branch install is being performed, in which
   case user-write is set.

Clean Up
--------

The original download directory, specified by :envvar:`WORKING_DIR`, is removed,
unless ``--keep`` is specified on the command line.
