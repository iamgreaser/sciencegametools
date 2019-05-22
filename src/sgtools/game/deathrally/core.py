#!/usr/bin/env python3 --
# vim: set sts=4 sw=4 et :

from collections import OrderedDict
import os
import os.path
import struct
import sys

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False
else:
    from typing import Mapping
    from typing import IO
    from typing import List
    from typing import Tuple
    from typing import Type
    from typing import TypeVar
    from sgtools.base.core import TCoreFile

    TDeathRallyArchive = TypeVar("TDeathRallyArchive", bound="DeathRallyArchive")
    TDeathRallyCmfFile = TypeVar("TDeathRallyCmfFile", bound="DeathRallyCmfFile")

from sgtools.base.core import CoreArchive
from sgtools.base.core import CoreDirectory
from sgtools.base.core import CoreFile
from sgtools.base.core import CoreGameData
from sgtools.base.core import UnknownFile
from sgtools.game.deathrally.bpa import BpaReader


UNHANDLED_FILES = [
    "CDROM.INI",
    "DR.CFG",
    "DR.SG0",
    "DR.SG7",
    "DRHELP.EXE",
    "ENDANI.HAF",
    "ENDANI0.HAF",
    "RALLY.BAT",
    "RALLY.EXE",
    "RALLY.ICO",
    "SANIM.HAF",
    "SETUP.EXE",
] # type: List[str]


BPA_ARCHIVES = [
    "ENGINE.BPA",
    "IBFILES.BPA",
    "MENU.BPA",
    "MUSICS.BPA",
    "TR0.BPA",
    "TR1.BPA",
    "TR2.BPA",
    "TR3.BPA",
    "TR4.BPA",
    "TR5.BPA",
    "TR6.BPA",
    "TR7.BPA",
    "TR8.BPA",
    "TR9.BPA",
] # type: List[str]


class DeathRallyGameData(CoreGameData):
    __slots__ = ()

    def load_files(self): # type: () -> Mapping[str, CoreFile]
        files = [] # type: List[Tuple[str, CoreFile]]
        for fname in BPA_ARCHIVES:
            files.append((fname, DeathRallyArchive.read_from_file_name(fname),))
        return OrderedDict(files)

    def save_files(self, file_map): # type: (Mapping[str, CoreFile]) -> None
        raise NotImplementedError()

    @classmethod
    def read_from_file_object(cls, *, fname, fp): # type: (Type[TCoreFile], *, str, IO[bytes]) -> TCoreFile
        raise NotImplementedError()


class DeathRallyArchive(CoreArchive):
    __slots__ = (
        "_fname",
        "_file_map",
    )

    def __init__(self, *, fname, file_map): # type: (*, str, Mapping[str, CoreFile]) -> None
        self._fname = fname
        self._file_map = file_map

    def get_file_name(self): # type: () -> str
        return self._fname

    @classmethod
    def read_from_file_object(cls, *, fname, fp): # type: (Type[TDeathRallyArchive], *, str, IO[bytes]) -> TDeathRallyArchive
        bpa_reader = BpaReader(
            fname=fname,
            fp=fp,
        )
        bpa_fname = fname # type: str

        files = [] # type: List[Tuple[str, CoreFile]]
        for fat_entry in bpa_reader.each_fat_entry():
            file_fname = fat_entry.fname
            file_data = fat_entry.data

            if file_fname.endswith(".CMF"):
                file = DeathRallyCmfFile(
                    fname=file_fname,
                    data=file_data,
                ) # type: CoreFile
                file_fname = file.get_file_name()
            else:
                file = UnknownFile(
                    fname=file_fname,
                    data=file_data,
                )

            files.append((file_fname, file,))

        return cls(
            fname=bpa_fname,
            file_map=OrderedDict(files),
        )

    def load_files(self): # type: () -> Mapping[str, CoreFile]
        return OrderedDict(self._file_map)

    def save_files(self, file_map): # type: (Mapping[str, CoreFile]) -> None
        raise NotImplementedError()


class DeathRallyCmfFile(CoreFile):
    """A file definition for a Death Rally obfuscated music/sound file type."""

    __slots__ = (
        "_fname",
        "_data",
    )

    def __init__(self, *, fname, data): # type: (str, bytes) -> None
        heuristic = [] # type: List[str]

        self._data = self._unobfuscate_data(data)

        if self._data[0x002C:0x002C+0x04] == b"SCRM":
            heuristic.append("S3M")
        if self._data[0x0000:0x0000+0x11] == b"Extended Module: ":
            heuristic.append("XM")

        if heuristic == []:
            self._fname = fname
        elif heuristic == ["S3M"]:
            self._fname = fname.replace(".CMF", ".S3M")
        elif heuristic == ["XM"]:
            self._fname = fname.replace(".CMF", ".XM")
        else:
            raise Exception(f"confused heuristic {heuristic!r} for file {fname!r}")

    @staticmethod
    def _unobfuscate_data(data): # type: (bytes) -> bytes
        """Unobfuscate an obfuscated music/sound file."""
        wdata = bytearray(data)
        for pos in range(len(wdata)):
            v = wdata[pos]
            v = (((v<<(pos%7))|(v>>(8-(pos%7)))) - (0x6D + (pos*0x11))) & 0xFF
            wdata[pos] = v
        return bytes(wdata)

    def get_file_name(self): # type: () -> str
        return self._fname

    @classmethod
    def read_from_file_object(cls, *, fname, fp): # type: (Type[TDeathRallyCmfFile], *, str, IO[bytes]) -> TDeathRallyCmfFile
        return cls(fname=fname, data=fp.read())


def main(): # type: () -> None
    gamedata = DeathRallyGameData()
    remaining_file_maps = [] # type: List[Tuple[List[str], CoreFile]]
    remaining_file_maps.append((["workdir"], gamedata,))
    while len(remaining_file_maps) >= 1:
        pathlist, file, = remaining_file_maps.pop(0) # type: Tuple[List[str], CoreFile]
        if isinstance(file, CoreDirectory):
            file_map = file.load_files()
            for subfname, subfile in file_map.items():
                remaining_file_maps.append((pathlist + [subfname], subfile,))
        else:
            print(f"- {'/'.join(pathlist)!r}: {file!r}")


if __name__ == "__main__":
    main()

