==========
Change Log
==========

4.0.0 (unreleased)
------------------

*Planned*:

* Remove deprecated commands in :mod:`desiutil.setup`.
* Remove deprecated module :mod:`desiutil.census`.
* Remove deprecated top-level ``setup.py``.

3.4.2 (2023-11-29)
------------------

* Fully support adding units and comments to FITS table columns (PR `#201`_).
* Created :mod:`desiutil.names` and added a function to it that takes an RA
  and DEC and produces a DESINAME that can be used to refer to a DESI
  object at that sky location (PR `#203`_).

.. _`#201`: https://github.com/desihub/desiutil/pull/201
.. _`#203`: https://github.com/desihub/desiutil/pull/203

3.4.1 (2023-09-25)
------------------

* Added functions to :mod:`desiutil.depend` to support removing dependencies
  from headers (PR `#202`_).

.. _`#202`: https://github.com/desihub/desiutil/pull/202

3.4.0 (2023-09-14)
------------------

* Add tools for adding units to :class:`~astropy.table.Table` columns (PR `#199`_).

.. _`#199`: https://github.com/desihub/desiutil/pull/199

3.3.1 (2023-06-13)
------------------

* Ensure old IERS cache files do not actually trigger an exception (PR `#195`_).
* Allow :command:`desiInstall` to install files world-readable (PR `#195`_).

.. _`#195`: https://github.com/desihub/desiutil/pull/195

3.3.0 (2023-05-04)
------------------

* Migrate ``python setup.py`` commands to stand-alone scripts, maintaining some
  compatibility until version 4.0 (PR `#190`_).

.. _`#190`: https://github.com/desihub/desiutil/pull/190

3.2.6 (2022-08-26)
------------------

* :command:`desiInstall` uses desihub location of simqso fork (commit e963344_).
* Allow :command:`desiInstall` to remove permission-locked directories;
  suppress certain :command:`pip` warnings (PR `#185`_).
* Allow :command:`desiInstall` to compile code in certain branch installs (PR `#188`_).
* Add `gpu_specter`_ to known packages (PR `#189`_).

.. _e963344: https://github.com/desihub/desiutil/commit/e963344cd072255174187d2bd6da72d085745abd
.. _`#185`: https://github.com/desihub/desiutil/pull/185
.. _`#188`: https://github.com/desihub/desiutil/pull/188
.. _`#189`: https://github.com/desihub/desiutil/pull/189
.. _`gpu_specter`: https://github.com/desihub/gpu_specter

3.2.5 (2022-01-20)
------------------

* Update :func:`desiutil.depend.add_dependencies` to include key environment
  variables like :envvar:`DESI_ROOT` (PR `#183`_).

.. _`#183`: https://github.com/desihub/desiutil/pull/183

3.2.4 (2022-01-10)
------------------

* Update :meth:`desiutil.plots.plot_grid_map` to support matplotlib 3.5
  (PR `#181`_).

.. _`#181`: https://github.com/desihub/desiutil/pull/181

3.2.3 (2021-10-27)
------------------

* Optionally compute the MW dust transmission in the WISE bands (PR `#175`_).
* Do not treat messages printed on STDERR as errors during :command:`desiInstall` (PR `#176`_).
* Add :meth:`desiutil.brick.Bricks.brick_tan_wcs_size` to compute required size of TAN-projection WCS tiles (PR `#177`_).
* Improve some test coverage; RTD fixes (PR `#178`_).

.. _`#175`: https://github.com/desihub/desiutil/pull/175
.. _`#176`: https://github.com/desihub/desiutil/pull/176
.. _`#177`: https://github.com/desihub/desiutil/pull/177
.. _`#178`: https://github.com/desihub/desiutil/pull/178


3.2.2 (2021-06-03)
------------------

* Add support to :func:`~desiutil.modules.config_module` for packages like
  QuasarNP_ where the GitHub name is capitalized but the internal Python
  package isn't (PR `#173`_).

.. _`#173`: https://github.com/desihub/desiutil/pull/173
.. _QuasarNP: https://github.com/desihub/QuasarNP

3.2.1 (2021-05-13)
------------------

* Changes in :mod:`desiutil.dust`: use Fitzpatrick reddening, add
  :func:`~desiutil.dust.dust_transmission` function, include GAIA bands (PR `#171`_).
* :func:`desiutil.depend.possible_dependencies`: add fiberassign, desimeter, and
  gpu_specter (direct commit).

.. _`#171`: https://github.com/desihub/desiutil/pull/171

3.2.0 (2021-03-29)
------------------

* Use :command:`pip install .` instead of :command:`python setup.py install` (PR `#168`_).

.. _`#168`: https://github.com/desihub/desiutil/pull/168

3.1.2 (2021-02-15)
------------------

* Fixes for Numpy 1.20 (PR `#162`_).
* :command:`desiInstall` auto derive build type "py" or "make" or "src"
  but don't combine them (PR `#163`_).
* :command:`desiInstall` only fallback to NERSC default installdir
  if ``--root`` isn't specified (PR `#163`_).
* Add :func:`desiutil.depend.mergedep` to merge DEPNAMnn/DEPVERnn
  dependencies between different headers (PR `#164`_)

.. _`#162`: https://github.com/desihub/desiutil/pull/162
.. _`#163`: https://github.com/desihub/desiutil/pull/163
.. _`#164`: https://github.com/desihub/desiutil/pull/164

3.1.1 (2020-12-23)
------------------

* ``astropy.erfa`` no longer exists in more recent versions of Astropy
  (PR `#159`_).
* Add function :func:`dust.extinction_total_to_selective_ratio` (PR `#157`_).

.. _`#157`: https://github.com/desihub/desiutil/pull/157
.. _`#159`: https://github.com/desihub/desiutil/pull/159

3.1.0 (2020-12-11)
------------------

* Migrate unit tests to GitHub Actions; allow :command:`desiInstall` to handle a
  diversity of possible branch names (PR `#156`_).
* Add :mod:`~desiutil.redirect` for utilites related to redirecting STDOUT (PR `#153`_).
* Add :class:`~desiutil.timer.Timer` class to standardize timing reports (PRs `#151`_, `#152`_).

.. _`#151`: https://github.com/desihub/desiutil/pull/151
.. _`#152`: https://github.com/desihub/desiutil/pull/152
.. _`#153`: https://github.com/desihub/desiutil/pull/153
.. _`#156`: https://github.com/desihub/desiutil/pull/156

3.0.3 (2020-08-04)
------------------

* Improve installation robustness when parsing :envvar:`DESICONDA` environment variable;
  fix py3.8 SyntaxWarnings about "is not" usage (PR `#150`_).

.. _`#150`: https://github.com/desihub/desiutil/pull/150

3.0.2 (2020-07-31)
------------------

* Travis testing with old healpy and old astropy (PR `#149`_).
* Use https to avoid redirect for data downloads (PR `#148`_).

.. _`#149`: https://github.com/desihub/desiutil/pull/149
.. _`#148`: https://github.com/desihub/desiutil/pull/148

3.0.1 (2020-06-12)
------------------

* Start migrating to use :command:`pytest` to run tests instead of
  :command:`python setup.py test` (PR `#145`_).
* Update package list in :mod:`desiutil.install`;
  enable parallel :command:`make` (PR `#143`_).
* Protect against running :command:`fix_permissions.sh` in :envvar:`HOME`
  (PR `#142`_).

.. _`#145`: https://github.com/desihub/desiutil/pull/145
.. _`#143`: https://github.com/desihub/desiutil/pull/143
.. _`#142`: https://github.com/desihub/desiutil/pull/142

3.0.0 (2020-04-15)
------------------

Note: minor :mod:`desiutil.plots` API and usage changes due to PR `#141`_
so moving to major version 3.0.0, even though the majority of desiutil
remains compatible with 2.x.x

* Remove all dependency on basemap_ (PR `#141`_).

.. _`#141`: https://github.com/desihub/desiutil/pull/141

2.0.3 (2020-04-10)
------------------

* Add IERS functions originally in `desisurvey`_ (PR `#139`_).

.. _`desisurvey`: https://github.com/desihub/desisurvey
.. _`#139`: https://github.com/desihub/desiutil/pull/139

2.0.2 (2020-01-25)
------------------

* Update NERSC paths for CFS (PR `#137`_).

.. _`#137`: https://github.com/desihub/desiutil/pull/137

2.0.1 (2019-09-24)
------------------

* Updated to latest `ReadTheDocs configuration`_; standardized
  some docstrings for better appearance (PR `#136`_).
* No code changes.

.. _`ReadTheDocs configuration`: https://docs.readthedocs.io/en/stable/config-file/v2.html
.. _`#136`: https://github.com/desihub/desiutil/pull/136

2.0.0 (2019-09-15)
------------------

* **This version does not support Python 2.**
* No significant API changes, however.

1.9.16 (2019-08-09)
-------------------

* Add support for auto-generating API documentation via
  :command:`python setup.py api` (PR `#131`_).
* Fix basemap plot tests by using unique axes (PR `#135`_).

.. _`#131`: https://github.com/desihub/desiutil/pull/131
.. _`#135`: https://github.com/desihub/desiutil/pull/135

1.9.15 (2018-12-14)
-------------------

* Add :func:`desiutil.dust.ext_odonnell` and :func:`desiutil.dust.ext_ccm`
  originally from desispec (PR `#128`_).
* Update permissions set by :command:`fix_permissions.sh` (PR `#126`_).
* Set read-only permissions on all Module files, and unlock them as needed (PR `#125`_).
* Draw ecliptic in all-sky plots (PR `#124`_).

.. _`#128`: https://github.com/desihub/desiutil/pull/128
.. _`#126`: https://github.com/desihub/desiutil/pull/126
.. _`#125`: https://github.com/desihub/desiutil/pull/125
.. _`#124`: https://github.com/desihub/desiutil/pull/124

1.9.14 (2018-10-05)
-------------------

* Restrict write access on software installed with :command:`desiInstall` (PR `#122`_).

.. _`#122`: https://github.com/desihub/desiutil/pull/122

1.9.13 (2018-09-06)
-------------------

* Add ``/maps`` to the default dust directory (PR `#119`_).

.. _`#119`: https://github.com/desihub/desiutil/pull/119

1.9.12 (2018-09-05)
-------------------

* Port the dust map code from desitarget to desiutil (PR `#116`_).

.. _`#116`: https://github.com/desihub/desiutil/pull/116

1.9.11 (2018-05-10)
-------------------

* Installing extra data happens *after* the main install, to prevent
  collisions in creating the install directory (Issue `#102`_, PR `#109`_).
* ``fix_permissions.sh`` ignores the group-write bit (Issue `#108`_, PR `#109`_).
* Remove support for a :command:`desiInstall` configuration file.  All options
  are specified on the command-line (Issue `#103`_, PR `#109`_).
* Update sklearn module to support updates to ``sklearn.mixture.GaussianMixture``
  (PR `#111`_).
* Added scatter option to :func:`desiutil.plots.plot_slices`;
  avoid slow PNG generation for large data samples (PR `#112`_).

.. _`#102`: https://github.com/desihub/desiutil/issues/102
.. _`#103`: https://github.com/desihub/desiutil/issues/103
.. _`#108`: https://github.com/desihub/desiutil/issues/108
.. _`#109`: https://github.com/desihub/desiutil/pull/109
.. _`#111`: https://github.com/desihub/desiutil/pull/111
.. _`#112`: https://github.com/desihub/desiutil/pull/112

1.9.10 (2018-03-29)
-------------------

* Remove support for :command:`desiInstall` in environments other than
  NERSC (PR `#101`_).
* Try as best as possible that Python executable scripts are installed with
  an explicit desiconda version (PR `#105`_).

.. _`#101`: https://github.com/desihub/desiutil/pull/101
.. _`#105`: https://github.com/desihub/desiutil/pull/105

1.9.9 (2017-12-20)
------------------

* Enhance :mod:`desiutil.log` with a context manager (PR `#92`_), and
  change the way the log level is set.
* Avoid logging interference with :func:`desiutil.log.get_logger` is called
  with different log levels (PR `#93`_).
* Use :mod:`unittest.mock` to increase test coverage.

.. _`#92`: https://github.com/desihub/desiutil/pull/92
.. _`#93`: https://github.com/desihub/desiutil/pull/93


1.9.8 (2017-11-09)
------------------

* Adds redrock, surveysim, desisurvey, and healpy to dependency version checks.
* Adds redrock and surveysim to known products for installation.
* Fix team name in license file.
* Support new ``/global/common/software`` filesystem at NERSC.
* Support ``coriknl`` versions of desiconda_.

1.9.7 (2017-09-29)
------------------

* Fixed some test failures that occurred in the NERSC environment and/or
  in an installed package, as opposed to a git checkout (PR `#80`_).
* Fixed bug in :meth:`desiutil.brick.Bricks.brick_radec` handling scalar inputs
  (PR `#81`_).
* Fixed bugs that could cause bricks to be slightly too big, and that
  incorrectly special-cased the north pole with brick sizes that don't
  evenly divide 180 degrees (PR `#84`_).
* Adds ``return_grid_data`` option to :func:`desiutil.plots.plot_sky_binned`
  (PR `#85`_).
* Added tests of :mod:`desiutil.sklearn` (PR `#86`_).

.. _`#80`: https://github.com/desihub/desiutil/pull/80
.. _`#81`: https://github.com/desihub/desiutil/pull/81
.. _`#84`: https://github.com/desihub/desiutil/pull/84
.. _`#86`: https://github.com/desihub/desiutil/pull/86
.. _`#85`: https://github.com/desihub/desiutil/pull/85


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
