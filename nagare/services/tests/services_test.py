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

from nagare.services import services, service


class DummyServices(services.Services):
    @staticmethod
    def iter_entry_points(section):
        egg_path = os.path.join(os.path.dirname(__file__), 'nagare_services.egg')
        return pkg_resources.WorkingSet([egg_path]).iter_entry_points(section)


class DummyService(service.Service):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}
    CATEGORY = 'TEST'
    TEST_VALUE = 42

    def __init__(self, conf_filename, error, value1, value2):
        self.value1 = value1
        self.value2 = value2
        self.test_value = self.TEST_VALUE


class TestService(unittest.TestCase):
    def load_service_test1(self):
        class Services(DummyServices):
            ENTRY_POINTS = 'nagare.services.test4'
            CONFIG_SECTION = 'my_services'

        repository = Services()

        conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
        repository.load(conf_filename, sys.stderr.write, root='/tmp/test')
        self.assertEqual(len(repository), 1)

        ((service1_name, service1),) = repository.items()

        self.assertEqual(service1_name, 'service1')
        self.assertEqual(service1.get_entry_name(), 'service1')
        self.assertEqual(service1.test_value, 42)
        self.assertEqual(service1.value1, 20)
        self.assertEqual(service1.value2, '/tmp/test/a.txt')

    def load_service_test2(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
        repository = DummyServices(conf_filename, sys.stderr.write, 'nagare.services.test4', root='/tmp/test')
        self.assertEqual(len(repository), 1)

        ((service1_name, service1),) = repository.items()

        self.assertEqual(service1_name, 'service1')
        self.assertEqual(service1.get_entry_name(), 'service1')
        self.assertEqual(service1.test_value, 42)
        self.assertEqual(service1.value1, 20)
        self.assertEqual(service1.value2, '/tmp/test/a.txt')

    def services_injection_of_service_test(self):
        conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
        repository = services.Services(conf_filename, sys.stderr.write, 'nagare.services.test4', root='/tmp/test')

        self.assertEqual(repository(lambda services_service: services_service), repository)
