# Encoding: utf-8

# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Helper to validate a configuration"""

from functools import partial

import configobj
from validate import Validator as ConfigobjValidator

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


class Validator(ConfigobjValidator):

    @staticmethod
    def new_validate(f, convert_to_list, value, *args, **kw):
        if convert_to_list and not isinstance(value, (list, tuple)):
            value = [value]

        kw.pop('help', None)

        return f(value, *args, **kw)

    def create_validation(self, name, f):
        convert_to_list = (name != 'force_list') and name.endswith('list')
        return partial(self.new_validate, f, convert_to_list)

    def __init__(self, functions=None):
        super(Validator, self).__init__(functions)
        self.functions = {name: self.create_validation(name, f) for name, f in self.functions.items()}


def _validate(config, filename, validator):
    """Validate a ``ConfigObj`` configuration

    The configuration object must have an associated ``configspec``

    Args:
      config: ``ConfigObj`` configuration to validate
      filename: optional path to the configuration file

    Yields:
      error messages
    """
    errors = configobj.flatten_errors(config, config.validate(validator, preserve_errors=True))

    for sections, name, error in errors:
        prefix = ('file "%s", ' % filename) if filename else ''

        yield prefix + 'section "[%s]", parameter "%s": %s' % (
            ' / '.join(sections),
            name, error
        )


def validate(config, filename=None, validator=None):
    """Validate a ``ConfigObj`` configuration

    The configuration object must have an associated ``configspec``

    Args:
      config: ``ConfigObj`` configuration to validate
      filename: optional path to the configuration file

    Raises:
      BadConfiguration: configuration is not valid
    """
    errors = list(_validate(config, filename, validator or Validator()))
    if errors:
        raise exceptions.BadConfiguration('\n'.join(errors))
