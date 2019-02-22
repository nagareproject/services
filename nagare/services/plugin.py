# Encoding: utf-8
# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Base classes for the loadable plugins"""

from __future__ import absolute_import

import logging

from . import plugins, exceptions


class Plugin(object):
    """The plugin is a class"""

    DESC = ''
    # Specification of the plugin configuration, read from the application
    # configuration file (http://www.voidspace.org.uk/python/configobj.html#validate)
    CONFIG_SPEC = {}
    LOAD_PRIORITY = 1000  # The plugins are loaded from lowest to highest priority value

    def __init__(self, name, dist, **config):
        self.name = name
        self.plugin_category = 'nagare.plugins'
        self._plugin_config = None

    @property
    def logger(self):
        return logging.getLogger(self.plugin_category + '.' + self.name)

    @logger.setter
    def logger(self, logger):
        pass

    @property
    def plugin_spec(self):
        return self.CONFIG_SPEC

    @property
    def plugin_config(self):
        return self._plugin_config

    def format_info(self, names=(), type_=None):
        yield ''


class PluginsPlugin(plugins.Plugins, Plugin):
    """The plugin is itself a plugins registry"""

    def __init__(self, name, dist, **config):
        plugins.Plugins.__init__(self, config, '')
        Plugin.__init__(self, name, dist)


class SelectionPlugin(PluginsPlugin):
    CONFIG_SPEC = {'type': 'string(default=None)'}
    WITH_INITIAL_CONFIG = True

    def __init__(self, name, dist, type, **config):
        self.type = type

        config = {type: config} if type else {}
        super(SelectionPlugin, self).__init__(name, dist, **config)

    @property
    def plugin_spec(self):
        return dict(
            self.plugin.plugin_spec,
            **super(SelectionPlugin, self).plugin_spec
        )

    @property
    def plugin_config(self):
        return dict(
            self.plugin.plugin_config,
            **super(SelectionPlugin, self).plugin_config
        )

    @property
    def plugin(self):
        try:
            return self[self.type]
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
