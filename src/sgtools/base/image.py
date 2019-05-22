#!/usr/bin/env python3 --
# vim: set sts=4 sw=4 et :

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False
else:
    from typing import IO


from abc import ABCMeta
from abc import abstractmethod


class BaseImage(metaclass=ABCMeta):
    __slots__ = ()

