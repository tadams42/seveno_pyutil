#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from __future__ import absolute_import, print_function

import io
import re
from glob import glob
from os.path import basename, dirname, join, splitext

from setuptools import find_packages, setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


setup(
    name="seveno_pyutil",
    version='0.2.10',
    license='MIT',
    description="Various unsorted Python utilities",
    long_description='%s\n%s' % (
        re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub('', read('README.rst')),
        re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))
    ),
    author="Tomislav Adamic",
    author_email="tomislav.adamic@gmail.com",
    url="https://github.com/tadams42/seveno_pyutil",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=[
        "utilities"
    ],
    # List run-time dependencies HERE.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'pytz',
        'tzlocal',
        'colorlog',
        'marshmallow',
        'pygments',
        'sqlparse'
    ],
    # List additional groups of dependencies HERE (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev]
    extras_require={
        'dev': [
            'pycodestyle',
            'yapf',
            'bumpversion',
            'isort',
            'check-manifest',

            # IPython stuff
            'ipython',
            'jupyter',
            'ipdb',

            # Docs and viewers
            'sphinx',
            'sphinx_rtd_theme',

            # py.test stuff
            'pytest >= 3.0.0',
            'pytest-pythonpath',
            'colored-traceback',
            'pytest-sugar',
            'pytest-cov',
            'pytest-mock',

            'coverage',
            'factory-boy',
            'faker',
        ]
    }
)
