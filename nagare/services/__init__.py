# Encoding: utf-8

# --
# (C)opyright Net-ng 2012-2017
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from .config import BadConfiguration

try:
    import pkg_resources

    pkg_resources.declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path

    __path__ = extend_path(__path__, __name__)

