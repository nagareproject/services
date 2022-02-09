# Encoding: utf-8
# --
# Copyright (c) 2008-2022 Net-ng.
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

import pkg_resources
from nagare.config import config_from_dict

from .reporters import PluginsReporter


class Plugins(object):
    CONFIG_SPEC = {'activated': 'boolean(default=True)'}
    ENTRY_POINTS = None  # Section where to read the entry points

    def __init__(self, activated_by_default=True):
        """Eager / lazy loading of the plugins

        In:
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
        """
        self.activated_by_default = activated_by_default
        self.plugins = OrderedDict()

    @staticmethod
    def load_order(plugin):
        """Get the loading order of a plugin

        In:
          - ``plugin`` -- the plugin

        Returns:
          - value to sort the plugin on
        """
        return plugin.LOAD_PRIORITY  # By default, the plugins are sorted on their ``LOAD_PRIORITY`` value

    @classmethod
    def iter_entry_points(cls, name, entry_points, config):
        """Read the entry points

        In:
          - ``entry_points`` -- section where to read the entry points

        Return:
          - the entry points
        """
        return [(entry.name, entry) for entry in pkg_resources.iter_entry_points(entry_points)] if entry_points else []

    @classmethod
    def iter_activated_entry_points(cls, name, entry_points, config, global_config, activated_by_default):
        spec = config_from_dict({'activated': 'boolean(default={})'.format(activated_by_default)})

        entries = []

        for plugin_name, entry in cls.iter_entry_points(name, entry_points, config):
            conf = {'activated': config.get(plugin_name, {}).get('activated', str(activated_by_default))}
            conf = config_from_dict(conf).interpolate(global_config).validate(spec)

            if conf['activated']:
                entries.append((plugin_name, entry))

        return entries

    @classmethod
    def load_entry_points(cls, entry_points, config):
        plugins = [(name, entry, entry.load()) for name, entry in entry_points]
        plugins.sort(key=lambda plugin: cls.load_order(plugin[2]))

        return list(OrderedDict((name, (name, entry, plugin)) for name, entry, plugin in plugins).values())

    def _load_plugin(self, name_, dist, plugin_cls, activated=None, **config):
        """Load and activate a plugin

        In:
          - ``plugin`` -- the plugin

        Returns:
          - the plugin
        """
        return plugin_cls(name_, dist, **config)

    def load_plugins(self, name, config=None, global_config=None, validate=False, entry_points=None):
        """Load, configure, activate and register the plugin

        In:
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- if defined, overloads the ``CONFIG_SECTION`` class attribute
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
          - ``initial_config`` -- other configuration parameters not read from the configuration file
        """
        config = config or {}
        if type(config) is dict:
            config = config_from_dict(config)

        entry_points = entry_points or self.ENTRY_POINTS
        entries = self.iter_activated_entry_points(name, entry_points, config, global_config, self.activated_by_default)

        activated_sections = set(e[0] for e in entries)
        config.sections = {name: section for name, section in config.sections.items() if name in activated_sections}

        if validate:

            def extract_infos(spec):
                r = {}

                for f, args in spec:
                    name, config_spec, children = f(*args)
                    r[name] = dict(config_spec, **extract_infos(children))

                return r

            spec = self.walk1(name, entries, config, global_config, self.activated_by_default)
            spec = {name: section for name, section in extract_infos(spec).items() if name in activated_sections}
            spec = config_from_dict(spec)

            config.merge_defaults(spec)
            config.interpolate(global_config).validate(spec)

        if type(config) is not dict:
            config = config.dict()

        plugins = self.load_entry_points(entries, config)
        for name, entry, plugin in plugins:
            try:
                plugin_config = config.get(name, {})
                plugin_instance = self._load_plugin(name, entry.dist, plugin, **plugin_config)
                if plugin_instance is not None:
                    self[name.replace('.', '_')] = plugin_instance
            except Exception:
                print("'%s' can't be loaded" % name)
                raise
        return self

    @staticmethod
    def _walk(o, name, entry_points, config, global_config, activated_by_default, get_children):
        all_entries = o.iter_entry_points(name, entry_points, config) if isinstance(entry_points, str) else entry_points

        if activated_by_default is None:
            activated_entries = all_entries
        else:
            spec = config_from_dict({'activated': 'boolean(default={})'.format(activated_by_default)})

            activated_entries = []

            for plugin_name, entry in all_entries:
                conf = {'activated': config.get(plugin_name, {}).get('activated', str(activated_by_default))}
                conf = config_from_dict(conf).interpolate(global_config).validate(spec)

                if conf['activated']:
                    activated_entries.append((plugin_name, entry))

        for name, entry, cls in o.load_entry_points(activated_entries, config):
            plugin = get_children(o, name, cls)

            if hasattr(plugin, '_walk'):
                children = plugin._walk(
                    plugin,
                    name, plugin.ENTRY_POINTS, config.get(name, {}), global_config,
                    activated_by_default,
                    get_children
                )
            else:
                children = []

            f = getattr(
                cls,
                'get_plugin_spec',
                lambda entry, name, cls, plugin, children: (name, cls.CONFIG_SPEC, children)
            )

            yield f, (entry, name, cls, plugin, children)

    @classmethod
    def walk1(cls, name, entry_points, config, global_config, activated_by_default):
        return cls._walk(
            cls, name, entry_points,
            config, global_config, activated_by_default,
            lambda cls, name, plugin: plugin
        )

    def walk2(self, name):
        return self._walk(
            self, name, self.ENTRY_POINTS,
            {}, {}, None,
            lambda o, name, plugin: o.get(name)
        )

    def report(self, name, title='Plugins', activated_columns=None, criterias=lambda *args: True):

        def extract_infos(plugins, added, level, ancestors):
            infos = []
            for plugin in plugins:
                f, (entry, name, cls, plugin, children) = plugin
                fullname = ancestors + (name,)

                if (fullname not in added) and criterias(entry, fullname, name, cls, plugin):
                    infos.append((entry.dist, level, name, cls, plugin))
                    added.add(fullname)

                for info in extract_infos(children, added, level + 1, fullname):
                    if (fullname not in added):
                        infos.append((entry.dist, level, name, cls, plugin))
                        added.add(fullname)

                    infos.append(info)

            return infos

        plugins = self.walk2(name)
        infos = extract_infos(plugins, set(), 0, ())

        print(title + ':\n')

        if not infos:
            print('  <empty>')
        else:
            PluginsReporter().report({'name', 'order', 'x'} | (activated_columns or set()), infos, False)

    def copy(self, **kw):
        """Create a new copy of this registry

        Returns:
          - the new registry
        """
        new = self.__class__()
        new.update(self)
        new.update(kw)

        return new

    def __len__(self):
        return len(self.plugins)

    def __iter__(self):
        return iter(self.plugins)

    def __setitem__(self, k, v):
        self.plugins[k] = v

    def __getitem__(self, k):
        return self.plugins[k]

    def __delitem__(self, k):
        del self.plugins[k]

    def get(self, k, v=None):
        return self.plugins.get(k, v)

    def update(self, d):
        self.plugins.update(d)

    def keys(self):
        return list(self.plugins)

    def values(self):
        return self.plugins.values()

    def items(self):
        return self.plugins.items()
