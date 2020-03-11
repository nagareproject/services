# Encoding: utf-8
# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Plugins registry

The plugins are read from an entry point and configured from a file
"""

from collections import OrderedDict

import configobj
import pkg_resources

from .config import validate
from .reporters import PluginsReporter


class Plugins(OrderedDict):
    ENTRY_POINTS = ''  # Section where to read the entry points
    CONFIG_SECTION = None  # Parent section of the plugins in the application configuration file

    def __init__(
            self,
            config=None, config_section=None,
            entry_points=None,
            activated_by_default=True,
            **initial_config
    ):
        """Eager / lazy loading of the plugins

        In:
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- if defined, overloads the ``CONFIG_SECTION`` class attribute
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
          - ``initial_config`` -- other configuration parameters not read from the configuration file
        """
        super(Plugins, self).__init__()

        self.entry_points = entry_points or self.ENTRY_POINTS
        self.activated_by_default = activated_by_default

        # Load the plugins only if the ``config`` object exists
        if config is not None:
            self.load_plugins(config, config_section, **initial_config)

    @staticmethod
    def load_order(plugin):
        """Get the loading order of a plugin

        In:
          - ``plugin`` -- the plugin

        Returns:
          - value to sort the plugin on
        """
        return plugin.LOAD_PRIORITY  # By default, the plugins are sorted on their ``LOAD_PRIORITY`` value

    def iter_entry_points(self):
        """Read the entry points

        In:
          - ``entry_points`` -- section where to read the entry points

        Return:
          - the entry points
        """
        return list(pkg_resources.iter_entry_points(self.entry_points))

    def load_activated_plugins(self, activations=None):
        entries = self.iter_entry_points()

        plugins = [(entry, entry.load()) for entry in entries if (activations is None) or (entry.name in activations)]
        plugins.sort(key=lambda plugin: self.load_order(plugin[1]))

        return list(OrderedDict((entry.name, (entry, plugin)) for entry, plugin in plugins).values())

    @staticmethod
    def merge_initial_config(config, **initial_config):
        """Merge some variables into the plugins config

        In:

          - ``config`` -- ``ConfigObj`` configuration object of the plugins configuration
          - ``initial_config`` -- variables to merge into the config
        """
        config.merge(initial_config)

    def read_config(self, spec, config, config_section, interpolation='TemplateWithDefaults', **initial_config):
        """Read and validate all the plugins configurations

        In:
          - ``plugins`` -- the plugins
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- parent section of the plugins in the application configuration file
          - ``initial_config`` -- other configuration parameters not read from the configuration file

        Return:
          - the ``ConfigObj`` validated section of the plugins configurations
        """
        if config_section:
            spec = {config_section: spec}

        plugins_conf = configobj.ConfigObj(config, configspec=spec, interpolation=interpolation)

        self.merge_initial_config(plugins_conf, **initial_config)
        validate(plugins_conf, getattr(config, 'filename', None))

        return (plugins_conf[config_section] if config_section else plugins_conf).dict()

    @staticmethod
    def _load_plugin(name, dist, plugin_cls, initial_config, plugin_config, *args, **kw):
        """Load and activate a plugin

        In:
          - ``plugin`` -- the plugin

        Returns:
          - the plugin
        """
        config = dict(plugin_config, **kw)

        return plugin_cls(name, dist, *args, **config), config

    def load_plugins(self, config, config_section=None, **initial_config):
        """Load, configure, activate and register the plugins

        In:
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- if defined, overloads the ``CONFIG_SECTION`` class attribute
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
          - ``initial_config`` -- other configuration parameters not read from the configuration file
        """
        entries = self.iter_entry_points()
        activations = self.read_config(
            {entry.name: {'activated': 'boolean(default=%s)' % self.activated_by_default} for entry in entries},
            config, self.CONFIG_SECTION if config_section is None else config_section,
            **initial_config
        )
        activated_plugins = {entry.name for entry in entries if activations[entry.name]['activated']}

        plugins = self.load_activated_plugins(activated_plugins)

        config = self.read_config(
            {entry.name: plugin.CONFIG_SPEC for entry, plugin in plugins},
            config, self.CONFIG_SECTION if config_section is None else config_section,
            **initial_config
        )

        for entry, plugin in plugins:
            name = entry.name

            try:
                plugin_config = config[name]
                plugin_config.pop('activated', None)

                plugin_instance, plugin_config = self._load_plugin(
                    name, entry.dist,
                    plugin,
                    initial_config, plugin_config
                )

                if plugin_instance is not None:
                    plugin_instance._plugin_config = plugin_config
                    self[name.replace('.', '_')] = plugin_instance
            except Exception:
                print("'%s' can't be loaded" % name)
                raise

    def copy(self, **kw):
        """Create a new copy of this registry

        Returns:
          - the new registry
        """
        new = self.__class__()
        new.update(self)
        new.update(kw)

        return new

    def report(self, title='Plugins', activated_columns=None, criterias=lambda plugins, name, plugin: True):
        plugins = self.load_activated_plugins()

        plugins = [(entry.name, entry.dist, plugin) for entry, plugin in plugins]
        plugins = filter(lambda plugin: criterias(self, plugin[0], plugin[2]), plugins)

        print(title + ':\n')

        if not plugins:
            print('  <empty>')
        else:
            plugins = {name: (dist, plugin) for name, dist, plugin in plugins}
            plugins = [(dist, name, plugin, self.get(name.replace('.', '_'))) for name, (dist, plugin) in plugins.items()]

            PluginsReporter().report({'name', 'order', 'x'} | (activated_columns or set()), plugins)
