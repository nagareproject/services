# Encoding: utf-8

#=-
# (C)opyright Net-ng 2012-2015
#
# This is a Net-ng source code.
# Any reproduction modification or use without prior written
# approval from Net-ng is strictly forbidden.
#=-

"""Helper to validate a configuration"""

import configobj
from validate import Validator


def _validate(filename, config):
    """Validate a ``ConfigObj`` object

    In:
      - ``filename`` -- the path to the configuration file
      - ``config`` -- the ``ConfigObj`` object, created from the configuration file

    Return:
      - yield the error messages
    """
    errors = configobj.flatten_errors(config, config.validate(Validator(), preserve_errors=True))

    for sections, name, error in errors:
        yield 'file "%s", section "[%s]", parameter "%s": %s' % (filename, ' / '.join(sections), name, error)


def validate(filename, config, error):
    """Validate a ``ConfigObj`` object

    In:
      - ``filename`` -- the path to the configuration file
      - ``config`` -- the ``ConfigObj`` object, created from the configuration file
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - is the configuration valid?
    """
    errors = list(_validate(filename, config))
    if errors:
        error('\n'.join(errors))
        return False

    return True
