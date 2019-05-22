#!/usr/bin/env python3 --
# vim: set sts=4 sw=4 et :

import os
import os.path
import struct
import sys

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False
else:
    from typing import Iterable
    from typing import IO
    from typing import List
    from typing import Tuple

from sgtools.base.utils import ensure_dirs

OUT_ROOT_DIR = os.path.join(*["unpacked"]) # type: str


class BpaFatEntry:
    __slots__ = (
        "fname",
        "data",
    )

    def __init__(self, *, fname, data): # type: (*, str, bytes) -> None
        self.fname = fname # type: str
        self.data = data # type: bytes


class BpaReader:
    __slots__ = (
        "_fname",
        "_fat",
        "_fp",
    )

    def _get_max_fat_entries(self): # type: () -> int
        return 255
        
    def __init__(self, *, fname, fp): # type: (str, IO[bytes]) -> None
        self._fname = fname # type: str
        self._fp = fp # type: IO[bytes]
        self._load_all()

    def _load_all(self): # type: () -> None
        self._fp.seek(0)
        file_count, = struct.unpack("<I", self._fp.read(4)) # type: Tuple[int]
        assert file_count <= self._get_max_fat_entries()
        self._fat = [] # type: List[BpaFatEntry]

        # Here we juggle two pointers:
        # the FAT pointer,
        # and the pointer with all the file data.
        #
        # It's easier to load the fat in one go,
        # but here I only need to create the file structures once.
        #
        # TODO: use a context manager for multiple file pointers.
        # Or alternatively abuse mmap.
        # Or just dump the whole thing into a byte array.

        fat_ptr = self._fp.tell() # type: int
        file_ptr = (4 + (13+4)*self._get_max_fat_entries()) # type: int
        for fidx in range(file_count):
            base_fname = self._read_encrapted_filename()
            size, = struct.unpack("<I", self._fp.read(4)) # type: Tuple[int]

            fat_ptr = self._fp.tell()
            self._fp.seek(file_ptr)

            data = self._fp.read(size) # type: bytes
            assert len(data) == size
            self._fat.append(BpaFatEntry(
                fname=base_fname,
                data=data,
            ))

            file_ptr = self._fp.tell()
            self._fp.seek(fat_ptr)

    def _read_encrapted_filename(self): # type: () -> str
        raw_fname = bytearray(self._fp.read(13)) # type: bytearray
        for i in range(len(raw_fname)):
            if raw_fname[i] != 0:
                raw_fname[i] = (raw_fname[i] - (117 - 3*i)) & 0xFF
        base_fname = bytes(raw_fname).partition(b"\x00")[0].decode("utf-8") # type: str
        return base_fname

    def each_fat_entry(self): # type: () -> Iterable[BpaFatEntry]
        return self._fat

    def get_fname(self): # type: () -> str
        return self._fname


def main(): # type: () -> None
    for bpa_fname in sys.argv[1:]:
        with open(bpa_fname, "rb") as infp:
            bpa_reader = BpaReader(
                fname=bpa_fname,
                fp=infp,
            )
            process_bpa_archive(bpa_reader)


def process_bpa_archive(bpa_reader): # type: (BpaReader) -> None
    bpa_fname = bpa_reader.get_fname() # type: str
    print(f"Processing {bpa_fname}")

    if "." in bpa_fname:
        bpa_root = bpa_fname.rpartition(".")[0] # type: str
    else:
        bpa_root = bpa_fname

    out_root = os.path.join(*[OUT_ROOT_DIR, bpa_root])
    ensure_dirs(out_root)

    for fat_entry in bpa_reader.each_fat_entry():
        out_fname = os.path.join(*[out_root, fat_entry.fname])
        data = fat_entry.data
        print(f"- {out_fname!r} {len(data)}")
        with open(out_fname, "wb") as outfp:
            outfp.write(fat_entry.data)


if __name__ == "__main__":
    main()
