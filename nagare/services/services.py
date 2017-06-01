# Encoding: utf-8

# --
# (C)opyright Net-ng 2012-2017
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Services registry"""

from . import dependencies, plugins


class MissingService(Exception):
    pass


class Services(dependencies.Dependencies, plugins.Plugins):
    ENTRY_POINTS = 'services'  # Default section of the service entry points
    CONFIG_SECTION = 'services'  # Default configuration section of the services

    activated = True

    def __init__(
            self,
            config=None, config_section=None,
            entry_points=None,
            config_filename=None,
            activate_by_default=True,
            **initial_conf
    ):
        """Eager / lazy loading of the services

        In:
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- if defined, overloads the ``CONFIG_SECTION`` class attribute
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
          - ``config_filename`` -- path of the configuration file
          - ``activate_by_default`` -- default value if a service has no explicit ``activated`` configuration value 
          - ``initial_config`` -- other configuration parameters not read from the configuration file
        """
        self.activate_by_default = activate_by_default

        dependencies.Dependencies.__init__(self, 'service')
        plugins.Plugins.__init__(self, config, config_section, entry_points, config_filename, **initial_conf)

    def get_plugin_spec(self, service):
        """Get the Service configuration specification

        In:
          - ``service`` -- the service

        Returns:
          - the service configuration specification
        """
        spec = super(Services, self).get_plugin_spec(service)

        return dict(spec, activated='boolean(default="%s")' % self.activate_by_default)

    def get_dependency(self, name, **kw):
        """Retrieve a service from this registry

        In:
          - ``name`` -- name of the service to inject (with the ``_service`` postfix)
          - ``other_dependencies`` -- optional other services to lookup

        Returns:
          - the service found
        """
        try:
            # Also inject the ``services_service`` dependency
            dependency = super(Services, self).get_dependency(name, services=self, **kw)
        except dependencies.MissingDependency as e:
            raise MissingService(e.args[0])

        if not dependency.activated:
            raise MissingService(name)

        return dependency

    def _load_plugin(self, service, *args, **kw):
        """Load and activate a service

        In:
          - ``service`` -- the service

        Returns:
          - the service
        """
        return self(service.load_plugin, *args, **kw)
