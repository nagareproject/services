# Encoding: utf-8

# --
# (C)opyright Net-ng 2012-2017
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Dependencies registration and injection"""

import inspect
import functools


class MissingDependency(Exception):
    pass


class Dependencies(dict):
    """Dependencies registry"""

    def __init__(self, dependencies_postfix='inject', **dependencies):
        """Initialization
        
        Dependencies to inject are postfixed by ``'_' + dependencies_postfix``
        in the signature of the functions to call
        """
        super(Dependencies, self).__init__(**dependencies)

        self.postfix = '_' + dependencies_postfix

    def get_dependency(self, name, **other_dependencies):
        """Retrieve a dependency from this registry
        
        In:
          - ``name`` -- name of the dependency to inject (with the postfix)
          - ``other_dependencies`` -- optional other dependencies to lookup
          
        Returns:
          - the dependency found
        """
        name = name[:-len(self.postfix)]  # strip the postfix

        return self.get(name) or other_dependencies[name]

    def __call__(self, f, *args, **kw):
        """Call ``f`` with dependencies injection

        In:
          - ``f`` -- a callable
          - ``args`` -- arguments to pass to ``f``
          - ``kw`` -- keywords to pass to ``f``
          
        Return:
          - value returns by ``f``
        """
        # Get the signature of ``f`` or the signature of its ``__init__`` method if ``f`` is a class
        f2 = f
        if inspect.isclass(f):
            f2 = f.__init__ if inspect.ismethod(f.__init__) else lambda: None

        names = inspect.getargspec(f2).args

        try:
            dependencies = {name: self.get_dependency(name) for name in names if name.endswith(self.postfix)}
        except KeyError as e:
            raise MissingDependency(e.args[0])

        dependencies.update(kw)

        return f(*args, **dependencies)

    def inject(self, f):
        """Function decorator
        
        Call ``f`` with dependencies injection

        In:
          - ``f`` -- a callable

        Return:
          - value returns by ``f``
        """
        return functools.update_wrapper(lambda *args, **kw: self(f, *args, **kw), f)
