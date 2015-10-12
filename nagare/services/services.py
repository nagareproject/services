# Encoding: utf-8

#=-
# (C)opyright Net-ng 2012-2015
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
#=-

"""Services registry"""

import inspect
import logging

from . import plugins


logger = logging.getLogger(__name__)


class ServiceMissing(Exception):
    pass


class Services(plugins.Plugins):
    ENTRY_POINTS = 'services'  # Default section of the service entry points
    CONFIG_SECTION = 'services'  # Default configuration section of the services

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

    def check_services_injection(self, f):
        """Discover and check the services to inject from the signature of ``f``

        In:
          - ``f`` -- a callable

        Return:
          - a dict {service name: service} of the services to inject
        """
        # Get the signature of ``f`` or the signature of its ``__init__`` method if ``f`` is a class
        args = inspect.getargspec(f.__init__ if isinstance(f, type) else f)

        # Services to inject are postfixed by ``__service`` in the signature
        services = dict(zip(reversed(args.args), reversed(args.defaults or ())))
        services.update({name + '_service': service for name, service in self.items()})
        services['services_service'] = self

        try:
            return {name: services[name] for name in args.args if name.endswith('_service')}
        except KeyError as e:
            raise ServiceMissing(e.args[0][:-8])

    def __call__(self, f, *args, **kw):
        """Call ``f`` with services injection

        In:
          - ``f`` -- a callable
          - ``args`` -- arguments to pass to ``f``
          - ``kw`` -- keywords to pass to ``f``
        """
        services = self.check_services_injection(f)
        services.update(kw)

        return f(*args, **services)
