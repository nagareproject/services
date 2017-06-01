# Encoding: utf-8

# --
# (C)opyright Net-ng 2012-2017
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Base classes for the loadable services"""

from . import plugin


class ClassService(plugin.ClassPlugin):
    """The service is a class"""

    @classmethod
    def load_plugin(cls, service_config, config, config_section, entry_points, config_filename, **initial_config):
        """Create and activate the service with its configuration

        In:
          - ``service_config`` -- the ``ConfigObj`` section for this service
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- parent section of the service in the application configuration file
          - ``entry_points`` --  section of the entry point for this service
          - ``config_filename`` -- path of the configuration file
          - ``initial_config`` -- other configuration parameters not read from the configuration file

        Return:
          - the activated service
        """
        activated = service_config.pop('activated')
        cls.activate_plugin(activated)
        cls.set_config(service_config)

        return cls  # By default the service is the Python class loaded from the entry point

    @classmethod
    def create_plugin(cls, services_service=lambda f, **config: f(**config), **config):
        """Instanciate an object from this service
        """
        return services_service(cls, **dict(cls.get_config(), **config))

    create_service = create_plugin


class SingletonService(plugin.SingletonPlugin):
    """The service is an object"""

    @classmethod
    def load_plugin(
            cls,
            service_config,
            config, config_section, entry_points, config_filename,
            services_service=lambda f, **config: f(**config),
            **initial_config
    ):
        """Create and activate the service with its configuration

        In:
          - ``service_config`` -- the ``ConfigObj`` section for this service
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- parent section of the service in the application configuration file
          - ``entry_points`` --  section of the entry point for this service
          - ``config_filename`` -- path of the configuration file
          - ``initial_config`` -- other configuration parameters not read from the configuration file

        Return:
          - the activated service
        """
        activated = service_config.pop('activated')
        service = services_service(cls, **service_config)
        service.activate_plugin(activated)

        return service


Service = SingletonService


class ServicesService(plugin.PluginsPlugin):
    """The service is itself a services registry"""

    @classmethod
    def load_plugin(
            cls,
            service_config,
            config, config_section, entry_points, config_filename,
            services_service=lambda f, **config: f(**config),
            **initial_config
    ):
        """Create and activate the service with its configuration

        In:
          - ``service_config`` -- the ``ConfigObj`` section for this service
          - ``config`` -- ``ConfigObj`` configuration object
          - ``config_section`` -- parent section of the service in the application configuration file
          - ``entry_points`` --  section of the entry point for this service
          - ``config_filename`` -- path of the configuration file
          - ``initial_config`` -- other configuration parameters not read from the configuration file

        Return:
          - the activated service
        """
        activated = service_config.pop('activated')
        service = services_service(cls, config, config_filename, initial_config, **service_config)
        service.activate_plugin(activated)

        return service
