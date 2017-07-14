==========
Change Log
==========

1.9.7 (unreleased)
------------------

* Fixed some test failures that occurred in the NERSC environment and/or
  in an installed package, as opposed to a git checkout (PR `#80`_).

.. _`#80`: https://github.com/desihub/desiutil/pull/80


1.9.6 (2017-07-12)
------------------

* Changed the location where code is installed so that code is correctly
  matched to the corresponding DESI+Anaconda (desiconda_) version (PR `#77`_).

.. _`#77`: https://github.com/desihub/desiutil/pull/77
.. _desiconda: https://github.com/desihub/desiconda

1.9.5 (2017-06-15)
------------------

* Improved correctness and functionality of :mod:`desiutil.brick` (PR `#74`_).

.. _`#74`: https://github.com/desihub/desiutil/pull/74


1.9.4 (2017-06-01)
------------------

* Moved ``desispec.brick`` to :mod:`desiutil.brick` (PR `#70`_).
* Get .travis.yml file and other components ready for Python 3.6.
* Increase test coverage in a few areas.
* Make basemap_ an optional dependency (PR `#61`_).
* Fix :command:`desiInstall` on cori.
* Add :mod:`desiutil.census` to calculate DESI disk space use.

.. _basemap: http://matplotlib.org/basemap/
.. _`#61`: https://github.com/desihub/desiutil/pull/61
.. _`#63`: https://github.com/desihub/desiutil/pull/63
.. _`#70`: https://github.com/desihub/desiutil/pull/70

1.9.3 (2017-03-01)
------------------

* Added new :mod:`desiutil.sklearn` module and
  :class:`distutils.sklearn.GaussianMixtureModel` class to save and
  sample from a Gaussian mixture model.
* Added new functions for creating all-sky maps (PR `#52`_) with an
  accompanying tutorial notebook in `doc/nb/`.
* Add option to :command:`fix_permissions.sh` to remove group-writeability for
  "official" data. Also, make sure that files and directories are group-readable.
* Moved logging infrastructure from desispec (PR `#56`_).

.. _`#52`: https://github.com/desihub/desiutil/pull/52
.. _`#56`: https://github.com/desihub/desiutil/pull/56

1.9.2 (2016-11-18)
------------------

* Enables desiInstall of desihub_ packages even if they aren't in the
  ``desiutil.install.known_products`` list yet.
* Include :mod:`desiutil.plots` in documentation.

.. _desihub: https://github.com/desihub

1.9.1 (2016-10-17)
------------------

* Allow top-level ``/python`` directories to be detected (not just ``/py``)
  to support redmonster_.

.. _redmonster: https://github.com/desihub/redmonster

1.9.0 (2016-10-12)
------------------

* Shorten Python version printed in dependency headers.
* :mod:`desiutil.test.test_plots` was not cleaning up after itself.
* Support new DESI+Anaconda software stack infrastructure (PR `#43`_).
* Fixes :meth:`~desiutil.bitmask.BitMask.names` when mask is a
  :class:`numpy.uint64` (`desihub/desitarget#79`_).
* :meth:`~desiutil.bitmask.BitMask.names` is much faster.
* Fixed problem opening tar files in Python 3.

.. _`#43`: https://github.com/desihub/desiutil/pull/43
.. _`desihub/desitarget#79`: https://github.com/desihub/desitarget/pull/79

1.8.0 (2016-09-10)
------------------

* Added :func:`~desiutil.io.encode_table` and :func:`~desiutil.io.decode_table`
  for converting string columns in tables between unicode and bytes (PR `#41`_).
* Set apache permissions by number instead of by name.

.. _`#41`: https://github.com/desihub/desiutil/pull/41

1.7.0 (2016-08-18)
------------------

* Added :func:`~desiutil.io.combine_dicts` function.
* Added :mod:`desiutil.plots` module including :func:`~desiutil.plots.plot_slices`.

1.6.0 (2016-07-01)
------------------

* Fixed some import statements so documentation will build on readthedocs.
* :func:`~desiutil.depend.add_dependencies` to add DEPNAM/DEPVER for
  common DESI dependencies

1.5.0 (2016-06-09)
------------------

* Fixed bug affecting people with the C version of Modules installed on
  laptops.
* Added :mod:`desiutil.depend` tools for manipulating DEPNAMnn and DEPVERnn
  keywords in FITS headers.

1.4.1 (2016-06-07)
------------------

* Don't consider warning messages about astropy_helpers to be errors.
* Update desiInstall documentation, adding information about environment
  variables.
* Use :class:`distutils.command.sdist.sdist` to ensure that ``MANIFEST.in``
  is respected.
* Add some test coverage in :mod:`desiutil.setup`.
* Cleaned up documentation of :mod:`desiutil.io` and several other modules.
* Modified conversion of keys to string in :mod:`desituil.io.yamlify`
* Log IP address in Travis Tests.

1.4.0 (2016-04-28)
------------------

* Fix module processing problem for non-DESI Python packages.
* Allow NERSC Modules root directory to be overridden in a configuration file.
* :mod:`desiutil.stats` module was previously snuck in, but never documented.
* Minor fixes for desiInstall bootstrap mode.
* PR `#30`_: Enable use of weights in :func:`~desiutil.funcfits.iter_fit`.
* Add a method for connverting Python objects to yaml-ready format.
  Includes :class:`unicode` to :class:`str` conversion.

.. _`#30`: https://github.com/desihub/desiutil/pull/30

1.3.6 (2016-03-25)
------------------

* Include :mod:`~desiutil.funcfits` in the documentation; added
  :func:`~desiutil.funcfits.mk_fit_dict`.
* Improve coverage of :mod:`~desiutil.funcfits`.
* Try to use a nicer Sphinx theme for documentation.

1.3.5 (2016-03-15)
------------------

* Ignore some additional MANIFEST.in warnings.
* Allow known_products and cross-install configuration to be overridden
  using an optional configuration file.
* Allow products to specify a method to download additional data not
  bundled with the code.

1.3.4 (2016-02-22)
------------------

* Support GitHub tags that start with 'v'.
* Add support for `speclite`_.

.. _`speclite`: https://github.com/dkirkby/speclite

1.3.3 (2016-02-03)
------------------

* Added :mod:`~desiutil.stats` module to compute percentiles on distributions.

1.3.2 (2016-01-25)
------------------

* Recent versions of setuptools do not include ``setuptools.compat``.  A
  simple workaround was added to fix that.

1.3.1 (2016-01-12)
------------------

* Update MANIFEST.in file.
* Ignore additional warnings produced by MANIFEST.in.
* Always run ``fix_permissions.sh`` after install.
* Remove references to defunct hopper system.

1.3.0 (2015-12-09)
------------------

* Updated docstrings for bitmasks.
* Added :mod:`~desiutil.funcfits` module.

1.2.0 (2015-11-24)
------------------

* Added bitmask processing code, :mod:`desiutil.bitmask`.
* Fixed a minor variable name bug.
* Ignore warnings produced by processing MANIFEST.in.
* Fixed return value in cross_install.
* Fixed a missing run stage.

1.1.1 (2015-11-18)
------------------

* Update the list of NERSC hosts, including cori.
* Code is now `PEP 8`_ compliant.

.. _`PEP 8`: http://legacy.python.org/dev/peps/pep-0008/

1.1.0 (2015-11-06)
------------------

* Don't print scary warning about :envvar:`DESI_PRODUCT_ROOT` not being
  set if running at NERSC.
* Support running ``python setup.py version`` in svn products.
* Move Modules support code into separate sub-package.
* Simplify Travis build system.
* Remove some obsolete files.
* Simplify package structure.

1.0.1 (2015-11-03)
------------------

* Fix issue where the Python tarfile package was failing to autodetect
  gzipped files.

1.0.0 (2015-10-29)
------------------

* pip install support.
* `Travis build support`_.
* `Read the Docs support`_.
* Remove unnecessary Sphinx extensions.
* Create setup subpackage for functions that go in setup.py files.
* fix_permissions.sh won't clobber executable bits.

.. _`Travis build support`: https://travis-ci.org/desihub/desiutil
.. _`Read the Docs support`: http://desiutil.readthedocs.org/en/latest/

0.6.0 (2015-10-13)
------------------

**Note:** This tag should not be used or installed.  It is an intermediate
tag intended to fix a subtle issue with how svn tags are translated into git
tags.

* Fixed a problem with log handling.
* Use ``module switch`` instead of ``module load`` when a module is already
  loaded.
* Add changes.rst file.
* Add LICENSE.rst file.
* Migration to GitHub
  - Change case of desiutil.
  - Add git support functions.

0.5.5 (2015-01-16)
------------------

* Fix a corner case when desiInstall tries to install desiUtil.
* Fix an svn version string parsing error.

0.5.4 (2015-01-16)
------------------

* Fix a minor syntax error.

0.5.3 (2015-01-16)
------------------

* Fix a minor syntax error.

0.5.2 (2015-01-16)
------------------

* Update desiInstall documentation.
* Changes to doc compilation.

0.5.1 (2015-01-14)
------------------

* Update desiInstall documentation.
* Handle ``-hpcp`` module names.
* Move build type detection to separate function.
* Move documentation generation to separate function.
* Add cross-install support.

0.5.0 (2015-01-14)
------------------

* Adding support for GitHub installs.

0.4.2 (2015-01-12)
------------------

* Fix a minor syntax error.

0.4.1 (2015-01-12)
------------------

* Fix a minor syntax error.

0.4.0 (2015-01-12)
------------------

* Major refactor of install, support 'plain' products.
* Use ``svn --non-interactive`` where possible.

0.3.9 (2014-09-12)
------------------

* Change the way tags are sorted.
* Tweak documentation compilation.

0.3.8 (2014-06-24)
------------------

* Change severity of certain log messages.

0.3.7 (2014-06-24)
------------------

* Minor fix to logging.

0.3.6 (2014-06-24)
------------------

* Don't auto-generate the desiInstall script.

0.3.5 (2014-06-24)
------------------

* Use ez_setup.py.

0.3.4 (2014-06-23)
------------------

* Reconfigure how the desiInstall script is created.

0.3.3 (2014-06-23)
------------------

* Tweak module file detection.

0.3.2 (2014-06-23)
------------------

* Fix chmod error.

0.3.1 (2014-06-23)
------------------

* Change ``version()`` to ``__version__``.

0.3.0 (2014-06-10)
------------------

* Change how version strings are set.
* Auto-detect a variety of build types.

0.2.5 (2014-05-26)
------------------

* Fix how the Modules Python init file is detected.

0.2.4 (2014-05-06)
------------------

* Fix directory creation for trunk/branch installs.

0.2.3 (2014-05-02)
------------------

* Change how dependencies are handled in the module file.
* Move some dependency processing to separate function.
* General restructuring.

0.2.2 (2014-05-01)
------------------

* Copy extra files in the etc directory.
* Remove some data files from setup.py.

0.2.1 (2014-05-01)
------------------

* Tweak how versions are reported.

0.2.0 (2014-05-01)
------------------

* Tweak documentation.
* Add ACL detection to fix_permission script.

0.1 (2014-01-09)
----------------

* First tag.
