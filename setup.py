# Copyright 2018 ELIFE. All rights reserved.
# Use of this source code is governed by a MIT
# license that can be found in the LICENSE file.

from setuptools import setup

with open("README.md") as f:
    README = f.read()

with open("LICENSE") as f:
    LICENSE = f.read()

setup(
    name='ecg',
    version='0.0.1',
    description='Biological databases -> Networks',
    long_description=README,
    maintainer='Harrison B. Smith; ELIFE',
    maintainer_email='hbs@asu.edu',
    url='https://github.com/ELIFE-ASU/ecg',
    license=LICENSE,
    requires=['glob', 'json', 'networkx', 'pyinform'],
    packages=['ecg'],
    package_data={'ecg': ['data/domain_ec_lists/*.dat', 'data/gmls/*.gml']},
    test_suite='nose.collector', #test
    tests_require=['nose'],
    platforms=['Windows', 'OS X', 'Linux']
)
