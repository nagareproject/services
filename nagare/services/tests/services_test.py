# Encoding: utf-8

# =-
# (C)opyright Net-ng 2012-2017
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
# =-

import os
import unittest

import pkg_resources

from nagare.services import service, services
from nagare.services.services import MissingService


class DummyServices(services.Services):
    @staticmethod
    def iter_entry_points(section):
        egg_path = os.path.join(os.path.dirname(__file__), 'nagare_services.egg')
        return pkg_resources.WorkingSet([egg_path]).iter_entry_points(section)


class DummyService1(service.ClassService):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}


class DummyService2(service.SingletonService):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}
    CATEGORY = 'TEST'
    TEST_VALUE = 42
    LOAD_PRIORITY = 10

    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
        self.test_value = self.TEST_VALUE


class DummyService3(service.SingletonService):
    LOAD_PRIORITY = 1


class DummyService4(service.ClassService):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}
    LOAD_PRIORITY = 2

    def __init__(self, value1, value2, service3_service):
        self.value1 = value1
        self.value2 = value2
        self.service3 = service3_service


class DummyService5(service.SingletonService):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}
    LOAD_PRIORITY = 3

    def __init__(self, value1, value2, service3_service):
        self.value1 = value1
        self.value2 = value2
        self.service3 = service3_service


class TestService(unittest.TestCase):
    def load_service_test1(self):
        class Services(DummyServices):
            ENTRY_POINTS = 'nagare.services.test4'
            CONFIG_SECTION = 'my_services'

        services = Services()

        conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
        services.load_plugins(conf_filename, root='/tmp/test')
        self.assertEqual(len(services), 2)

        (service1_name, service1), (service2_name, service2) = services.items()

        self.assertEqual(service1_name, 'service1')
        self.assertEqual(service1.get_entry_name(), 'service1')
        self.assertEqual(service1.get_config(), {'value1': 10, 'value2': '/tmp/test/a.txt'})

        self.assertEqual(service2_name, 'service2')
        self.assertEqual(service2.get_entry_name(), 'service2')
        self.assertEqual(service2.test_value, 42)
        self.assertEqual(service2.value1, 20)
        self.assertEqual(service2.value2, '/tmp/test/b.txt')

    def load_service_test2(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
        services = DummyServices.from_file(conf_filename, 'my_services', 'nagare.services.test4', root='/tmp/test')
        self.assertEqual(len(services), 2)

        (service1_name, service1), (service2_name, service2) = services.items()

        self.assertEqual(service1_name, 'service1')
        self.assertEqual(service1.get_entry_name(), 'service1')
        self.assertEqual(service1.get_config(), {'value1': 10, 'value2': '/tmp/test/a.txt'})

        self.assertEqual(service2_name, 'service2')
        self.assertEqual(service2.get_entry_name(), 'service2')
        self.assertEqual(service2.test_value, 42)
        self.assertEqual(service2.value1, 20)
        self.assertEqual(service2.value2, '/tmp/test/b.txt')

    def injection_of_services_test(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
        services = DummyServices.from_file(conf_filename, entry_points='nagare.services.test4', root='/tmp/test')

        self.assertIs(services(lambda services_service: services_service), services)

    def injection_of_service_test(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
        services = DummyServices.from_file(conf_filename, entry_points='nagare.services.test5', root='/tmp/test')
        self.assertEqual(len(services), 3)

        (_, service3), (service1_name, service1), (service2_name, service2) = services.items()

        self.assertEqual(service1_name, 'service1')
        self.assertEqual(service1.get_entry_name(), 'service1')
        self.assertEqual(service1.get_config(), {'value1': 10, 'value2': '/tmp/test/a.txt'})

        self.assertEqual(service2_name, 'service2')
        self.assertEqual(service2.get_entry_name(), 'service2')
        self.assertEqual(service2.value1, 20)
        self.assertEqual(service2.value2, '/tmp/test/b.txt')
        self.assertIs(service2.service3, service3)

        o = services(service1.create_plugin)

        self.assertEqual(o.value1, 10)
        self.assertEqual(o.value2, '/tmp/test/a.txt')
        self.assertIs(o.service3, service3)

        o = services(service1.create_plugin, value2='/tmp/test/b.txt')

        self.assertEqual(o.value1, 10)
        self.assertEqual(o.value2, '/tmp/test/b.txt')
        self.assertIs(o.service3, service3)

    def activation_test1(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
        services = DummyServices.from_file(conf_filename, 'activation', 'nagare.services.test5', root='/tmp/test')

        self.assertEqual(services.keys(), ['service3', 'service1', 'service2'])
        self.assertEqual(services.keys(only_activated=True), ['service3', 'service1'])

    def activation_test2(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
        services = DummyServices.from_file(conf_filename, 'activation', 'nagare.services.test5', activate_by_default=False, root='/tmp/test')

        self.assertEqual(services.keys(), ['service3', 'service1', 'service2'])
        self.assertEqual(services.keys(only_activated=True), ['service3'])

    def activation_test3(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
        services = DummyServices.from_file(conf_filename, 'activation', 'nagare.services.test5', root='/tmp/test')

        self.assertEqual(services.keys(), ['service3', 'service1', 'service2'])
        self.assertEqual(services.keys(only_activated=True), ['service3', 'service1'])

        services['service1'].activate_plugin(False)
        services['service2'].activate_plugin(True)

        self.assertEqual(services.keys(), ['service3', 'service1', 'service2'])
        self.assertEqual(services.keys(only_activated=True), ['service3', 'service2'])

        r = services(lambda x, y, service2_service: (x, y, service2_service), 42, y='hello')

        self.assertEqual(r[0], 42)
        self.assertEqual(r[1], 'hello')
        self.assertIs(r[2], services['service2'])

        services['service2'].activate_plugin(False)

        self.assertRaises(
            MissingService,
            services,
            lambda x, y, service2_service: (x, y, service2_service), 42, y='hello'
        )
