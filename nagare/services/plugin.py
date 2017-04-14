# Encoding: utf-8
# =-
# (C)opyright Net-ng 2012-2017
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
# =-

"""Base class for the loadable plugins"""


class Plugin(object):
    """Base class for the loadable plugins, loaded from entry points"""
    CATEGORY = None  # Category of the plugin
    # Specification of the plugin configuration, read from the application
    # configuration file (http://www.voidspace.org.uk/python/configobj.html#validate)
    CONFIG_SPEC = {}
    LOAD_PRIORITY = 0  # The plugins are loaded from lowest to highest priority

    # These class attributes are set once the plugin is loaded
    entry_name = None  # Name of the entry point
    project_name = None  # Project name where the plugin is defined
    # Configobj plugin configuration, read from the application configuration file
    config = None

    @classmethod
    def set_entry_name(cls, name):
        cls.entry_name = name

    @classmethod
    def get_entry_name(cls):
        return cls.entry_name

    @classmethod
    def set_project_name(cls, name):
        cls.project_name = name

    @classmethod
    def get_project_name(cls):
        return cls.project_name

    @classmethod
    def set_config(cls, config):
        cls.config = config

    @classmethod
    def get_config(cls):
        return cls.config
