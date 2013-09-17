# coding=utf-8

from setuptools import setup

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'loadimpactsdk'))
from version import __version__

setup(
    name='loadimpactsdk',
    version=__version__,
    author='Load Impact',
    author_email='support@loadimpact.com',
    packages=['loadimpactsdk'],
    url='http://developers.loadimpact.com/',
    license='LICENSE.txt',
    description="The Load Impact API SDK provides Python APIs to create and manage load tests",
    install_requires=['requests'],
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords="loadimpact api rest sdk",
    test_suite='test'
)
