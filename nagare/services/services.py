# Encoding: utf-8

# --
# Copyright (c) 2008-2022 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Services registry"""
import inspect
import functools
try:
    from inspect import signature, Parameter
    POSITIONAL_OR_KEYWORD = Parameter.POSITIONAL_OR_KEYWORD
    KEYWORD_ONLY = Parameter.KEYWORD_ONLY
    EMPTY = Parameter.empty

    PY_VERSION = 3
except ImportError:
    from inspect import getargspec
    PY_VERSION = 2

from . import exceptions, plugins


class Services(plugins.Plugins):

    def __init__(self, activated_by_default=True, dependencies_postfix='service'):
        """Eager / lazy loading of the services

        In:
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- if defined, overloads the ``CONFIG_SECTION`` class attribute
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
          - ``activate_by_default`` -- default value if a service has no explicit ``activated`` configuration value
          - ``initial_config`` -- other configuration parameters not read from the configuration file
        """
        self.postfix = '_' + dependencies_postfix
        super(Services, self).__init__(activated_by_default)

    def _load_plugin(self, name_, dist, service_cls, activated=None, **config):
        """Load and activate a service

        In:
          - ``service`` -- the service

        Returns:
          - the service
        """
        service_cls.PLUGIN_CATEGORY = self.ENTRY_POINTS
        return self(service_cls, name_, dist, **config)

    def load_services(self, name, config=None, global_config=None, validate=False, entry_points=None):
        return self.load_plugins(name, config, global_config, validate, entry_points)

    def get_service(self, service_path):
        return functools.reduce(lambda d, name: d[name], service_path, self)

    def find_services(self, criterias=lambda service: True):
        services = []
        for service in self.values():
            children = service.find_services(criterias) if hasattr(service, 'find_services') else []
            if criterias(service) or children:
                services.append((service, children))

        return services

    def get_dependency(self, name, is_mandatory=True):
        """Retrieve a dependency from this registry

        Args:
          name: name of the dependency to retrieve (with the postfix)
          is_mandatory: the dependency must be found

        Raises:
          exceptions.MissingDependency: dependency not found and mandatory

        Return:
          None, _: optional dependency not found
          str, object: dependency found
        """
        name2 = name[:-len(self.postfix)]  # strip the postfix

        if name2 == 'services':
            dependency = self
        else:
            if name2 not in self:
                if is_mandatory:
                    raise exceptions.MissingService(name)
                else:
                    name = None

            dependency = self.get(name2)

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

        if PY_VERSION == 3:
            # Retrieve the dependencies to inject
            dependencies = dict(
                self.get_dependency(p.name, p.default is EMPTY)
                for p in signature(f2).parameters.values()
                if ((p.kind == POSITIONAL_OR_KEYWORD) or (p.kind == KEYWORD_ONLY)) and p.name.endswith(self.postfix)
            )
        else:
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
