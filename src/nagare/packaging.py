# Encoding: utf-8

# --
# Copyright (c) 2008-2024 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import json
import urllib.parse as urlparse
from importlib.metadata import distribution


def Distribution(dist):
    location = None
    content = distribution(dist.metadata['name']).read_text('direct_url.json')
    if content is not None:
        direct_url_info = json.loads(content)
        if direct_url_info.get('dir_info', {}).get('editable', False):
            location = urlparse.urlsplit(direct_url_info['url'])[2]

    dist.editable_project_location = location

    return dist
