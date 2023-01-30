# Encoding: utf-8

# --
# Copyright (c) 2008-2023 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import distutils  # noqa: F401
import json
import logging
import warnings

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

warnings.filterwarnings('ignore', module='_distutils')

try:

    from importlib.metadata import distribution

    def get_editable_project_location(dist):
        content = distribution(dist.project_name).read_text('direct_url.json')
        if content is None:
            location = None
        else:
            url = json.loads(content)['url']
            location = urlparse.urlsplit(url)[2]

        return location

except ImportError:

    try:
        from pip._internal.metadata import pkg_resources

        logging.getLogger('pip._internal.utils.packaging').setLevel('ERROR')
        logging.getLogger('pip._internal.metadata.pkg_resources').setLevel('ERROR')

        def get_editable_project_location(dist):
            return getattr(pkg_resources.Distribution(dist), 'editable_project_location', None)

    except ImportError:

        def get_editable_project_location(dist):
            return None


def Distribution(dist):
    dist.editable_project_location = get_editable_project_location(dist)
    return dist
