# Encoding: utf-8

# --
# Copyright (c) 2008-2020 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import pytest

from nagare.services.dependencies import Dependencies
from nagare.services.exceptions import MissingDependency


def test_dependencies_injection_to_lambdas():
    dependencies = Dependencies(c=42)

    assert dependencies(lambda a, b, c: a + b + c, 10, 22, c=10) == 42
    assert dependencies(lambda a, b, c_inject: a + b + c_inject, 10, 22) == 74
    assert dependencies(lambda a, b, c_inject, d: a + b + c_inject + d, 10, 22, d=10) == 84
    assert dependencies(lambda a, b, c_inject, d: a + b + c_inject + d, 10, 22, c_inject=2, d=10) == 44


def test_dependencies_injection_to_functions():
    dependencies = Dependencies(c=42, other=10)

    def f1(a, b, c):
        return a + b + c

    assert dependencies(f1, 10, 22, c=10) == 42

    def f2(a, b, c_inject):
        return a + b + c_inject

    assert dependencies(f2, 10, 22) == 74

    def f3(a, b, c_inject, d):
        return a + b + c_inject + d

    assert dependencies(f3, 10, 22, d=10) == 84

    assert dependencies(f3, 10, 22, c_inject=2, d=10) == 44


def test_dependencies_injection_with_decorator():
    dependencies1 = Dependencies(c=42, other=10)
    dependencies2 = Dependencies(c=43)

    @dependencies1.inject
    def f1(a, b, c):
        return a + b + c

    assert f1(10, 22, c=10) == 42

    @dependencies1.inject
    def f2(a, b, c_inject):
        return a + b + c_inject

    assert f2(10, 22) == 74

    @dependencies2.inject
    def f3(a, b, c_inject, d):
        return a + b + c_inject + d

    assert f3(10, 22, d=10) == 85

    assert f3(10, 22, c_inject=2, d=10) == 44


def test_dependencies_injection_to_object():
    dependencies = Dependencies(c=42)

    class C1(object):
        def __init__(self, a, b, c):
            self.value = a + b + c

    assert dependencies(C1, 10, 22, c=10).value == 42

    class C2(object):
        def __init__(self, a, b, c_inject):
            self.value = a + b + c_inject

    assert dependencies(C2, 10, 22).value == 74

    class C3(object):
        def __init__(self, a, b, c_inject, d):
            self.value = a + b + c_inject + d

    assert dependencies(C3, 10, 22, d=10).value == 84

    assert dependencies(C3, 10, 22, c_inject=2, d=10).value == 44


def test_dependencies_injection_with_postfix():
    dependencies = Dependencies('service', c=42)

    assert dependencies(lambda a, b, c: a + b + c, 10, 22, c=10) == 42
    assert dependencies(lambda a, b, c_service: a + b + c_service, 10, 22) == 74
    assert dependencies(lambda a, b, c_service, d: a + b + c_service + d, 10, 22, d=10) == 84
    assert dependencies(lambda a, b, c_service, d: a + b + c_service + d, 10, 22, c_service=2, d=10) == 44


def test_dependencies_injection_errors():
    dependencies = Dependencies(other=10)

    with pytest.raises(MissingDependency, match='^c_inject$'):
        dependencies(lambda a, b, c_inject: a + b + c_inject, 10, 22)

    assert dependencies(lambda a, b, c_service, d: a + b + c_service + d, 10, 22, c_service=2, d=10) == 44


def test_dependencies_injection_with_default_values():
    dependencies = Dependencies(c=42)

    assert dependencies(lambda a, d_inject=42: a + d_inject, 10) == 52
    assert dependencies(lambda a, c_inject=10, d_inject=42: a + c_inject + d_inject, 10) == 94
