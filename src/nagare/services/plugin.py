# Encoding: utf-8
# --
# Copyright (c) 2008-2023 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Base classes for the loadable plugins."""

from __future__ import absolute_import

import logging

from nagare.config import ParameterError, config_from_dict

from . import plugins


class Plugin(object):
    """The plugin is a class."""

    DESC = ''
    # Specification of the plugin configuration, read from the application
    # configuration file (http://www.voidspace.org.uk/python/configobj.html#validate)
    PLUGIN_CATEGORY = 'nagare.plugins'
    CONFIG_SPEC = {'activated': 'boolean(default=True)'}
    LOAD_PRIORITY = 1000  # The plugins are loaded from lowest to highest priority value

    def __init__(self, name_, dist, **config):
        self.name = name_
        config.setdefault('activated', True)
        self.plugin_config = config

    @property
    def logger(self):
        return logging.getLogger(self.PLUGIN_CATEGORY + '.' + self.name)

    @logger.setter
    def logger(self, logger):
        pass


class PluginsPlugin(plugins.Plugins, Plugin):
    """The plugin is itself a plugins registry."""

    def __init__(self, name_, dist, **config):
        plugins.Plugins.__init__(self)
        Plugin.__init__(self, name_, dist, **config)


class SelectionPlugin(PluginsPlugin):
    SELECTOR = 'type'
    CONFIG_SPEC = dict({SELECTOR: 'string'}, **PluginsPlugin.CONFIG_SPEC)

    def __init__(self, name_, dist, type, **config):
        self.selector = config[self.SELECTOR] = type
        super(SelectionPlugin, self).__init__(name_, dist, **config)
        self.load_plugins(name_, config_from_dict({self.SELECTOR: type, name_: config}))

    @classmethod
    def iter_entry_points(cls, name, entry_points, config=None):
        """Read the entry points.

        In:
          - ``entry_points`` -- section where to read the entry points

        Return:
          - the entry points
        """
        if not config:
            return []

        entries = {
            name: (dist, entry) for dist, name, entry in PluginsPlugin.iter_entry_points(name, entry_points, config)
        }

        selector = config.get(cls.SELECTOR)
        if not selector:
            raise ParameterError('required', sections=[name], name=cls.SELECTOR)

        if selector not in entries:
            choices = list(map("'{}'".format, entries))
            error = "invalid value '{}', ".format(selector)
            if choices:
                error += 'can only be {}'.format(' or '.join(choices))
            else:
                error += 'no choice available'

            raise ParameterError(error, sections=[name], name=cls.SELECTOR)

        dist, entry = entries[selector]
        return [(dist, name, entry)]

    @staticmethod
    def get_plugin_spec(entry, name, cls, plugin, children):
        f, args = next(children, (lambda: (name, {}, []), ()))
        _, spec, children = f(*args)

        return name, dict(cls.CONFIG_SPEC, **spec), children

    @classmethod
    def _walk(cls, plugin, name, entry_points, config, global_config, activated_by_default, get_children):
        selector = plugin.SELECTOR
        selector_value = config.get(selector)
        if selector_value is not None:
            config[selector] = config_from_dict({selector: selector_value}).interpolate(global_config)[selector]

        return super(SelectionPlugin, cls)._walk(
            plugin, name, entry_points, config, global_config, activated_by_default, get_children
        )

    @property
    def plugin(self):
        return list(self.values())[0]

    def _load_plugin(self, name_, dist, plugin_cls, **config):
        config = config.copy()
        del config[self.SELECTOR]

        return super(SelectionPlugin, self, name_, dist, plugin_cls, **config)
