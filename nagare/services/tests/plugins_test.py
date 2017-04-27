# Encoding: utf-8

# =-
# (C)opyright Net-ng 2012-2017
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
# =-

import os
import sys
import unittest

import pkg_resources

from nagare.services import plugins, plugin


class DummyPlugins(plugins.Plugins):
    @staticmethod
    def iter_entry_points(section):
        egg_path = os.path.join(os.path.dirname(__file__), 'nagare_services.egg')
        return pkg_resources.WorkingSet([egg_path]).iter_entry_points(section)


class DummyPlugin1(plugin.Plugin):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}
    CATEGORY = 'TEST'
    TEST_VALUE = 42


class DummyPlugin2(plugin.Plugin):
    CONFIG_SPEC = {
        'value1': 'integer(default=10)',
        'value2': 'string(default="$root/b.txt")',
        'value3': 'string'
    }
    CATEGORY = 'TEST'
    TEST_VALUE = 43
    LOAD_PRIORITY = 10


class TestPlugins1(unittest.TestCase):
    def setUp(self):
        DummyPlugin1.set_config(None)
        DummyPlugin2.set_config(None)

    def discover_plugin_test1(self):
        class Plugins(DummyPlugins):
            ENTRY_POINTS = 'nagare.services.test1'

        repository = Plugins()
        all_plugins = repository.discover()

        self.assertEqual(len(all_plugins), 1)

        test_plugin = all_plugins[0]
        self.assertEqual(test_plugin.get_entry_name(), 'test_plugin')
        self.assertEqual(test_plugin.get_project_name(), 'nagare-services')
        self.assertIsNone(test_plugin.get_config())

        self.assertEqual(test_plugin.CATEGORY, 'TEST')
        self.assertEqual(test_plugin.TEST_VALUE, 42)

    def discover_plugin_test2(self):
        repository = DummyPlugins(entry_points='nagare.services.test1')
        all_plugins = repository.discover()

        self.assertEqual(len(all_plugins), 1)

        test_plugin = all_plugins[0]
        self.assertEqual(test_plugin.get_entry_name(), 'test_plugin')
        self.assertEqual(test_plugin.get_project_name(), 'nagare-services')
        self.assertIsNone(test_plugin.get_config())

        self.assertEqual(test_plugin.CATEGORY, 'TEST')
        self.assertEqual(test_plugin.TEST_VALUE, 42)

    def load_priority_test(self):
        repository = DummyPlugins(entry_points='nagare.services.test2')
        all_plugins = repository.discover()

        self.assertEqual([plugin.get_entry_name() for plugin in all_plugins], ['test_plugin1', 'test_plugin2'])

        repository = DummyPlugins(entry_points='nagare.services.test3')
        all_plugins = repository.discover()

        self.assertEqual([plugin.get_entry_name() for plugin in all_plugins], ['test_plugin1', 'test_plugin2'])

    def read_config_test(self):
        class Plugins(DummyPlugins):
            ENTRY_POINTS = 'nagare.services.test2'
            CONFIG_SECTION = 'my_plugins'

        repository = Plugins()
        all_plugins = repository.discover()

        conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
        conf = repository.read_config(all_plugins, conf_filename, sys.stderr.write, root='/tmp/test', greeting='Hello')

        self.assertEqual(len(conf['test_plugin1']), 2)
        self.assertEqual(conf['test_plugin1']['value1'], 20)
        self.assertEqual(conf['test_plugin1']['value2'], '/tmp/test/a.txt')

        self.assertEqual(len(conf['test_plugin2']), 3)
        self.assertEqual(conf['test_plugin2']['value1'], 10)
        self.assertEqual(conf['test_plugin2']['value2'], '/tmp/test/b.txt')
        self.assertEqual(conf['test_plugin2']['value3'], 'Hello world!')

    def activate_test(self):
        class Plugins(DummyPlugins):
            ENTRY_POINTS = 'nagare.services.test2'
            CONFIG_SECTION = 'my_plugins'

        repository = Plugins()
        all_plugins = repository.discover()
        conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
        conf = repository.read_config(all_plugins, conf_filename, sys.stderr.write, root='/tmp/test', greeting='Hello')

        self.assertEqual(len(conf['test_plugin1']), 2)
        plugin1 = all_plugins[0]

        self.assertIsNone(plugin1.get_config())
        repository.activate(plugin1, conf_filename, conf['test_plugin1'], sys.stderr.write)
        self.assertEqual(len(plugin1.get_config()), 2)
        self.assertEqual(plugin1.get_config()['value1'], 20)
        self.assertEqual(plugin1.get_config()['value2'], '/tmp/test/a.txt')

    def load_test1(self):
        class Plugins(DummyPlugins):
            ENTRY_POINTS = 'nagare.services.test2'
            CONFIG_SECTION = 'my_plugins'

        repository = Plugins()

        conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
        repository.load(conf_filename, sys.stderr.write, root='/tmp/test', greeting='Hello')
        self.assertEqual(len(repository), 2)

        (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()
        self.assertEqual(plugin1_name, 'test_plugin1')
        self.assertEqual(len(plugin1.get_config()), 2)
        self.assertEqual(plugin1.get_config()['value1'], 20)
        self.assertEqual(plugin1.get_config()['value2'], '/tmp/test/a.txt')

        self.assertEqual(plugin2_name, 'test_plugin2')
        self.assertEqual(len(plugin2.get_config()), 3)
        self.assertEqual(plugin2.get_config()['value1'], 10)
        self.assertEqual(plugin2.get_config()['value2'], '/tmp/test/b.txt')
        self.assertEqual(plugin2.get_config()['value3'], 'Hello world!')

    def load_test2(self):
        class Plugins(DummyPlugins):
            CONFIG_SECTION = 'my_plugins'

        conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
        repository = Plugins(conf_filename, sys.stderr.write, 'nagare.services.test2', root='/tmp/test', greeting='Hello')
        self.assertEqual(len(repository), 2)

        (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()

        self.assertEqual(plugin1_name, 'test_plugin1')
        self.assertEqual(len(plugin1.get_config()), 2)
        self.assertEqual(plugin1.get_config()['value1'], 20)
        self.assertEqual(plugin1.get_config()['value2'], '/tmp/test/a.txt')

        self.assertEqual(plugin2_name, 'test_plugin2')
        self.assertEqual(len(plugin2.get_config()), 3)
        self.assertEqual(plugin2.get_config()['value1'], 10)
        self.assertEqual(plugin2.get_config()['value2'], '/tmp/test/b.txt')
        self.assertEqual(plugin2.get_config()['value3'], 'Hello world!')

