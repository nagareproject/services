# Encoding: utf-8

# --
# Copyright (c) 2008-2020 Net-ng.
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
    from inspect import getfullargspec as getargspec
except ImportError:
    from inspect import getargspec

from . import exceptions, plugins


class Services(plugins.Plugins):
    ENTRY_POINTS = 'services'  # Default section of the service entry points
    CONFIG_SECTION = 'services'  # Default configuration section of the services

    def __init__(
            self,
            config=None, config_section=None,
            entry_points=None,
            activated_by_default=True,
            dependencies_postfix='service',
            **initial_config
    ):
        """Eager / lazy loading of the services

        In:
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- if defined, overloads the ``CONFIG_SECTION`` class attribute
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
          - ``activate_by_default`` -- default value if a service has no explicit ``activated`` configuration value
          - ``initial_config`` -- other configuration parameters not read from the configuration file
        """
        self.postfix = '_' + dependencies_postfix
        super(Services, self).__init__(config, config_section, entry_points, activated_by_default, **initial_config)

    def _load_plugin(self, name, dist, service_cls, initial_config, config, *args, **kw):
        """Load and activate a service

        In:
          - ``service`` -- the service

        Returns:
          - the service
        """
        if hasattr(service_cls, 'WITH_INITIAL_CONFIG'):
            args = (initial_config,) + args

        config = dict(config, **kw)

        service_cls.PLUGIN_CATEGORY = 'nagare.services'
        service = self(service_cls, name, dist, *args, **config)

        return service

    def report(self, title='Services', activated_columns=None, criterias=lambda _: True):
        super(Services, self).report(title, activated_columns, criterias)

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
