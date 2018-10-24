# Encoding: utf-8

# --
# Copyright (c) 2008-2018 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os

import pytest
import pkg_resources

from nagare.services import exceptions, plugin, services


class DummyServices(services.Services):
    def iter_entry_points(self):
        egg_path = os.path.join(os.path.dirname(__file__), 'entry_points')
        return list(pkg_resources.WorkingSet([egg_path]).iter_entry_points(self.entry_points))


class DummyService1(plugin.Plugin):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}
    CATEGORY = 'TEST'

    def __init__(self, name, dist, value1, value2):
        self.name = name
        self.dist = dist
        self.value1 = value1
        self.value2 = value2


class DummyService2(DummyService1):
    LOAD_PRIORITY = 2000


class DummyService3(plugin.Plugin):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}
    LOAD_PRIORITY = 1

    def __init__(self, name, dist, value1, value2):
        self.name = name
        self.dist = dist
        self.value1 = value1
        self.value2 = value2


class DummyService4(plugin.Plugin):
    CONFIG_SPEC = {'value1': 'integer', 'value2': 'string'}
    LOAD_PRIORITY = 2

    def __init__(self, name, dist, value1, value2, service1_service):
        self.name = name
        self.dist = dist
        self.value1 = value1
        self.value2 = value2
        self.service1 = service1_service


class DummyService5(plugin.Plugin):
    LOAD_PRIORITY = 3


class DummyService6(plugin.Plugin):
    LOAD_PRIORITY = 4

    def __init__(self, *args, **kw):
        raise NotImplementedError()

# ---------------------------------------------------------------------------------------------------------------------


def test_load_service1():
    class Services(DummyServices):
        ENTRY_POINTS = 'nagare.services.test1'
        CONFIG_SECTION = 'my_services'

    services = Services()
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    services.load_plugins(conf_filename, root='/tmp/test')

    assert len(services) == 2

    (service1_name, service1), (service2_name, service2) = services.items()

    assert service1_name == 'service1'
    assert service1.name == 'service1'
    assert service1.dist.project_name == 'nagare-services'
    assert service1.value1 == 10
    assert service1.value2 == '/tmp/test/a.txt'

    assert service2_name == 'service2'
    assert service2.name == 'service2'
    assert service2.dist.project_name == 'nagare-services'
    assert service2.value1 == 20
    assert service2.value2 == '/tmp/test/b.txt'


def test_load_service2():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    services = DummyServices(conf_filename, 'my_services', 'nagare.services.test1', root='/tmp/test')

    assert len(services) == 2

    (service1_name, service1), (service2_name, service2) = services.items()

    assert service1_name == 'service1'
    assert service1.name == 'service1'
    assert service1.dist.project_name == 'nagare-services'
    assert service1.value1 == 10
    assert service1.value2 == '/tmp/test/a.txt'

    assert service2_name == 'service2'
    assert service2.name == 'service2'
    assert service2.dist.project_name == 'nagare-services'
    assert service2.value1 == 20
    assert service2.value2 == '/tmp/test/b.txt'


def test_injection_of_services():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    services = DummyServices(conf_filename, entry_points='nagare.services.test1', root='/tmp/test')

    assert services(lambda services_service: services_service) is services


def test_injection_of_service():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    services = DummyServices(conf_filename, 'services', entry_points='nagare.services.test2', root='/tmp/test')

    assert len(services) == 2

    (service1_name, service1), (service2_name, service2) = services.items()

    assert service1_name == 'service1'
    assert service1.name == 'service1'
    assert service1.dist.project_name == 'nagare-services'
    assert service1.value1 == 10
    assert service1.value2 == '/tmp/test/a.txt'

    assert service2_name == 'service2'
    assert service2.name == 'service2'
    assert service2.dist.project_name == 'nagare-services'
    assert service2.value1 == 20
    assert service2.value2 == '/tmp/test/b.txt'

    assert service2.service1 is service1


def test_activation1():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    services = DummyServices(conf_filename, 'activation1', 'nagare.services.test3', root='/tmp/test')

    assert list(services) == ['service1', 'service3']


def test_activation2():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    services = DummyServices(conf_filename, 'activation2', 'nagare.services.test4', activated_by_default=False)

    assert list(services) == ['service3']


def test_injection():
    conf_filename = os.path.join(os.path.dirname(__file__), 'services.cfg')
    services = DummyServices(conf_filename, 'activation1', 'nagare.services.test3', root='/tmp/test')

    r = services(lambda x, y, service3_service: (x, y, service3_service), 42, y='hello')

    assert r[0] == 42
    assert r[1] == 'hello'
    assert r[2] is services['service3']

    with pytest.raises(exceptions.MissingService, match='service2_service'):
        services(lambda x, y, service2_service: (x, y, service2_service), 42, y='hello')
