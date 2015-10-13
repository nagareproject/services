# Encoding: utf-8

#=-
# (C)opyright Net-ng 2012-2015
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
#=-

from .plugin import Plugin

"""Base class for the loadable services"""


class Service(Plugin):
    def __init__(self, conf_filename, error):
        """Initialization

        In:
          - ``conf_filename`` -- the path to the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        pass

