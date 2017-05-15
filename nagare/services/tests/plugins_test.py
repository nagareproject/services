# Encoding: utf-8

# =-
# (C)opyright Net-ng 2012-2017
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
# =-

import os
import inspect
import unittest

import pkg_resources

from nagare.services import plugins, plugin


CONFIG = {
    'my_plugins': {
        'test_plugin1': {
            'value1': '20',
            'value2': '$root/a.txt'
        },

        'test_plugin2': {
            'value3': '$greeting world!'
        }
    }
}


class DummyPlugins(plugins.Plugins):
    @staticmethod
    def iter_entry_points(entry_points):
        egg_path = os.path.join(os.path.dirname(__file__), 'nagare_services.egg')
        return pkg_resources.WorkingSet([egg_path]).iter_entry_points(entry_points)


class DummyPlugin1(plugin.ClassPlugin):
    CONFIG_SPEC = {
        'value1': 'integer',
        'value2': 'string'
    }
    CATEGORY = 'TEST'
    TEST_VALUE = 42

    def __init__(self, **config):
        self.config = config


class DummyPlugin2(plugin.SingletonPlugin):
    CONFIG_SPEC = {
        'value1': 'integer(default=10)',
        'value2': 'string(default="$root/b.txt")',
        'value3': 'string'
    }
    CATEGORY = 'TEST'
    TEST_VALUE = 43
    LOAD_PRIORITY = 10

    def __init__(self, **config):
        self.config = config


class PluginsOfPlugins(plugin.PluginsPlugin):
    CONFIG_SPEC = {'value1': 'integer'}

    ENTRY_POINTS = 'nagare.services.auth'
    CONFIG_SECTION = 'authentication'

    @staticmethod
    def iter_entry_points(entry_points):
        egg_path = os.path.join(os.path.dirname(__file__), 'nagare_services.egg')
        return pkg_resources.WorkingSet([egg_path]).iter_entry_points(entry_points)

    def __init__(self, config, config_filename, initial_config, value1):
        super(PluginsOfPlugins, self).__init__(config, config_filename, initial_config)
        self.value1 = value1


class UserPlugin(plugin.ClassPlugin):
    def __init__(self, default_user):
        self.default_user = default_user


class LdapPlugin(plugin.SingletonPlugin):
    CONFIG_SPEC = {'host': 'string', 'port': 'integer'}

    def __init__(self, host, port):
        self.host = host
        self.port = port


class TestPlugins1(unittest.TestCase):
    def setUp(self):
        DummyPlugin1.set_config({})

    def discover_plugin_test1(self):
        repository = DummyPlugins()
        all_plugins = list(repository.discover('nagare.services.test1'))

        self.assertEqual(len(all_plugins), 2)

        test_plugin1, test_plugin2 = all_plugins

        self.assertTrue(inspect.isclass(test_plugin1))

        self.assertEqual(test_plugin1.get_entry_name(), 'test_plugin1')
        self.assertEqual(test_plugin1.get_project_name(), 'nagare-services')

        self.assertEqual(test_plugin1.CATEGORY, 'TEST')
        self.assertEqual(test_plugin1.TEST_VALUE, 42)

        self.assertTrue(inspect.isclass(test_plugin2))

        self.assertEqual(test_plugin2.get_entry_name(), 'test_plugin2')
        self.assertEqual(test_plugin2.get_project_name(), 'nagare-services')

        self.assertEqual(test_plugin2.CATEGORY, 'TEST')
        self.assertEqual(test_plugin2.TEST_VALUE, 43)

    def load_priority_test(self):
        repository = DummyPlugins()
        all_plugins = repository.discover('nagare.services.test1')

        self.assertEqual([plugin.get_entry_name() for plugin in all_plugins], ['test_plugin1', 'test_plugin2'])

        all_plugins = repository.discover('nagare.services.test2')

        self.assertEqual([plugin.get_entry_name() for plugin in all_plugins], ['test_plugin1', 'test_plugin2'])

    def read_config_test1(self):
        repository = DummyPlugins()
        all_plugins = repository.discover('nagare.services.test1')

        conf = repository.read_config(all_plugins, CONFIG, 'my_plugins', root='/tmp/test', greeting='Hello')

        self.assertEqual(len(conf['test_plugin1']), 2)

        self.assertEqual(conf['test_plugin1']['value1'], 20)
        self.assertEqual(conf['test_plugin1']['value2'], '/tmp/test/a.txt')

        self.assertEqual(len(conf['test_plugin2']), 3)
        self.assertEqual(conf['test_plugin2']['value1'], 10)
        self.assertEqual(conf['test_plugin2']['value2'], '/tmp/test/b.txt')
        self.assertEqual(conf['test_plugin2']['value3'], 'Hello world!')

    def read_config_test2(self):
        repository = DummyPlugins()
        all_plugins = repository.discover('nagare.services.test1')

        conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
        conf = repository.read_config(all_plugins, conf_filename, 'my_plugins', root='/tmp/test', greeting='Hello')

        self.assertEqual(len(conf['test_plugin1']), 2)

        self.assertEqual(conf['test_plugin1']['value1'], 20)
        self.assertEqual(conf['test_plugin1']['value2'], '/tmp/test/a.txt')

        self.assertEqual(len(conf['test_plugin2']), 3)
        self.assertEqual(conf['test_plugin2']['value1'], 10)
        self.assertEqual(conf['test_plugin2']['value2'], '/tmp/test/b.txt')
        self.assertEqual(conf['test_plugin2']['value3'], 'Hello world!')

    def load_test1(self):
        class Plugins(DummyPlugins):
            ENTRY_POINTS = 'nagare.services.test1'
            CONFIG_SECTION = 'my_plugins'

        repository = Plugins()

        repository.load_plugins(CONFIG, root='/tmp/test', greeting='Hello')
        self.assertEqual(len(repository), 2)

        (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()

        self.assertTrue(inspect.isclass(plugin1))
        self.assertEqual(plugin1_name, 'test_plugin1')
        self.assertEqual(plugin1.get_config(), {'value1': 20, 'value2': '/tmp/test/a.txt'})

        self.assertFalse(inspect.isclass(plugin2))
        self.assertEqual(plugin2_name, 'test_plugin2')
        self.assertEqual(plugin2.config, {'value1': 10, 'value2': '/tmp/test/b.txt', 'value3': 'Hello world!'})

    def load_test2(self):
        class Plugins(DummyPlugins):
            ENTRY_POINTS = 'nagare.services.test1'
            CONFIG_SECTION = 'my_plugins'

        repository = Plugins()

        conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
        repository.load_plugins(conf_filename, root='/tmp/test', greeting='Hello')
        self.assertEqual(len(repository), 2)

        (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()

        self.assertTrue(inspect.isclass(plugin1))
        self.assertEqual(plugin1_name, 'test_plugin1')
        self.assertEqual(plugin1.get_config(), {'value1': 20, 'value2': '/tmp/test/a.txt'})

        self.assertFalse(inspect.isclass(plugin2))
        self.assertEqual(plugin2_name, 'test_plugin2')
        self.assertEqual(plugin2.config, {'value1': 10, 'value2': '/tmp/test/b.txt', 'value3': 'Hello world!'})

    def load_test3(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
        repository = DummyPlugins.from_file(conf_filename, 'my_plugins', 'nagare.services.test2', root='/tmp/test', greeting='Hello')
        self.assertEqual(len(repository), 2)

        (plugin1_name, plugin1), (plugin2_name, plugin2) = repository.items()

        self.assertTrue(inspect.isclass(plugin1))
        self.assertEqual(plugin1_name, 'test_plugin1')
        self.assertEqual(plugin1.get_config(), {'value1': 20, 'value2': '/tmp/test/a.txt'})

        self.assertFalse(inspect.isclass(plugin2))
        self.assertEqual(plugin2_name, 'test_plugin2')
        self.assertEqual(plugin2.config, {'value1': 10, 'value2': '/tmp/test/b.txt', 'value3': 'Hello world!'})

    def load_test4(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
        repository = DummyPlugins.from_file(conf_filename, 'my_services', 'nagare.services.test3', default_email='admin@localhost')

        self.assertEqual(len(repository), 1)
        (name, plugins_of_plugins) = repository.items()[0]

        self.assertEqual(name, 'authentication')
        self.assertEqual(plugins_of_plugins.value1, 20)

        ldap = plugins_of_plugins['ldap']
        self.assertFalse(inspect.isclass(ldap))
        self.assertEqual(ldap.host, 'localhost')
        self.assertEqual(ldap.port, 389)

        users = plugins_of_plugins['user']
        self.assertTrue(inspect.isclass(users))
        self.assertEqual(users.get_config(), {'default_user': 'John Doe <admin@localhost>'})

        o = users.create_plugin()
        self.assertEqual(o.default_user, 'John Doe <admin@localhost>')

    def instanciate_test(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'plugins.cfg')
        repository = DummyPlugins.from_file(conf_filename, 'my_plugins', 'nagare.services.test2', root='/tmp/test', greeting='Hello')
        self.assertEqual(len(repository), 2)

        plugin1 = repository.values()[0]

        self.assertTrue(inspect.isclass(plugin1))

        o = plugin1.create_plugin()
        self.assertEqual(o.config, {'value1': 20, 'value2': '/tmp/test/a.txt'})

        o = plugin1.create_plugin(value1=42)
        self.assertEqual(o.config, {'value1': 42, 'value2': '/tmp/test/a.txt'})
