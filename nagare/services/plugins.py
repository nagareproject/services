# Encoding: utf-8
# =-
# (C)opyright Net-ng 2012-2017
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
# =-

"""Plugins registry"""

import logging

import configobj
import pkg_resources

from . import config


logger = logging.getLogger(__name__)


class Plugins(dict):
    ENTRY_POINTS = None  # Section where to read the entry points
    CONFIG_SECTION = None  # Parent section of the plugins in the application configuration file

    def __init__(self, conf_filename=None, error=None, conf=None, entry_points=None):
        """Eager / lazy loading the plugins

        In:
          - ``conf_filename`` -- the path to the configuration file
          - ``error`` -- the function to call in case of configuration errors
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
        """
        self.entry_points = entry_points or self.ENTRY_POINTS

        if conf_filename is not None:
            # If a configuration is defined, load the plugins
            self.load(conf_filename, error, conf and conf.get('root'))

    def compare_load_order(self, plugin1, plugin2):
        """Sort the plugin loading order

        In:
          - ``plugin1`` -- first plugin to compare
          - ``plugin2`` -- second plugin to compare
        """
        return cmp(plugin1.LOAD_PRIORITY, plugin2.LOAD_PRIORITY)

    def discover(self):
        """Read the plugins

        Return:
          - the plugins list sorted on their ``LOAD_PRIORITY`` attribute
        """
        plugins = []

        for entry in pkg_resources.iter_entry_points(self.entry_points):
            plugin = entry.load()
            plugin.set_entry_name(entry.name)
            plugin.set_project_name(entry.dist.project_name)

            plugins.append(plugin)

        return sorted(plugins, self.compare_load_order)

    def read_config(self, plugins, conf_filename, error, root):
        """Read and validate all the plugins configurations

        In:
          - ``plugins`` -- the plugins
          - ``conf_filename`` -- the path to the configuration file
          - ``error`` -- the function to call in case of configuration errors
          - ``root`` -- the filesystem path to the project

        Return:
          - ``configobj`` parent section of the plugins configurations
        """
        if not self.CONFIG_SECTION:
            return {}

        # Merge the configuration specifications of all the plugins
        spec = {plugin.get_entry_name(): plugin.CONFIG_SPEC for plugin in plugins}
        spec = configobj.ConfigObj({self.CONFIG_SECTION: spec, 'root': 'string(default="%s")' % root})

        plugins_conf = configobj.ConfigObj(conf_filename, configspec=spec, interpolation='Template')
        config.validate(conf_filename, plugins_conf, error)

        return plugins_conf[self.CONFIG_SECTION]

    def activate(self, plugin, conf_filename, conf, error):
        """Activate the plugin with its configuration

        In:
          - ``plugin`` -- the plugin to activate (the class loaded from the entry point)
          - ``conf_filename`` -- the path to the configuration file
          - ``conf`` -- the ``configobj`` configuration
          - ``error`` -- the function to call in case of configuration errors

        Return:
          - the activated plugin
        """
        plugin.set_config(conf)
        return plugin  # By default the plugin is the Python class loaded from the entry point

    def register(self, name, plugin):
        """Register a plugin

        In:
          - ``name`` -- name of the plugin
          - ``plugin`` -- the plugin
        """
        self[name] = plugin

    def load(self, conf_filename=None, error=None, root=None):
        """Activate and register the plugins

        In:
          - ``conf_filename`` -- the path to the configuration file
          - ``error`` -- the function to call in case of configuration errors
          - ``root`` -- the filesystem path to the project
        """
        plugins = self.discover()
        plugins_conf = self.read_config(plugins, conf_filename, error, root or '')

        for plugin in plugins:
            category = '%s ' % plugin.CATEGORY if plugin.CATEGORY else ''

            name = plugin.get_entry_name()
            if name in self:
                print 'Name conflict: %s<%s> already defined' % (category, name)
                raise NameError(name)

            try:
                plugin_conf = plugins_conf.get(name)
                if plugin_conf:
                    plugin_conf = plugin_conf.dict()

                plugin_instance = self.activate(plugin, conf_filename, plugin_conf, error)
                if plugin_instance is not None:
                    self.register(name, plugin_instance)
            except:
                print "%s<%s> can't be loaded" % (category.capitalize(), name)
                raise

        return self

    def items(self):
        """Return the (name, plugin) list

        Return:
          - the (name, plugin) list sorted on the ``LOAD_PRIORITY`` attribute of the plugins
        """
        return sorted(super(Plugins, self).items(), key=lambda (_, plugin): plugin.LOAD_PRIORITY)

    def keys(self):
        """Return the names of the plugins

        Return:
          - the names list sorted on the ``LOAD_PRIORITY`` attribute of the plugins
        """
        return [name for name, _ in self.items()]

    def __iter__(self):
        """Return an iterator on the names of the plugins

        Return:
          - the names iterator sorted on the ``LOAD_PRIORITY`` attribute of the plugins
        """
        return iter(self.keys())

    def values(self):
        """Return the plugins

        Return:
          - the plugins list sorted on the their ``LOAD_PRIORITY`` attribute
        """
        return [plugin for _, plugin in self.items()]

    def copy(self):
        new = self.__class__()
        new.update(self)

        return new
