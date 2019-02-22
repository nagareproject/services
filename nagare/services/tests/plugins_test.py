# Encoding: utf-8

# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os

import pkg_resources
from configobj import ConfigObj

from nagare.services import plugins, plugin


CONFIG = {
    'my_plugins': {
        'test1': {
            'value1': '20',
            'value2': '$root/a.txt'
        },

        'test2': {
            'value3': '$greeting world!'
        }
    }
}


class DummyPlugins(plugins.Plugins):
    ENTRY_POINTS = 'nagare.plugins.test1'

    def iter_entry_points(self):
        egg_path = os.path.join(os.path.dirname(__file__), 'entry_points')
        return list(pkg_resources.WorkingSet([egg_path]).iter_entry_points(self.entry_points))


class DummyPlugin1(plugin.Plugin):
    CONFIG_SPEC = {
        'value1': 'integer',
        'value2': 'string'
    }
    CATEGORY = 'TEST1'
    TEST_VALUE = 42

    def __init__(self, name, dist, **config):
        self.name = name
        self.dist = dist


class DummyPlugin2(plugin.Plugin):
    CONFIG_SPEC = {
        'value1': 'integer(default=10)',
        'value2': 'string(default="$root/b.txt")',
        'value3': 'string'
    }
    CATEGORY = 'TEST2'
    TEST_VALUE = 43
    LOAD_PRIORITY = 2000

    def __init__(self, name, dist, **config):
        self.name = name
        self.dist = dist


class PluginsOfPlugins(plugin.PluginsPlugin):
    CONFIG_SPEC = {'value1': 'integer'}

    ENTRY_POINTS = 'nagare.services.auth'
    CONFIG_SECTION = 'authentication'

    def __init__(self, name, dist, value1, **config):
        super(PluginsOfPlugins, self).__init__(name, dist, **config)

        self.name = name
        self.dist = dist
        self.value1 = value1

    def iter_entry_points(self):
        egg_path = os.path.join(os.path.dirname(__file__), 'entry_points')
        return list(pkg_resources.WorkingSet([egg_path]).iter_entry_points(self.entry_points))


class UserPlugin(plugin.Plugin):
    def __init__(self, name, dist, default_user):
        self.name = name
        self.dist = dist
        self.default_user = default_user


class LdapPlugin(plugin.Plugin):
    CONFIG_SPEC = {'host': 'string', 'port': 'integer'}

    def __init__(self, name, dist, host, port):
        self.name = name
        self.dist = dist
        self.host = host
        self.port = port


class Selection(plugin.SelectionPlugin):
    ENTRY_POINTS = 'nagare.services.auth'

    def iter_entry_points(self):
        egg_path = os.path.join(os.path.dirname(__file__), 'entry_points')
        return list(pkg_resources.WorkingSet([egg_path]).iter_entry_points(self.entry_points))

# --------------------------------------------------------------------------------------------------------------------


def test_discover_plugin1():
    repository = DummyPlugins()

    entries = repository.iter_entry_points()
    assert len(entries) == 2

    plugins = [(entry.name, cls) for entry, cls in repository.load_activated_plugins()]
    ((test_name1, test_plugin1), (test_name2, test_plugin2)) = plugins

    assert test_name1 == 'test1'
    assert test_plugin1 is DummyPlugin1
    assert test_name2 == 'test2'
    assert test_plugin2 is DummyPlugin2

    plugins = [(entry.name, cls) for entry, cls in repository.load_activated_plugins({'test1', 'test2'})]
    assert len(plugins) == 2
    (test_name1, test_plugin1), (test_name2, test_plugin2) = plugins

    assert test_name1 == 'test1'
    assert test_plugin1 is DummyPlugin1
    assert test_name2 == 'test2'
    assert test_plugin2 is DummyPlugin2

    plugins = [(entry.name, cls) for entry, cls in repository.load_activated_plugins({'test1'})]
    assert len(plugins) == 1
    ((test_name1, test_plugin1),) = plugins

    assert test_name1 == 'test1'
    assert test_plugin1 is DummyPlugin1

    plugins = [(entry.name, cls) for entry, cls in repository.load_activated_plugins({'test2'})]
    assert len(plugins) == 1
    ((test_name2, test_plugin2),) = plugins

    assert test_name2 == 'test2'
    assert test_plugin2 is DummyPlugin2


def test_load_priority():
    repository = DummyPlugins()
    plugins = [entry.name for entry, _ in repository.load_activated_plugins()]

    assert list(plugins) == ['test1', 'test2']

    repository = DummyPlugins(entry_points='nagare.plugins.test2')
    plugins = [entry.name for entry, _ in repository.load_activated_plugins()]

    assert list(plugins) == ['test1', 'test2']


def test_read_config1():
    repository = DummyPlugins()
    spec = {entry.name: plugin.CONFIG_SPEC for entry, plugin in repository.load_activated_plugins()}
    conf = repository.read_config(spec, CONFIG, 'my_plugins', root='/tmp/test', greeting='Hello')

    assert len(conf['test1']) == 2

    assert conf['test1']['value1'] == 20
    assert conf['test1']['value2'] == '/tmp/test/a.txt'

    assert len(conf['test2']) == 3
    assert conf['test2']['value1'] == 10
    assert conf['test2']['value2'] == '/tmp/test/b.txt'
    assert conf['test2']['value3'] == 'Hello world!'


def test_read_config2():
    repository = DummyPlugins()
    spec = {entry.name: plugin.CONFIG_SPEC for entry, plugin in repository.load_activated_plugins()}
    conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
    conf = repository.read_config(spec, ConfigObj(conf_filename), 'my_plugins', root='/tmp/test', greeting='Hello')

    assert len(conf['test1']) == 2

    assert conf['test1']['value1'] == 20
    assert conf['test1']['value2'] == '/tmp/test/a.txt'

    assert len(conf['test2']) == 3
    assert conf['test2']['value1'] == 10
    assert conf['test2']['value2'] == '/tmp/test/b.txt'
    assert conf['test2']['value3'] == 'Hello world!'


def test_load1():
    class Plugins(DummyPlugins):
        CONFIG_SECTION = 'my_plugins'

    repository = Plugins()
    repository.load_plugins(CONFIG, root='/tmp/test', greeting='Hello')
    assert len(repository) == 2

    (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()

    assert plugin1_name == 'test1'
    assert plugin1.dist.project_name == 'nagare-services'
    assert plugin1.plugin_config == {'value1': 20, 'value2': '/tmp/test/a.txt'}

    assert plugin2_name == 'test2'
    assert plugin2.name == 'test2'
    assert plugin2.dist.project_name == 'nagare-services'
    assert plugin2.plugin_config == {'value1': 10, 'value2': '/tmp/test/b.txt', 'value3': 'Hello world!'}


def test_load2():
    class Plugins(DummyPlugins):
        ENTRY_POINTS = 'nagare.plugins.test1'
        CONFIG_SECTION = 'my_plugins'

    repository = Plugins()
    conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
    repository.load_plugins(ConfigObj(conf_filename), root='/tmp/test', greeting='Hello')
    assert len(repository) == 2

    (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()

    assert plugin1_name == 'test1'
    assert plugin1.dist.project_name == 'nagare-services'
    assert plugin1.plugin_config == {'value1': 20, 'value2': '/tmp/test/a.txt'}

    assert plugin2_name == 'test2'
    assert plugin2.name == 'test2'
    assert plugin2.dist.project_name == 'nagare-services'
    assert plugin2.plugin_config == {'value1': 10, 'value2': '/tmp/test/b.txt', 'value3': 'Hello world!'}


def test_load3():
    conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
    repository = DummyPlugins(conf_filename, 'my_plugins2', 'nagare.plugins.test3', default_email='admin@localhost')

    assert len(repository) == 1
    (name, plugins_of_plugins) = next(iter(repository.items()))

    assert name == 'authentication'
    assert plugins_of_plugins.name == 'authentication'
    assert plugins_of_plugins.dist.project_name == 'nagare-services'
    assert plugins_of_plugins.value1 == 20

    ldap = plugins_of_plugins['ldap']
    assert ldap.name == 'ldap'
    assert ldap.dist.project_name == 'nagare-services'
    assert ldap.host == 'localhost'
    assert ldap.port == 389

    users = plugins_of_plugins['user']
    assert users.name == 'user'
    assert users.dist.project_name == 'nagare-services'
    assert users.default_user == 'John Doe <admin@localhost>'


def test_load4():
    conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
    repository = DummyPlugins(conf_filename, 'test4', 'nagare.plugins.test4')

    assert len(repository) == 1
    (name, selection) = next(iter(repository.items()))

    assert name == 'selection'
    plugin = selection.plugin
    assert isinstance(plugin, UserPlugin)
    assert plugin.name == 'user'
    assert plugin.dist.project_name == 'nagare-services'
    assert plugin.default_user == 'John Doe'

    conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
    repository = DummyPlugins(conf_filename, 'test5', 'nagare.plugins.test4')

    assert len(repository) == 1
    (name, selection) = next(iter(repository.items()))

    assert name == 'selection'
    plugin = selection.plugin
    assert plugin.name == 'ldap'
    assert plugin.dist.project_name == 'nagare-services'
    assert plugin.host == 'localhost'
    assert plugin.port == 389
