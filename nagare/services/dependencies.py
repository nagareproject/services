# Encoding: utf-8

# =-
# (C)opyright Net-ng 2012-2017
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
# =-

"""Dependencies registry and injection"""

import inspect


class MissingDependency(Exception):
    pass


class Dependencies(dict):
    def __init__(self, dependencies_postfix='inject', **kw):
        """Initialization
        
        Dependencies to inject are postfixed by ``'_' + dependencies_postfix``
        in the signature of the functions to call
        """
        super(Dependencies, self).__init__(**kw)

        self.postfix = '_' + dependencies_postfix

    def get_dependency(self, name, **kw):
        name = name[:-len(self.postfix)]

        return self.get(name) or kw[name]

    def __call__(self, f, *args, **kw):
        """Call ``f`` with dependencies injection

        In:
          - ``f`` -- a callable
          - ``args`` -- arguments to pass to ``f``
          - ``kw`` -- keywords to pass to ``f``
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
         
        """
        return lambda *args, **kw: self(f, *args, **kw)
