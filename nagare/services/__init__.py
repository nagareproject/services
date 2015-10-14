# Encoding: utf-8

#=-
# (C)opyright Net-ng 2012-2015
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
#=-

try:
    import pkg_resources

    pkg_resources.declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path

    __path__ = extend_path(__path__, __name__)

