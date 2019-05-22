#!/usr/bin/env python3 --
# vim: set sts=4 sw=4 et :

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False
else:
    from typing import Mapping
    from typing import IO
    from typing import List
    from typing import Type
    from typing import TypeVar

    TCoreFile = TypeVar("TCoreFile", bound="CoreFile")
    TUnknownFile = TypeVar("TUnknownFile", bound="UnknownFile")


from abc import ABCMeta
from abc import abstractmethod


class CoreFile(metaclass=ABCMeta):
    """A file definition."""
    __slots__ = ()

    @abstractmethod
    def get_file_name(self): # type: () -> str
        raise NotImplementedError()

    @classmethod
    def read_from_file_name(cls, fname): # type: (Type[TCoreFile], str) -> TCoreFile
        with open(fname, "rb") as fp:
            return cls.read_from_file_object(fname=fname, fp=fp)

    @classmethod
    @abstractmethod
    def read_from_file_object(cls, *, fname, fp): # type: (Type[TCoreFile], *, str, IO[bytes]) -> TCoreFile
        raise NotImplementedError()


class UnknownFile(CoreFile):
    """A file definition for an unknown file type."""
    __slots__ = (
        "_fname",
        "_data",
    )

    def __init__(self, *, fname, data): # type: (str, bytes) -> None
        self._fname = fname
        self._data = data

    def get_file_name(self): # type: () -> str
        return self._fname

    @classmethod
    def read_from_file_object(cls, *, fname, fp): # type: (Type[TUnknownFile], *, str, IO[bytes]) -> TUnknownFile
        return cls(fname=fname, data=fp.read())


class CoreDirectory(CoreFile, metaclass=ABCMeta):
    """A directory definition."""
    __slots__ = ()

    @abstractmethod
    def load_files(self): # type: () -> Mapping[str, CoreFile]
        raise NotImplementedError()

    @abstractmethod
    def save_files(self, file_map): # type: (Mapping[str, CoreFile]) -> None
        raise NotImplementedError()


class CoreArchive(CoreDirectory, metaclass=ABCMeta):
    """An archive file definition."""
    __slots__ = ()

    @abstractmethod
    def load_files(self): # type: () -> Mapping[str, CoreFile]
        raise NotImplementedError()

    @abstractmethod
    def save_files(self, file_map): # type: (Mapping[str, CoreFile]) -> None
        raise NotImplementedError()


class CoreGameData(CoreDirectory, metaclass=ABCMeta):
    """A game data definition."""
    __slots__ = ()

    def get_file_name(self): # type: () -> str
        return "workdir"

    @abstractmethod
    def load_files(self): # type: () -> Mapping[str, CoreFile]
        raise NotImplementedError()

    @abstractmethod
    def save_files(self, file_map): # type: (Mapping[str, CoreFile]) -> None
        raise NotImplementedError()
