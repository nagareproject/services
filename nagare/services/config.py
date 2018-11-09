# Encoding: utf-8

# --
# Copyright (c) 2008-2018 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Helper to validate a configuration"""

import configobj
from validate import Validator

from . import exceptions


class Match(dict):

    def group(self, name=None):
        return self.get(name, [self['escaped'], self['named'], self['braced']])


class TemplateInterpolation(configobj.TemplateInterpolation):

    def __init__(self, section):
        self.key = None
        super(TemplateInterpolation, self).__init__(section)

    def interpolate(self, key, value):
        self.key = key

        return super(TemplateInterpolation, self).interpolate(key, value)

    def _parse_match(self, match):
        groups = match.groupdict()

        braced = groups['braced']
        if braced and (':' in braced):
            groups['braced'], default = braced.split(':', 1)
        else:
            default = None

        try:
            r = super(TemplateInterpolation, self)._parse_match(Match(**groups))
        except configobj.MissingInterpolationOption:
            if default is None:
                raise

            r = self.key + '#', default, self.section

        return r

    def _fetch(self, key):
        if '.' not in key:
            return super(TemplateInterpolation, self)._fetch(key)

        root_section = self.section
        while root_section.parent is not root_section:
            root_section = root_section.parent

        for key in key.split('.'):
            section, root_section = root_section, root_section[key]

        return root_section, section


configobj.interpolation_engines['templatewithdefaults'] = TemplateInterpolation


def _validate(config, filename=None):
    """Validate a ``ConfigObj`` configuration

    The configuration object must have an associated ``configspec``

    Args:
      config: ``ConfigObj`` configuration to validate
      filename: optional path to the configuration file

    Yields:
      error messages
    """
    functions = {
        name: (
            lambda f:
                lambda value, *args, **kw: f(
                    value if isinstance(value, (list, tuple)) else [value],
                    *args, **kw
                )
        )(f)
        for name, f in Validator().functions.items()
        if (name != 'force_list') and name.endswith('_list')
    }

    validator = Validator(functions)

    errors = configobj.flatten_errors(config, config.validate(validator, preserve_errors=True))

    for sections, name, error in errors:
        prefix = ('file "%s", ' % filename) if filename else ''

        yield prefix + 'section "[%s]", parameter "%s": %s' % (
            ' / '.join(sections),
            name, error
        )


def validate(config, filename=None):
    """Validate a ``ConfigObj`` configuration

    The configuration object must have an associated ``configspec``

    Args:
      config: ``ConfigObj`` configuration to validate
      filename: optional path to the configuration file

    Raises:
      BadConfiguration: configuration is not valid
    """
    errors = list(_validate(config, filename))
    if errors:
        raise exceptions.BadConfiguration('\n'.join(errors))
