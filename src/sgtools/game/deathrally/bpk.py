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
    from typing import Dict
    from typing import IO
    from typing import List
    from typing import Optional
    from typing import Tuple

from sgtools.base.io import BitReader
from sgtools.base.io import BitReaderLe
from sgtools.base.io import EndOfFileReached
from sgtools.base.utils import ensure_dirs

OUT_ROOT_DIR = os.path.join(*["unpacked"]) # type: str

#DEBUG_RAW_READS = True
DEBUG_RAW_READS = False

TGA_SIZE_PAL_MAPS = {
    2250: (15, 150, "MENU.PAL",), # palette is kinda wrong here
    4096: (64, 64, "MENU.PAL",),
    5440: (272, 20, "MENU.PAL",),
    64000: (320, 200, None,),
    98640: (360, 274, "MENU.PAL",),
    640*480: (640, 480, None,),
} # type: Dict[int, Tuple[int, int, Optional[str]]]


class LzwReader:
    __slots__ = (
        "_fp",
        "_width",
        "_table",
        "_next",
        "_prev",
        "_max_width",
    )

    def __init__(self, fp): # type: (BitReader) -> None
        self._fp = fp # type: BitReader
        self._max_width = 12 # type: int

        self.reset_tables()

    def reset_tables(self): # type: () -> None
        self._width = 9 # type: int
        self._table = [] # type: List[bytes]
        self._next = b"" # type: bytes
        self._prev = b"" # type: bytes

        for i in range(256):
            v = i # type: int
            v = ((v>>3)&0xFF) | (v<<(8-3)&0xFF) # reverse the encraption
            self._table.append(bytes([v]))

        self._table.append(b"") # 0x100: EOF
        self._table.append(b"") # 0x101: Reset tables

    def getraw(self): # type: () -> int
        v = self._fp.readbits(self._width) # type: int
        if DEBUG_RAW_READS:
            print(f"{v:012b} {v:03X}")
        return v

    def getnext(self): # type: () -> bytes
        v = self.getraw()

        #return b""
        #print(hex(len(self._table)))

        if v == 0x100:
            raise EndOfFileReached("This is probably the end of the file.")
            #self._fp.sync()
            #self.reset_tables()
            #return b""

        elif v == 0x101:
            self.reset_tables()
            return b""

        elif v == len(self._table):
            assert self._prev != b""
            data = self._prev + self._prev[:1] # type: bytes
            assert data != b""
            self._next = data[-1:]
            assert self._next != b""
            if self._prev != b"":
                self.add_chain(self._prev + data[:1])
            self._prev = data
            return data

        else:
            if v >= len(self._table):
                print(v, len(self._table))

            data = self._table[v]
            assert data != b""
            self._next = data[-1:]
            assert self._next != b""
            if self._prev != b"":
                self.add_chain(self._prev + data[:1])
            self._prev = data
            return data

    def add_chain(self, data): # type: (bytes) -> None
        if len(self._table) < (1<<self._max_width)-1:
            assert data != b""
            v = len(self._table)
            #print(f"ADD {v:012b} {v:03X} {data!r}")
            self._table.append(data)
            if len(self._table) >= (1<<(self._width)):
                self._width += 1
                #print(f"NEW WIDTH {self._width}")


def main(): # type: () -> None
    for in_fname in sys.argv[1:]:
        with open(in_fname, "rb") as raw_infp:
            infp = LzwReader(BitReaderLe(raw_infp))
            process_file(infp, in_fname)


def process_file(infp, in_fname): # type: (LzwReader, str) -> None
    print(f"Processing {in_fname!r}")
    outdata_list = [] # type: List[bytes]
    try:
        while True:
            v = infp.getnext() # type: bytes
            outdata_list.append(v)
    except EndOfFileReached:
        pass

    outdata = b"".join(outdata_list) # type: bytes
    ensure_dirs(OUT_ROOT_DIR)
    out_fname = os.path.join(*[OUT_ROOT_DIR, in_fname+".unlzw"])
    print(len(outdata))
    with open(out_fname, "wb") as outfp:
        outfp.write(outdata)

    w, h, = (0, 0,) # type: Tuple[int, int]
    has_dims = False
    paldata = b"" # type: bytes
    if outdata[:4] == b"RIX3":
        w, h, unk1 = struct.unpack("<HHH", outdata[0x4:][:0x6])
        print(f"RIX3 file detected, {w} x {h} (unk {unk1} / {unk1:04X})")
        paldata = outdata[0xA:][:256*3]
        assert len(paldata) == 256*3
        outdata = outdata[0x30A:]
        has_dims = True

    elif len(outdata) in TGA_SIZE_PAL_MAPS:
        w, h, pal_fname = TGA_SIZE_PAL_MAPS[len(outdata)]
        has_dims = True
        if pal_fname is None:
            in_pal_fname = in_fname.rpartition(".")[0] + ".PAL"
        else:
            in_pal_fname = pal_fname

        try:
            with open(in_pal_fname, "rb") as inpalfp:
                paldata = inpalfp.read()
        except FileNotFoundError:
            pass # can't make a tga file
        else:
            print(f"Got palette {in_pal_fname}")
            assert len(paldata) == 256*3

    if has_dims and paldata != b"":
        tga_out_fname = os.path.join(*[OUT_ROOT_DIR, in_fname+".tga"])
        print(f"Writing {tga_out_fname!r}")
        assert w*h == len(outdata)
        with open(tga_out_fname, "wb") as outfp:
            outfp.write(struct.pack("<BBB", 0, 1, 1))
            outfp.write(struct.pack("<HHB", 0, 256, 24))
            outfp.write(struct.pack("<HHHH", 0, 0, w, h))
            outfp.write(struct.pack("<BB", 8, 0b00100000))
            for i in range(256):
                outfp.write(bytes([(paldata[i*3+2]*0x41)>>4]))
                outfp.write(bytes([(paldata[i*3+1]*0x41)>>4]))
                outfp.write(bytes([(paldata[i*3+0]*0x41)>>4]))
            outfp.write(outdata)


if __name__ == "__main__":
    main()

