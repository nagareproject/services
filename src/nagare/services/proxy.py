# Encoding: utf-8
# --
# Copyright (c) 2008-2023 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import functools


def proxy_to(dest, get_target=lambda self: self.proxy_target, blacklist=()):
    def _(cls):
        for name in dir(dest):
            method = getattr(dest, name)
            if not name.startswith('_') and (name not in blacklist) and callable(method):

                def _(method):
                    return functools.update_wrapper(
                        lambda self, *args, **kw: method(get_target(self), *args, **kw), method
                    )

                setattr(cls, name, _(method))

        return cls

    return _
