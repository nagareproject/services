# Encoding: utf-8
# --
# Copyright (c) 2008-2022 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import sys
import warnings

warnings.filterwarnings('ignore', module='_distutils')
try:
    from pip._internal.metadata.pkg_resources import Distribution  # noqa: E402
except ImportError:
    def Distribution(dist):
        dist.editable_project_location = None
        return dist


class Reporter(object):

    def __init__(self, columns=()):
        self.columns = columns

    def report(self, activated_columns, to_report, sorted, display=None, indent=0):
        display = display or (lambda m: sys.stdout.write(m + '\n'))
        if not to_report:
            display('  <empty>')
            return

        columns = [list(column) for column in self.columns if column[0].lower() in activated_columns]

        for column in columns:
            label, extract, left = column
            padding = max(len(extract(*args)) for args in to_report)
            column.append(max((padding, len(label))))

        labels = [(label.ljust if left else label.rjust)(padding) for label, extract, left, padding in columns]  # noqa: F812
        display((' ' * indent) + ' '.join(labels))
        labels = ['-' * padding for label, extract, left, padding in columns]
        display((' ' * indent) + ' '.join(labels))

        rows = []
        for args in to_report:
            fields = []
            for label, extract, left, padding in columns:
                field = extract(*args)
                field = (field.ljust if left else field.rjust)(padding)
                fields.append(field)

            rows.append(fields)

        if sorted:
            rows.sort()

        for fields in rows:
            display((' ' * indent) + ' '.join(fields))


class PackagesReporter(Reporter):
    COLUMNS = (
        ('Package', lambda dist, *args: dist.project_name, True),
        ('Version', lambda dist, *args: dist.version, True),
        ('Location', lambda dist, *args: Distribution(dist).editable_project_location or dist.location, True)
    )

    def __init__(self, columns=None):
        super(PackagesReporter, self).__init__(columns or self.COLUMNS)


class PluginsReporter(PackagesReporter):

    def __init__(self):
        super(PluginsReporter, self).__init__((
            ('Name', lambda dist, level, name, plugin, activated: ' ' * (4 * level) + name, True),
            ('X', lambda dist, level, name, plugin, activated: '-' if activated is None else '+', True),
            ('Order', lambda dist, level, name, plugin, activated: str(plugin.LOAD_PRIORITY), False),
        ) + PackagesReporter.COLUMNS + (
            ('Module', lambda dist, level, name, plugin, activated: self.extract_module(plugin), True),
            (
                'Description',
                lambda dist, level, name, plugin, activated: self.extract_description(plugin, activated),
                True
            )
        ))

    @staticmethod
    def extract_module(plugin):
        module = plugin.__module__ + '.'
        if module.startswith('nagare.'):
            module = '~' + module[7:]

        return module + plugin.__name__

    @staticmethod
    def extract_description(plugin, activated_plugin):
        return (plugin if activated_plugin is None else activated_plugin).DESC
