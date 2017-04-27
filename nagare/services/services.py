# Encoding: utf-8

# =-
# (C)opyright Net-ng 2012-2017
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
# =-

"""Services registry"""

from . import dependencies, plugins


class MissingService(Exception):
    pass


class Services(dependencies.Dependencies, plugins.Plugins):
    ENTRY_POINTS = 'services'  # Default section of the service entry points
    CONFIG_SECTION = 'services'  # Default configuration section of the services

    def __init__(self, conf_filename=None, error=None, entry_points=None, **initial_conf):
        """Eager / lazy loading the services

        In:
          - ``conf_filename`` -- the path to the configuration file
          - ``error`` -- the function to call in case of configuration errors
          - ``entry_points`` -- if defined, overloads the ``ENTRY_POINT`` class attribute
          - ``initial_conf`` -- other configuration parameters not read from the configuration file          
        """
        dependencies.Dependencies.__init__(self, 'service')
        plugins.Plugins.__init__(self, conf_filename, error, entry_points, **initial_conf)

    def get_dependency(self, name, **kw):
        try:
            return super(Services, self).get_dependency(name, services=self, **kw)
        except dependencies.MissingDependency as e:
            raise MissingService(e.args[0])

    def activate(self, plugin, conf_filename, conf, error):
        """Activate the service with its configuration

        In:
          - ``plugin`` -- the plugin to activate (the class loaded from the entry point)
          - ``conf_filename`` -- the path to the configuration file
          - ``conf`` -- the ``configobj`` configuration
          - ``error`` -- the function to call in case of configuration errors

        Return:
          - the activated service
        """
        factory = super(Services, self).activate(plugin, conf_filename, conf, error)

        # Instanciate a singleton service (with services injection)
        return self(factory, conf_filename, error, **conf)
