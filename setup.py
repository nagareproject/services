# Encoding: utf-8

# --
# Copyright (c) 2008-2018 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from os import path

from setuptools import setup, find_packages

here = path.normpath(path.dirname(__file__))

with open(path.join(here, 'README.rst')) as long_description:
    LONG_DESCRIPTION = long_description.read()

setup(
    name='nagare-services',
    author='Net-ng',
    author_email='alain.poirier@net-ng.com',
    description='Dependency and services injection',
    long_description=LONG_DESCRIPTION,
    license='BSD',
    keywords='',
    url='https://github.com/nagareproject/services',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    setup_requires=['setuptools_scm', 'pytest-runner'],
    use_scm_version=True,
    install_requires=['configobj'],
    tests_require=['pytest']
)
