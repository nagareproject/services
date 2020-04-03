# Encoding: utf-8
# --
# Copyright (c) 2008-2020 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import sys


class PackagesReporter(object):

    def __init__(self):
        self.columns = [
            ['Package', lambda dist, *args: dist.project_name, True],
            ['Version', lambda dist, *args: dist.version, True],
            ['Location', lambda dist, *args: dist.location, True]
        ]

    def report(self, activated_columns, packages, display=None):
        display = display or (lambda m: sys.stdout.write(m + '\n'))
        if not packages:
            display('  <empty>')
            return

        columns = [column for column in self.columns if column[0].lower() in activated_columns]

        for column in columns:
            label, extract, left = column
            padding = max(len(extract(*args)) for args in packages)
            column.append(max((padding, len(label))))

        labels = [(label.ljust if left else label.rjust)(padding) for label, extract, left, padding in columns]  # noqa: F812
        display('  ' + ' '.join(labels))
        labels = ['-' * padding for label, extract, left, padding in columns]
        display('  ' + ' '.join(labels))

        rows = []
        for args in packages:
            fields = []
            for label, extract, left, padding in columns:
                field = extract(*args)
                field = (field.ljust if left else field.rjust)(padding)
                fields.append(field)

            rows.append(fields)

        for fields in sorted(rows):
            display('  ' + ' '.join(fields))


class PluginsReporter(PackagesReporter):

    def __init__(self):
        super(PluginsReporter, self).__init__()

        self.columns = [
            ['Order', lambda dist, name, plugin, activated, *args: str(plugin.LOAD_PRIORITY), False],
            ['X', lambda dist, name, plugin, activated, *args: '-' if activated is None else '+', True],
            ['Name', lambda dist, name, *args: name, True]
        ] + self.columns + [
            ['Module', lambda dist, name, plugin, activated, *args: self.extract_module(plugin), True],
            ['Description', lambda dist, name, plugin, activated, *args: self.extract_description(plugin, activated), True]
        ]

    @staticmethod
    def extract_module(plugin):
        module = plugin.__module__ + '.'
        if module.startswith('nagare.'):
            module = '~' + module[7:]

        return module + plugin.__name__

    @staticmethod
    def extract_description(plugin, activated_plugin):
        return (plugin if activated_plugin is None else activated_plugin).DESC
