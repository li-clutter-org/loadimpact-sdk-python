# coding=utf-8

"""
Copyright 2013 Load Impact

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Make sure setup tools is installed, if not install it.
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'loadimpact'))
from version import __version__

setup(
    name='loadimpact',
    version=__version__,
    author='Load Impact',
    author_email='support@loadimpact.com',
    packages=['loadimpact'],
    py_modules = ['ez_setup'],
    url='http://developers.loadimpact.com/',
    license='LICENSE.txt',
    description="The Load Impact SDK provides access to Load Impact's cloud-based performance testing platform",
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
