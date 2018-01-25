# Encoding: utf-8

# --
# Copyright (c) 2008-2018 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Services registry"""

from . import exceptions, dependencies, plugins


class Services(dependencies.Dependencies, plugins.Plugins):
    ENTRY_POINTS = 'services'  # Default section of the service entry points
    CONFIG_SECTION = 'services'  # Default configuration section of the services

    def __init__(
            self,
            config=None, config_section=None,
            entry_points=None,
            activated_by_default=True,
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
        dependencies.Dependencies.__init__(self, 'service')
        plugins.Plugins.__init__(self, config, config_section, entry_points, activated_by_default, **initial_config)

    def get_dependency(self, name, has_default_value, **kw):
        """Retrieve a service from this registry

        In:
          - ``name`` -- name of the service to inject (with the ``_service`` postfix)
          - ``other_dependencies`` -- optional other services to lookup

        Returns:
          - the service found
        """
        try:
            # Also inject the ``services_service`` dependency
            name, dependency = super(Services, self).get_dependency(name, has_default_value, services=self, **kw)
        except exceptions.MissingDependency as e:
            raise exceptions.MissingService(e.args[0])

        return name, dependency

    def _load_plugin(self, name, dist, service, config, *args, **kw):
        """Load and activate a service

        In:
          - ``service`` -- the service

        Returns:
          - the service
        """
        return self(service, name, dist, *args, **dict(config, **kw))

    def display(self, title='Services', criterias=lambda _: True):
        super(Services, self).display(title, criterias)
