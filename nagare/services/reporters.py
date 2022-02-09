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


class Reporter(object):

    def __init__(self, columns=()):
        self.columns = columns

    def report(self, activated_columns, to_report, sorted, display=None):
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
        display('  ' + ' '.join(labels))
        labels = ['-' * padding for label, extract, left, padding in columns]
        display('  ' + ' '.join(labels))

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
            display('  ' + ' '.join(fields))


class PackagesReporter(Reporter):
    COLUMNS = (
        ('Package', lambda dist, *args: dist.project_name, True),
        ('Version', lambda dist, *args: dist.version, True),
        ('Location', lambda dist, *args: dist.location, True)
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
