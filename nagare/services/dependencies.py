# Encoding: utf-8

# --
# Copyright (c) 2008-2018 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Dependencies registration and injection"""

import inspect
try:
    from inspect import getfullargspec as getargspec
except ImportError:
    from inspect import getargspec
import functools

from . import exceptions


class Dependencies(dict):
    """Dependencies registry"""

    def __init__(self, dependencies_postfix='inject', **dependencies):
        """Initialization

        Dependencies to inject are postfixed by ``'_' + dependencies_postfix``
        in the signature of the functions to call

        Args:
          dependencies_postfix: postfix of the parameters to inject
          dependencies: initial dependencies
        """
        super(Dependencies, self).__init__(**dependencies)

        self.postfix = '_' + dependencies_postfix

    def get_dependency(self, name, is_mandatory, **other_dependencies):
        """Retrieve a dependency from this registry

        Args:
          name: name of the dependency to retrieve (with the postfix)
          is_mandatory: the dependency must be found
          **other_dependencies: other registry to lookup into

        Raises:
          exceptions.MissingDependency: dependency not found and mandatory

        Return:
          None, _: optional dependency not found
          str, object: dependency found
        """
        name2 = name[:-len(self.postfix)]  # strip the postfix
        dependency = self.get(name2, other_dependencies.get(name2))

        if dependency is None:
            if is_mandatory:
                raise exceptions.MissingDependency(name)

            name = None

        return name, dependency

    def __call__(self, f, *args, **kw):
        """Call ``f`` with dependencies injection

        Args:
          f: a callable
          *args: arguments to pass to ``f``
          **kw: keywords to pass to ``f``

        Return:
          value returns by ``f``
        """
        # Get the signature of ``f`` or the signature of its ``__init__`` method if ``f`` is a class
        f2 = f
        if inspect.isclass(f):
            f2 = f.__init__ if inspect.isroutine(f.__init__) else lambda: None

        args_spec = getargspec(f2)

        nb_default_values = len(args_spec.defaults or ())
        names = args_spec.args

        # Retrieve the dependencies to inject
        dependencies = dict(
            self.get_dependency(name, i >= nb_default_values)
            for i, name in enumerate(reversed(names))
            if name.endswith(self.postfix)
        )

        dependencies.pop(None, None)
        dependencies.update(kw)

        return f(*args, **dependencies)

    def inject(self, f):
        """Function decorator

        Call ``f`` with dependencies injection

        Args:
          f: a callable

        Return:
          the decorated ``f``
        """
        return functools.update_wrapper(lambda *args, **kw: self(f, *args, **kw), f)
