==============
Helper Scripts
==============

Python Scripts
==============

API Generation
--------------

:command:`desi_api_file` creates an API file for a DESI software product.
The command is meant to be run in a git clone (or svn checkout) of a software
product.  It creates ``doc/api.rst``, with a link to every ``*.py`` file in the
software product.

Example::

    git clone https://github.com/desihub/desiexample.git
    cd desiexample
    desi_api_file desiexample

:command:`desi_api_file` will refuse to overwrite an existing file, unless the
``--overwrite`` option is supplied.  The ``--overwrite`` option is a good way
to ensure that your API documentation is in sync with the actual Python files
in the software product.

Note: this command *replaces* the capability::

    python setup.py api

that was provided in earlier versions of desiutil.

Module File Generation
----------------------

:command:`desi_module_file` creates a `Module file`_ for a DESI software product.
It is meant to be run in the working directory or git clone of a software product.

Normally this step is automatically performed by :doc:`desiInstall <./desiInstall>`, but
this script is provided to create Module files independently of :command:`desiInstall`.

Example::

    git clone https://github.com/desihub/desispec.git
    cd desispec
    desi_module_file -m /separate/module/directory/modulefiles desispec main

.. _`Module file`: https://docs.nersc.gov/environment/modules/

Note: this command *replaces* the capability::

    python setup.py module_file

that was provided in earlier versions of desiutil.

Version String Update
---------------------

:command:`desi_update_version` creates or updates ``py/packagename/_version.py``.
In most DESI packages, this file is then used to create ``__version__``
in the top-level ``__init__.py`` file::

    from ._version import __version__

To create or update a ``_version.py`` file for a git clone::

    git clone https://github.com/desihub/desispec.git
    cd desispec
    desi_update_version desispec

The actual version string is based on the last known tag and the number of
git commits.

In preparation for a tag, the version string should be set explicitly::

    desi_update_version --tag 1.2.3 desispec
    git tag 1.2.3

Note: this command *replaces* the capability::

    python setup.py version

that was provided in earlier versions of desiutil.

Update IERS Data
----------------

:command:`update_iers_frozen` is an internal utility command that updates
data files stored in the desiutil package that are used with :mod:`desiutil.iers`.
See that module for further details.

Shell Scripts
=============

Bootstrap DESI Environment
--------------------------

:command:`desiBootstrap.sh` is used to set up a bare-bones DESI software
environment, for example, for an entirely new system at NERSC.  It downloads
and sets up a version of desiutil, which it then uses to :command:`desiInstall`
an "official" version of desiutil.  From there, that "official" version can
be used to :command:`desiInstall` other DESI software packages.

Set DESI-friendly Permissions
-----------------------------

:command:`fix_permissions.sh` recursively changes permissions in a directory
to match DESI standards:

* All files belong to group ``desi``;
* All files are readable by group ``desi``;
* All directories are at least readable and accessible by group ``desi``.

See also the `NERSC filesystem discussion`_.

Example::

    fix_permissions.sh /global/cfs/cdirs/desi/users/desi

.. _`NERSC filesystem discussion`: https://desi.lbl.gov/trac/wiki/Computing/NerscFileSystem#FileSystemAccess
