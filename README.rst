Overview
========

.. start-badges

|version| |license| |travis| |docs| |wheel| |python_versions|

.. |version| image:: https://img.shields.io/pypi/v/seveno-pyutil.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/seveno-pyutil/

.. |license| image:: https://img.shields.io/pypi/l/seveno-pyutil.svg
    :alt: License
    :target: https://opensource.org/licenses/MIT

.. |wheel| image:: https://img.shields.io/pypi/wheel/seveno-pyutil.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/seveno-pyutil/

.. |python_versions| image:: https://img.shields.io/pypi/pyversions/seveno-pyutil.svg
    :alt: Supported versions
    :target: https://pypi.org/project/seveno-pyutil/

.. |python_implementations| image:: https://img.shields.io/pypi/implementation/seveno-pyutil.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/seveno-pyutil/

.. |travis| image:: https://travis-ci.org/tadams42/seveno_pyutil.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/tadams42/seveno_pyutil

.. |docs| image:: https://readthedocs.org/projects/seveno-pyutil/badge/?style=flat
    :alt: Documentation Status
    :target: http://seveno-pyutil.readthedocs.io/en/latest/

.. end-badges

Various unsorted Python utilities.

Installation
------------

::

    pip install seveno_pyutil

Documentation
-------------

::

    python setup.py build_sphinx

Tests
-----

::

    py.test

or against multiple Python versions

::

    pip install tox
    tox

Development mode
----------------

Install

::

    python setup.py develop --uninstall

Install with extra dev packages

::

    pip install -e .[dev]

Uninstall

::
  
    python setup.py develop --uninstall
