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
from nagare.services import services, service


class TestService(service.Service):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}
    CATEGORY = 'TEST'
    TEST_VALUE = 42

    def __init__(self, conf_filename, error, value1, value2):
        self.value1 = value1
        self.value2 = value2
        self.test_value = self.TEST_VALUE


def load_service_test1():
    class Services(services.Services):
        ENTRY_POINTS = 'nagare.services.test4'
        CONFIG_SECTION = 'my_services'

    repository = Services()

    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    repository.load(conf_filename, sys.stderr.write, '/tmp/test')
    assert len(repository) == 1

    ((service1_name, service1),) = repository.items()

    assert service1_name == 'service1'
    assert service1.get_entry_name() == 'service1'
    assert service1.test_value == 42
    assert service1.value1 == 20
    assert service1.value2 == '/tmp/test/a.txt'


def load_service_test2():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    repository = services.Services(conf_filename, sys.stderr.write, {'root': '/tmp/test'}, 'nagare.services.test4')
    assert len(repository) == 1

    ((service1_name, service1),) = repository.items()

    assert service1_name == 'service1'
    assert service1.get_entry_name() == 'service1'
    assert service1.test_value == 42
    assert service1.value1 == 20
    assert service1.value2 == '/tmp/test/a.txt'


def services_injection_to_lambdas_test():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    repository = services.Services(conf_filename, sys.stderr.write, {'root': '/tmp/test'}, 'nagare.services.test4')

    assert repository(lambda a, b, c: a + b + c, 10, 22, c=10) == 42
    assert repository(lambda a, b, service1_service, c: a + b + service1_service.value1 + c, 10, 2, c=10) == 42


def services_injection_to_functions_test():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    repository = services.Services(conf_filename, sys.stderr.write, {'root': '/tmp/test'}, 'nagare.services.test4')

    def f1(a, b, c):
        return a + b + c

    assert repository(f1, 10, 22, c=10) == 42

    def f2(a, b, service1_service, c):
        return a + b + service1_service.value1 + c

    assert repository(f2, 10, 2, c=10) == 42


def services_injection_to_object_test():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    repository = services.Services(conf_filename, sys.stderr.write, {'root': '/tmp/test'}, 'nagare.services.test4')

    class C1(object):
        def __init__(self, a, b, c):
            self.value = a + b + c

    assert repository(C1, 10, 22, c=10).value == 42

    class C2(object):
        def __init__(self, a, b, service1_service, c):
            self.value = a + b + service1_service.value1 + c

    assert repository(C2, 10, 2, c=10).value == 42


def services_injection_of_service_test():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    repository = services.Services(conf_filename, sys.stderr.write, {'root': '/tmp/test'}, 'nagare.services.test4')

    assert repository(lambda services_service: services_service) is repository
