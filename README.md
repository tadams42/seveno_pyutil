# Overview

[//]: # (start-badges)

[![version](https://img.shields.io/pypi/v/seveno-pyutil.svg)](https://pypi.org/project/seveno-pyutil/)
[![license](https://img.shields.io/pypi/l/seveno-pyutil.svg)](https://opensource.org/licenses/MIT)
[![wheel](https://img.shields.io/pypi/wheel/seveno-pyutil.svg)](https://pypi.org/project/seveno-pyutil/)
[![python_versions](https://img.shields.io/pypi/pyversions/seveno-pyutil.svg)](https://pypi.org/project/seveno-pyutil/)
[![python_implementations](https://img.shields.io/pypi/implementation/seveno-pyutil.svg)](https://pypi.org/project/seveno-pyutil/)
[![travis](https://travis-ci.org/tadams42/seveno_pyutil.svg?branch=master)](https://travis-ci.org/tadams42/seveno_pyutil)
[![docs](https://readthedocs.org/projects/seveno-pyutil/badge/?style=flat)](http://seveno-pyutil.readthedocs.io/en/latest/)

[//]: # (end-badges)

Various unsorted Python utilities.

## Installation

~~~sh
pip install seveno_pyutil
~~~

## Documentation

~~~sh
python setup.py build_sphinx
~~~

## Tests

~~~sh
py.test
~~~

or against multiple Python versions

~~~sh
pip install tox
tox
~~~

## Development mode

Install

~~~sh
python setup.py develop
~~~

Install with extra dev packages

~~~sh
pip install -e .[dev]
~~~

Uninstall

~~~sh
python setup.py develop --uninstall
~~~
