# Encoding: utf-8

# --
# (C)opyright Net-ng 2012-2017
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import unittest

from nagare.services.dependencies import MissingDependency, Dependencies


class TestDependenciesInjection(unittest.TestCase):
    def dependencies_injection_to_lambdas_test(self):
        dependencies = Dependencies(c=42)

        self.assertEqual(dependencies(lambda a, b, c: a + b + c, 10, 22, c=10), 42)
        self.assertEqual(dependencies(lambda a, b, c_inject: a + b + c_inject, 10, 22), 74)
        self.assertEqual(dependencies(lambda a, b, c_inject, d: a + b + c_inject + d, 10, 22, d=10), 84)
        self.assertEqual(dependencies(lambda a, b, c_inject, d: a + b + c_inject + d, 10, 22, c_inject=2, d=10), 44)

    def dependencies_injection_to_functions_test(self):
        dependencies = Dependencies(c=42, other=10)

        def f1(a, b, c):
            return a + b + c

        self.assertEqual(dependencies(f1, 10, 22, c=10), 42)

        def f2(a, b, c_inject):
            return a + b + c_inject

        self.assertEqual(dependencies(f2, 10, 22), 74)

        def f3(a, b, c_inject, d):
            return a + b + c_inject + d

        self.assertEqual(dependencies(f3, 10, 22, d=10), 84)

        self.assertEqual(dependencies(f3, 10, 22, c_inject=2, d=10), 44)

    def dependencies_injection_with_decorator_test(self):
        dependencies1 = Dependencies(c=42, other=10)
        dependencies2 = Dependencies(c=43)

        @dependencies1.inject
        def f1(a, b, c):
            return a + b + c

        self.assertEqual(f1(10, 22, c=10), 42)

        @dependencies1.inject
        def f2(a, b, c_inject):
            return a + b + c_inject

        self.assertEqual(f2(10, 22), 74)

        @dependencies2.inject
        def f3(a, b, c_inject, d):
            return a + b + c_inject + d

        self.assertEqual(f3(10, 22, d=10), 85)

        self.assertEqual(f3(10, 22, c_inject=2, d=10), 44)

    def dependencies_injection_to_object_test(self):
        dependencies = Dependencies(c=42)

        class C1(object):
            def __init__(self, a, b, c):
                self.value = a + b + c

        self.assertEqual(dependencies(C1, 10, 22, c=10).value, 42)

        class C2(object):
            def __init__(self, a, b, c_inject):
                self.value = a + b + c_inject

        self.assertEqual(dependencies(C2, 10, 22).value, 74)

        class C3(object):
            def __init__(self, a, b, c_inject, d):
                self.value = a + b + c_inject + d

        self.assertEqual(dependencies(C3, 10, 22, d=10).value, 84)

        self.assertEqual(dependencies(C3, 10, 22, c_inject=2, d=10).value, 44)

    def dependencies_injection_with_postfix_test(self):
        dependencies = Dependencies('service', c=42)

        self.assertEqual(dependencies(lambda a, b, c: a + b + c, 10, 22, c=10), 42)
        self.assertEqual(dependencies(lambda a, b, c_service: a + b + c_service, 10, 22), 74)
        self.assertEqual(dependencies(lambda a, b, c_service, d: a + b + c_service + d, 10, 22, d=10), 84)
        self.assertEqual(dependencies(lambda a, b, c_service, d: a + b + c_service + d, 10, 22, c_service=2, d=10), 44)

    def dependencies_injection_errors_test(self):
        dependencies = Dependencies(other=10)

        self.assertRaisesRegexp(MissingDependency, "^c$", dependencies, lambda a, b, c_inject: a + b + c_inject, 10, 22)
        self.assertEqual(dependencies(lambda a, b, c_service, d: a + b + c_service + d, 10, 22, c_service=2, d=10), 44)
