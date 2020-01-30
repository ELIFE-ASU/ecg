# Copyright 2019 ELIFE. All rights reserved.
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
    description='jgi/kegg databases -> biochemical jsons/graphs',
    long_description=README,
    maintainer='Harrison B. Smith; ELIFE',
    maintainer_email='hbs@elsi.jp',
    author='Harrison B. Smith; ELIFE',
    project_urls={"github":'https://github.com/ELIFE-ASU/ecg'},
    license=LICENSE,
    install_requires=['docopt','tqdm','biopython','selenium','beautifulsoup4','networkx'],
    packages=['ecg'],
    test_suite='nose.collector', #test
    tests_require=['nose'],
    platforms=['Windows', 'OS X', 'Linux']
)
