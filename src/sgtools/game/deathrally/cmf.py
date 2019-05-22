#!/usr/bin/env python3 --
# vim: set sts=4 sw=4 et :

import os
import os.path
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

OUT_DIR = os.path.join(*["uncmf"]) # type: str

def main(): # type: () -> None
    for fname in sys.argv[1:]:
        process_cmf(fname)

def process_cmf(cmf_fname): # type: (str) -> None
    print(f"Processing {cmf_fname!r}")
    ensure_dirs(OUT_DIR)
    data = bytearray(open(cmf_fname, "rb").read())
    for pos in range(len(data)):
        v = data[pos]
        v = (((v<<(pos%7))|(v>>(8-(pos%7)))) - (0x6D + (pos*0x11))) & 0xFF
        data[pos] = v

    if data[0x2C:0x2C+0x4] == b"SCRM":
        out_fname = os.path.join(*[OUT_DIR, cmf_fname + ".s3m"])
    elif data[0x00:0x00+0x11] == b"Extended Module: ":
        out_fname = os.path.join(*[OUT_DIR, cmf_fname + ".xm"])
    else:
        out_fname = os.path.join(*[OUT_DIR, cmf_fname + ".unknown"])

    with open(out_fname, "wb") as outfp:
        outfp.write(data)


if __name__ == "__main__":
    main()

