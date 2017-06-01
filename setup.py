# Encoding: utf-8

# --
# (C)opyright Net-ng 2012-2017
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os

from setuptools import setup, find_packages


with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as version:
    VERSION = version.readline().rstrip()


setup(
    name='nagare-services',
    version=VERSION,
    author='Net-ng',
    author_email='alain.poirier@net-ng.com',
    description='Loadable plugins and services injection',
    license='proprietary',
    keywords='',
    url='',
    packages=find_packages(),
    zip_safe=False,
    install_requires=('configobj',),
    namespace_packages=('nagare', 'nagare.services'),
    tests_require=('nose',),
    test_suite='nose.collector',
)
