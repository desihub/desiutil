====================================
Welcome to desiutil's documentation!
====================================

Introduction
============

desiutil is a set of low-level utilities used by all DESI_ packages.

.. _DESI: https://desi.lbl.gov

Dependencies
============

Required Dependencies
+++++++++++++++++++++

These packages must be installed for desiutil to work properly:

* `pyyaml <https://pyyaml.org/>`_
* `requests <https://requests.readthedocs.io/>`_
* `astropy <https://www.astropy.org/>`_

  - This implies a dependency on `NumPy <https://numpy.org>`_

Optional Dependencies
+++++++++++++++++++++

If you want to use the plotting utilities in :mod:`desiutil.plots`, you will
need:

* `matplotlib <https://matplotlib.org/>`_
* `healpy <https://healpy.readthedocs.io/en/latest/>`_

Contents
========

.. toctree::
   :maxdepth: 1

   api.rst
   desiInstall.rst
   changes.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
