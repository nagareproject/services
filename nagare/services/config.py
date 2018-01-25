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


def _validate(config, filename=None):
    """Validate a ``ConfigObj`` configuration

    The configuration object must have an associated ``configspec``

    Args:
      config: ``ConfigObj`` configuration to validate
      filename: optional path to the configuration file

    Yields:
      error messages
    """
    errors = configobj.flatten_errors(config, config.validate(Validator(), preserve_errors=True))

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
