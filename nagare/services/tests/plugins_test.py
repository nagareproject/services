# Encoding: utf-8

#=-
# (C)opyright Net-ng 2012-2015
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
#=-

import os
import sys
from nagare.services import plugins, plugin


class TestPlugin1(plugin.Plugin):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}
    CATEGORY = 'TEST'
    TEST_VALUE = 42


class TestPlugin2(plugin.Plugin):
    CONFIG_SPEC = {'value1': 'integer(default=10)', 'value2': 'string(default="$root/b.txt")'}
    CATEGORY = 'TEST'
    TEST_VALUE = 43
    LOAD_PRIORITY = 10


def discover_plugin_test1():
    class Plugins(plugins.Plugins):
        ENTRY_POINTS = 'nagare.services.test1'

    repository = Plugins()
    all_plugins = repository.discover()

    assert len(all_plugins) == 1

    test_plugin = all_plugins[0]
    assert test_plugin.get_entry_name() == 'test_plugin'
    assert test_plugin.get_project_name() == 'nagare-services'
    assert test_plugin.get_config() is None

    assert test_plugin.CATEGORY == 'TEST'
    assert test_plugin.TEST_VALUE == 42


def discover_plugin_test2():
    repository = plugins.Plugins(entry_points='nagare.services.test1')
    all_plugins = repository.discover()

    assert len(all_plugins) == 1

    test_plugin = all_plugins[0]
    assert test_plugin.get_entry_name() == 'test_plugin'
    assert test_plugin.get_project_name() == 'nagare-services'
    assert test_plugin.get_config() is None

    assert test_plugin.CATEGORY == 'TEST'
    assert test_plugin.TEST_VALUE == 42


def load_priority_test():
    repository = plugins.Plugins(entry_points='nagare.services.test2')
    all_plugins = repository.discover()

    assert [plugin.get_entry_name() for plugin in all_plugins] == ['test_plugin1', 'test_plugin2']

    repository = plugins.Plugins(entry_points='nagare.services.test3')
    all_plugins = repository.discover()

    assert [plugin.get_entry_name() for plugin in all_plugins] == ['test_plugin1', 'test_plugin2']


def read_config_test():
    class Plugins(plugins.Plugins):
        ENTRY_POINTS = 'nagare.services.test2'
        CONFIG_SECTION = 'my_plugins'

    repository = Plugins()
    all_plugins = repository.discover()

    conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
    conf = repository.read_config(all_plugins, conf_filename, sys.stderr.write, '/tmp/test')

    assert len(conf['test_plugin1']) == 2
    assert conf['test_plugin1']['value1'] == 20
    assert conf['test_plugin1']['value2'] == '/tmp/test/a.txt'

    assert len(conf['test_plugin2']) == 2
    assert conf['test_plugin2']['value1'] == 10
    assert conf['test_plugin2']['value2'] == '/tmp/test/b.txt'


def activate_test():
    class Plugins(plugins.Plugins):
        ENTRY_POINTS = 'nagare.services.test2'
        CONFIG_SECTION = 'my_plugins'

    repository = Plugins()
    all_plugins = repository.discover()
    conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
    conf = repository.read_config(all_plugins, conf_filename, sys.stderr.write, '/tmp/test')

    assert len(conf['test_plugin1']) == 2
    plugin1 = all_plugins[0]

    assert plugin1.get_config() is None
    repository.activate(plugin1, conf_filename, conf['test_plugin1'], sys.stderr.write)
    assert len(plugin1.get_config()) == 2
    assert plugin1.get_config()['value1'] == 20
    assert plugin1.get_config()['value2'] == '/tmp/test/a.txt'


def load_test1():
    class Plugins(plugins.Plugins):
        ENTRY_POINTS = 'nagare.services.test2'
        CONFIG_SECTION = 'my_plugins'

    repository = Plugins()

    conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
    repository.load(conf_filename, sys.stderr.write, '/tmp/test')
    assert len(repository) == 2

    (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()
    assert plugin1_name == 'test_plugin1'
    assert len(plugin1.get_config()) == 2
    assert plugin1.get_config()['value1'] == 20
    assert plugin1.get_config()['value2'] == '/tmp/test/a.txt'

    assert plugin2_name == 'test_plugin2'
    assert len(plugin2.get_config()) == 2
    assert plugin2.get_config()['value1'] == 10
    assert plugin2.get_config()['value2'] == '/tmp/test/b.txt'


def load_test2():
    class Plugins(plugins.Plugins):
        CONFIG_SECTION = 'my_plugins'

    conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
    repository = Plugins(conf_filename, sys.stderr.write, {'root': '/tmp/test'}, 'nagare.services.test2')
    assert len(repository) == 2

    (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()
    assert plugin1_name == 'test_plugin1'
    assert len(plugin1.get_config()) == 2
    assert plugin1.get_config()['value1'] == 20
    assert plugin1.get_config()['value2'] == '/tmp/test/a.txt'

    assert plugin2_name == 'test_plugin2'
    assert len(plugin2.get_config()) == 2
    assert plugin2.get_config()['value1'] == 10
    assert plugin2.get_config()['value2'] == '/tmp/test/b.txt'
