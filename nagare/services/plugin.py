# Encoding: utf-8
# --
# Copyright (c) 2008-2020 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Base classes for the loadable plugins"""

from __future__ import absolute_import

import logging
from collections import OrderedDict

from . import plugins, exceptions


class Plugin(object):
    """The plugin is a class"""

    DESC = ''
    # Specification of the plugin configuration, read from the application
    # configuration file (http://www.voidspace.org.uk/python/configobj.html#validate)
    PLUGIN_CATEGORY = 'nagare.plugins'
    CONFIG_SPEC = {'activated': 'boolean(default=True)'}
    LOAD_PRIORITY = 1000  # The plugins are loaded from lowest to highest priority value

    @classmethod
    def get_plugin_spec(cls):
        return OrderedDict(sorted(cls.CONFIG_SPEC.items()))

    def __init__(self, name, dist, **config):
        self.name = name
        self._plugin_config = config

    @property
    def logger(self):
        return logging.getLogger(self.PLUGIN_CATEGORY + '.' + self.name)

    @logger.setter
    def logger(self, logger):
        pass

    @property
    def plugin_spec(self):
        return self.get_plugin_spec()

    @property
    def plugin_config(self):
        return OrderedDict(sorted(self._plugin_config.items()), activated=True)

    def format_info(self, names=(), type_=None):
        yield ''


class PluginsPlugin(plugins.Plugins, Plugin):
    """The plugin is itself a plugins registry"""

    def __init__(self, name, dist, **config):
        plugins.Plugins.__init__(self, config, '')
        Plugin.__init__(self, name, dist)


class SelectionPlugin(PluginsPlugin):
    CONFIG_SPEC = dict(PluginsPlugin.CONFIG_SPEC, type='string(default=None)')
    WITH_INITIAL_CONFIG = True

    def __init__(self, name, dist, type, **config):
        self.type = type

        config = {type: config} if type else {}
        super(SelectionPlugin, self).__init__(name, dist, **config)

    @property
    def plugin_spec(self):
        return dict(self.plugin.plugin_spec, **self.CONFIG_SPEC)

    @property
    def plugin_config(self):
        return dict(self.plugin.plugin_config, type=self.type)

    @property
    def plugin(self):
        try:
            return self[self.type.replace('.', '_')]
        except KeyError:
            self.raise_not_found()

    def raise_not_found(self):
        error = 'section "[{}]", parameter "{}": '.format(self.name, list(self.CONFIG_SPEC)[0])
        error += 'missing parameter' if self.type is None else'invalid value `{}`'.format(self.type)
        exc = exceptions.BadConfiguration(error)
        exc.__cause__ = None

        raise exc

    def load_activated_plugins(self, activations=None):
        return super(SelectionPlugin, self).load_activated_plugins({self.type})

    def format_info(self, names=()):
        if self.plugin:
            for line in self.plugin.format_info(
                names + (self.name,),
                next(iter(self.CONFIG_SPEC))
            ):
                yield line
