# Encoding: utf-8

# =-
# (C)opyright Net-ng 2012-2017
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
# =-

"""Helper to validate a configuration"""

import configobj
from validate import Validator


class BadConfiguration(Exception):
    pass


def _validate(config, filename=None):
    """Validate a ``ConfigObj`` object

    In:
      - ``config`` -- the ``ConfigObj`` object, created from the configuration file
      - ``filename`` -- the path to the configuration file

    Return:
      - yield the error messages
    """
    errors = configobj.flatten_errors(config, config.validate(Validator(), preserve_errors=True))

    for sections, name, error in errors:
        yield 'file "%s", section "[%s]", parameter "%s": %s' % (
            filename or '<undefined>',
            ' / '.join(sections),
            name, error
        )


def validate(config, filename=None):
    """Validate a ``ConfigObj`` object

    In:
      - ``config`` -- the ``ConfigObj`` object, created from the configuration file
      - ``filename`` -- the path to the configuration file
    """
    errors = list(_validate(config, filename))
    if errors:
        raise BadConfiguration('\n'.join(errors))
