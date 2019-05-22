#!/usr/bin/env python3 --
# vim: set sts=4 sw=4 et :

import os


def ensure_dirs(path): # type: (str) -> None
    try:
        os.makedirs(path)
    except FileExistsError:
        pass
