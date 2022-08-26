# Encoding: utf-8

# --
# Copyright (c) 2008-2022 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import logging
import warnings
import distutils  # noqa: F401

warnings.filterwarnings('ignore', module='_distutils')

try:
    from pip._internal.metadata import pkg_resources

    logging.getLogger('pip._internal.utils.packaging').setLevel('ERROR')
    logging.getLogger('pip._internal.metadata.pkg_resources').setLevel('ERROR')

    def get_editable_project_location(dist):
        return pkg_resources.Distribution(dist).editable_project_location

except ImportError:

    def get_editable_project_location(dist):
        return None


def Distribution(dist):
    dist.editable_project_location = get_editable_project_location(dist)
    return dist
