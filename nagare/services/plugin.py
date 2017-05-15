# Encoding: utf-8
# =-
# (C)opyright Net-ng 2012-2017
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
# =-

"""Base classes for the loadable plugins"""

from . import plugins


class Plugin(object):
    """Base class for loadable plugins, loaded from entry points"""

    CATEGORY = None  # Category of the plugin
    # Specification of the plugin configuration, read from the application
    # configuration file (http://www.voidspace.org.uk/python/configobj.html#validate)
    CONFIG_SPEC = {}
    LOAD_PRIORITY = 0  # The plugins are loaded from lowest to highest priority value

    # These class attributes are set once the plugin is loaded
    entry_name = None  # Name of the entry point
    project_name = None  # Project name where the plugin is defined

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
    def load_plugin(cls, plugin_config, config, config_section, entry_points, config_filename, **initial_config):
        """Plugin factory"""
        return None


class ClassPlugin(Plugin):
    """The plugin is a class"""

    activated = True
    config = {}  # ``Configobj`` plugin configuration, read from the application configuration file

    @classmethod
    def set_config(cls, config):
        cls.config = config

    @classmethod
    def get_config(cls):
        return cls.config

    @classmethod
    def activate_plugin(cls, activated):
        cls.activated = activated

    @classmethod
    def load_plugin(cls, plugin_config, config, config_section, entry_points, config_filename, **initial_config):
        """Create and activate the plugin with its configuration

        In:
          - ``plugin_config`` -- the ``ConfigObj`` section for this plugin
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- parent section of the plugin in the application configuration file
          - ``entry_points`` --  section of the entry point for this plugin
          - ``config_filename`` -- path of the configuration file
          - ``initial_config`` -- other configuration parameters not read from the configuration file

        Return:
          - the activated plugin
        """
        cls.set_config(plugin_config)

        return cls  # By default the plugin is the Python class, loaded from the entry point

    @classmethod
    def create_plugin(cls, *args, **kw):
        """Instanciate an object from this plugin
        """
        return cls(*args, **dict(cls.get_config(), **kw))


class SingletonPlugin(Plugin):
    """The plugin is an object"""

    def activate_plugin(self, activated):
        self.activated = activated

    @classmethod
    def load_plugin(cls, plugin_config, config, config_section, entry_points, config_filename, **initial_config):
        """Create and activate the plugin with its configuration

        In:
          - ``plugin_config`` -- the ``ConfigObj`` section for this plugin
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- parent section of the plugin in the application configuration file
          - ``entry_points`` --  section of the entry point for this plugin
          - ``config_filename`` -- path of the configuration file
          - ``initial_config`` -- other configuration parameters not read from the configuration file

        Return:
          - the activated plugin
        """
        plugin = cls(**plugin_config)
        plugin.activate_plugin(True)

        return plugin


Plugin = SingletonPlugin


class PluginsPlugin(SingletonPlugin, plugins.Plugins):
    """The plugin is itself a plugins registry"""

    @classmethod
    def load_plugin(cls, plugin_config, config, config_section, entry_points, config_filename, **initial_config):
        """Create and activate the plugin with its configuration

        In:
          - ``plugin_config`` -- the ``ConfigObj`` section for this plugin
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- parent section of the plugin in the application configuration file
          - ``entry_points`` --  section of the entry point for this plugin
          - ``config_filename`` -- path of the configuration file
          - ``initial_config`` -- other configuration parameters not read from the configuration file

        Return:
          - the activated plugin
        """
        # Pass the ``config``, ``config_filename`` and ``initial_config`` parameters to the ``__init__`` method
        plugin_config = dict(
            plugin_config,
            config=config, config_filename=config_filename, initial_config=initial_config
        )

        return super(PluginsPlugin, cls).load_plugin(
            plugin_config,
            config, config_section, entry_points, config_filename,
            **initial_config
        )

    def __init__(self, config, config_filename, initial_config):
        # Load the plugins
        super(PluginsPlugin, self).__init__(config, config_filename=config_filename, **initial_config)
