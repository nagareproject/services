# Encoding: utf-8

# --
# Copyright (c) 2008-2023 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from importlib import metadata
import os
import pathlib

from nagare.config import config_from_dict, config_from_file
from nagare.services import plugin, plugins

CONFIG = config_from_dict(
    {'my_plugins': {'test1': {'value1': '20', 'value2': '$root/a.txt'}, 'test2': {'value3': '$greeting world!'}}}
)


class DummyPlugins(plugins.Plugins):
    ENTRY_POINTS = 'nagare.plugins.test1'

    @classmethod
    def iter_entry_points(cls, name, entry_points, config):
        dist = metadata.PathDistribution(pathlib.Path(__file__).parent)

        return super().iter_entry_points(name, entry_points, config, [dist])


class DummyPlugin1(plugin.Plugin):
    CONFIG_SPEC = dict(plugin.Plugin.CONFIG_SPEC, value1='integer', value2='string')
    CATEGORY = 'TEST1'
    TEST_VALUE = 42

    def __init__(self, name, dist, **config):
        super(DummyPlugin1, self).__init__(name, dist, **config)
        self.name = name
        self.dist = dist


class DummyPlugin2(plugin.Plugin):
    CONFIG_SPEC = dict(
        plugin.Plugin.CONFIG_SPEC, value1='integer(default=10)', value2='string(default="$root/b.txt")', value3='string'
    )
    CATEGORY = 'TEST2'
    TEST_VALUE = 43
    LOAD_PRIORITY = 2000

    def __init__(self, name, dist, **config):
        super(DummyPlugin2, self).__init__(name, dist, **config)
        self.name = name
        self.dist = dist


class PluginsOfPlugins(plugin.PluginsPlugin):
    ENTRY_POINTS = 'nagare.services.auth'
    CONFIG_SPEC = dict(plugin.PluginsPlugin.CONFIG_SPEC, value1='integer')

    def __init__(self, name, dist, value1, **config):
        super(PluginsOfPlugins, self).__init__(name, dist, **config)
        self.load_plugins(name, config)

        self.name = name
        self.dist = dist
        self.value1 = value1

    @classmethod
    def iter_entry_points(cls, name, entry_points, config):
        dist = metadata.PathDistribution(pathlib.Path(__file__).parent)

        return super().iter_entry_points(name, entry_points, config, [dist])


class UserPlugin(plugin.Plugin):
    def __init__(self, name, dist, default_user):
        super(UserPlugin, self).__init__(name, dist, default_user=default_user)
        self.name = name
        self.dist = dist
        self.default_user = default_user


class LdapPlugin(plugin.Plugin):
    CONFIG_SPEC = dict(plugin.Plugin.CONFIG_SPEC, host='string', port='integer')

    def __init__(self, name, dist, host, port):
        super(LdapPlugin, self).__init__(name, dist, host=host, port=port)
        self.name = name
        self.dist = dist
        self.host = host
        self.port = port


# --------------------------------------------------------------------------------------------------------------------


def test_discover_plugin1():
    repository = DummyPlugins()

    entries = repository.iter_entry_points(None, repository.ENTRY_POINTS, {})
    assert len(entries) == 2

    plugins = [(name, cls) for dist, name, entry, cls in repository.load_entry_points(entries, {})]
    ((test_name1, test_plugin1), (test_name2, test_plugin2)) = plugins

    assert test_name1 == 'test1'
    assert test_plugin1 is DummyPlugin1
    assert test_name2 == 'test2'
    assert test_plugin2 is DummyPlugin2


def test_load_priority():
    repository = DummyPlugins()

    entries = repository.iter_entry_points(None, repository.ENTRY_POINTS, {})
    assert len(entries) == 2

    plugins = [name for dist, name, entry, cls in repository.load_entry_points(entries, {})]

    assert plugins == ['test1', 'test2']

    class Plugins(DummyPlugins):
        ENTRY_POINTS = 'nagare.plugins.test2'

    repository = Plugins()

    entries = repository.iter_entry_points(None, repository.ENTRY_POINTS, {})
    assert len(entries) == 2

    plugins = [name for dist, name, entry, cls in repository.load_entry_points(entries, {})]

    assert plugins == ['test1', 'test2']


def test_load1():
    repository = DummyPlugins()
    repository.load_plugins(None, CONFIG['my_plugins'], {'root': '/tmp/test', 'greeting': 'Hello'}, True)
    assert len(repository) == 2

    (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()

    assert plugin1_name == 'test1'
    assert plugin1.dist.metadata['name'] == 'nagare-services'
    assert plugin1.plugin_config == {'activated': True, 'value1': 20, 'value2': '/tmp/test/a.txt'}

    assert plugin2_name == 'test2'
    assert plugin2.name == 'test2'
    assert plugin2.dist.metadata['name'] == 'nagare-services'
    assert plugin2.plugin_config == {
        'activated': True,
        'value1': 10,
        'value2': '/tmp/test/b.txt',
        'value3': 'Hello world!',
    }


def test_load2():
    class Plugins(DummyPlugins):
        ENTRY_POINTS = 'nagare.plugins.test1'

    repository = Plugins()
    config = config_from_file(os.path.join(os.path.dirname(__file__), 'plugins.cfg'))
    repository.load_plugins(None, config['my_plugins'], {'root': '/tmp/test', 'greeting': 'Hello'}, True)
    assert len(repository) == 2

    (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()

    assert plugin1_name == 'test1'
    assert plugin1.dist.metadata['name'] == 'nagare-services'
    assert plugin1.plugin_config == {'activated': True, 'value1': 20, 'value2': '/tmp/test/a.txt'}

    assert plugin2_name == 'test2'
    assert plugin2.name == 'test2'
    assert plugin2.dist.metadata['name'] == 'nagare-services'
    assert plugin2.plugin_config == {
        'activated': True,
        'value1': 10,
        'value2': '/tmp/test/b.txt',
        'value3': 'Hello world!',
    }


def test_load3():
    class Plugins(DummyPlugins):
        ENTRY_POINTS = 'nagare.plugins.test3'

    repository = Plugins()
    config = config_from_file(os.path.join(os.path.dirname(__file__), 'plugins.cfg'))
    repository.load_plugins(None, config['my_plugins2'], {'default_email': 'admin@localhost'}, validate=True)

    assert len(repository) == 1
    (name, plugins_of_plugins) = next(iter(repository.items()))

    assert name == 'authentication'
    assert plugins_of_plugins.name == 'authentication'
    assert plugins_of_plugins.dist.metadata['name'] == 'nagare-services'
    assert plugins_of_plugins.value1 == 20

    ldap = plugins_of_plugins['ldap']
    assert ldap.name == 'ldap'
    assert ldap.dist.metadata['name'] == 'nagare-services'
    assert ldap.host == 'localhost'
    assert ldap.port == 389

    users = plugins_of_plugins['user']
    assert users.name == 'user'
    assert users.dist.metadata['name'] == 'nagare-services'
    assert users.default_user == 'John Doe <admin@localhost>'
