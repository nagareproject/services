# Encoding: utf-8
# =-
# (C)opyright Net-ng 2012-2017
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
# =-

"""Plugins registry

The plugins are read from an entry point and configured from a file
"""

import configobj
import pkg_resources

from .config import validate


class Plugins(dict):
    ENTRY_POINTS = None  # Section where to read the entry points
    CONFIG_SECTION = None  # Parent section of the plugins in the application configuration file

    def __init__(self, config=None, config_section=None, entry_points=None, config_filename=None, **initial_config):
        """Eager / lazy loading of the plugins

        In:
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- if defined, overloads the ``CONFIG_SECTION`` class attribute
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
          - ``config_filename`` -- path of the configuration file
          - ``initial_config`` -- other configuration parameters not read from the configuration file
        """
        # Load the plugins only if the ``config`` object exists
        if config is not None:
            if not isinstance(config, configobj.ConfigObj):
                raise ValueError("Not a `ConfigObj` instance. Don't you want to call the `from_file()` method instead?")

            self.load_plugins(config, config_section, entry_points, config_filename, **initial_config)

    @classmethod
    def from_file(cls, config_filename, config_section=None, entry_points=None, **initial_config):
        """Eager / lazy loading of the plugins

        In:
          - ``config_filename`` -- path of the configuration file
          - ``config_section`` -- if defined, overloads the ``CONFIG_SECTION`` class attribute
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
          - ``initial_config`` -- other configuration parameters not read from the configuration file
        """
        return cls(
            configobj.ConfigObj(config_filename),
            config_section, entry_points, config_filename, **initial_config
        )

    @staticmethod
    def load_order(plugin):
        """Get the loading order of a plugin

        In:
          - ``plugin`` -- the plugin
          
        Returns:
          - value to sort the plugin on
        """
        # By default, the plugins are loaded on their ``LOAD_PRIORITY`` value
        return plugin.LOAD_PRIORITY

    @staticmethod
    def iter_entry_points(entry_points):
        """Read the entry points

        In:
          - ``entry_points`` -- section where to read the entry points

        Return:
          - the entry points
        """
        return pkg_resources.iter_entry_points(entry_points)

    def discover(self, entry_points):
        """Read the plugins

        In:
          - ``entry_points`` -- section where to read the entry points

        Return:
          - the sorted plugins list
        """
        plugins = []

        for entry in self.iter_entry_points(entry_points):
            plugin = entry.load()
            plugin.set_entry_name(entry.name)
            plugin.set_project_name(entry.dist.project_name)

            plugins.append(plugin)

        return sorted(plugins, key=self.load_order)

    def get_plugin_spec(self, plugin):
        """Get the plugin configuration specification
        
        In:
          - ``plugin`` -- the plugin
          
        Returns:
          - the plugin configuration specification
        """
        return plugin.CONFIG_SPEC

    def read_config(self, plugins, config, config_section, config_filename=None, **initial_config):
        """Read and validate all the plugins configurations

        In:
          - ``plugins`` -- the plugins
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- parent section of the plugins in the application configuration file
          - ``config_filename`` -- path of the configuration file
          - ``initial_config`` -- other configuration parameters not read from the configuration file

        Return:
          - the ``ConfigObj`` validated section of the plugins configurations
        """
        if not config_section:
            return {}

        # Merge the configuration specifications of all the plugins
        spec = {plugin.get_entry_name(): self.get_plugin_spec(plugin) for plugin in plugins}
        spec = configobj.ConfigObj({config_section: spec})

        plugins_conf = configobj.ConfigObj(config, configspec=spec, interpolation='Template')
        plugins_conf.merge(initial_config)
        validate(plugins_conf, config_filename)

        return plugins_conf[config_section]

    @staticmethod
    def _load_plugin(plugin, *args, **kw):
        """Load and activate a plugin
        
        In:
          - ``plugin`` -- the plugin
          
        Returns:
          - the plugin
        """
        return plugin.load_plugin(*args, **kw)

    def load_plugins(self, config=None, config_section=None, entry_points=None, config_filename=None, **initial_config):
        """Load, configure, activate and register the plugins

        In:
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- if defined, overloads the ``CONFIG_SECTION`` class attribute
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
          - ``config_filename`` -- path of the configuration file
          - ``initial_config`` -- other configuration parameters not read from the configuration file
        """
        plugins = self.discover(entry_points or self.ENTRY_POINTS)
        plugins_config = self.read_config(
            plugins,
            config, config_section or self.CONFIG_SECTION,
            config_filename,
            **initial_config
        )

        for plugin in plugins:
            category = '%s ' % (plugin.CATEGORY if plugin.CATEGORY else '')

            name = plugin.get_entry_name()
            if name in self:
                print 'Name conflict: %s<%s> already defined' % (category, name)
                raise NameError(name)

            try:
                plugin_config = plugins_config.get(name)
                plugin_config = plugin_config.dict() if plugin_config is not None else {}
                plugin_instance = self._load_plugin(
                    plugin, plugin_config,
                    config, config_section, entry_points, config_filename,
                    **initial_config
                )

                if plugin_instance is not None:
                    self[name] = plugin_instance
            except:
                print "%s<%s> can't be loaded" % (category.capitalize(), name)
                raise

    def items(self, only_activated=False):
        """Return the (name, plugin) list
        
        In:
          - ``only_activated`` -- if ``true``, only the activated plugins are returned

        Return:
          - the (name, plugin) list, sorted on the ``LOAD_PRIORITY`` attribute of the plugins
        """
        items = ((name, plugin) for name, plugin in super(Plugins, self).items() if not only_activated or plugin.activated)
        return sorted(items, key=lambda (_, plugin): self.load_order(plugin))

    def keys(self, only_activated=False):
        """Return the names of the plugins
        
        In:
          - ``only_activated`` -- if ``true``, only the activated plugins are returned

        Return:
          - the names, list sorted on the ``LOAD_PRIORITY`` attribute of the plugins
        """
        return [name for name, _ in self.items(only_activated)]

    def __iter__(self, only_activated=False):
        """Return an iterator on the names of the plugins
        
        In:
          - ``only_activated`` -- if ``true``, only the activated plugins are returned

        Return:
          - the names iterator, sorted on the ``LOAD_PRIORITY`` attribute of the plugins
        """
        return iter(self.keys(only_activated))

    def values(self, only_activated=False):
        """Return the plugins
        
        In:
          - ``only_activated`` -- if ``true``, only the activated plugins are returned

        Return:
          - the plugins list, sorted on the their ``LOAD_PRIORITY`` attribute
        """
        return [plugin for _, plugin in self.items(only_activated)]

    def copy(self):
        """Create a new copy of this registry
        
        Returns:
          - the new registry
        """
        new = self.__class__()
        new.update(self)

        return new
