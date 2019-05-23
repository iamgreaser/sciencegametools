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
    from typing import IO


def main(): # type: () -> None
    for fname in sys.argv[1:]:
        with open(fname, "rb") as infp:
            haf2gif(fname, infp)


def haf2gif(haf_fname, haf_fp): # type: (str, IO[bytes]) -> None
    print(f"Processing {haf_fname!r}")

    if "." in haf_fname:
        haf_root = haf_fname.rpartition(".")[0] # type: str
    else:
        haf_root = haf_fname

    gif_fname = haf_root + ".gif"

    frame_count, = struct.unpack("<H", haf_fp.read(2))
    sound_triggers = list(haf_fp.read(frame_count))
    frame_lengths = list(haf_fp.read(frame_count))

    accum_delay = 0

    with open(gif_fname, "wb") as gif_fp:
        gif_fp.write(b"GIF89a") # Header

        # Logical Screen Descriptor
        gif_fp.write(struct.pack("<HH", 320, 120)) # Logical Screen Width and Height
        gif_fp.write(struct.pack("<B", 0b01110111)) # flags
        gif_fp.write(struct.pack("<B", 0)) # Background Color Index (ignored)
        gif_fp.write(struct.pack("<B", 0)) # Pixel Aspect Ratio (TODO: apply 240/200 height)

        # Application Extension Block: NETSCAPE2.0 animation
        gif_fp.write(struct.pack("<BB", 0x21, 0xFF)) # Application Extension Block
        gif_fp.write(b"\x0BNETSCAPE2.0") # Authentication Code
        gif_fp.write(struct.pack("<BBh", 3, 1, -1)) # block length, sub-block index (always 1), repetition count
        gif_fp.write(struct.pack("<B", 0)) # end of AEB

        for fidx in range(frame_count):
            frame_length, = struct.unpack("<H", haf_fp.read(2))
            raw_frame_data = bytearray(haf_fp.read(frame_length))

            # Fix up the palette, converting from 6bit to 8bit components
            for i in range(256*3):
                v = raw_frame_data[i]
                v = ((v<<6)|v) # 6 * 2 = 12
                v = v>>4 # 12 - 4 = 8
                raw_frame_data[i] = v

            # Graphic Control Extension
            accum_delay += frame_lengths[fidx]*100
            delay = accum_delay//70
            accum_delay -= delay*70
            gif_fp.write(struct.pack("<BB", 0x21, 0xF9)) # AEB identifier: GCE
            gif_fp.write(struct.pack("<BBHB", 4, 0b00000000, delay, 0)) # GCE data
            gif_fp.write(struct.pack("<B", 0)) # end of AEB

            # Image Descriptor
            gif_fp.write(struct.pack("<B", 0x2C))
            gif_fp.write(struct.pack("<HH", 0, 0)) # Image Left and Top Position
            gif_fp.write(struct.pack("<HH", 320, 120)) # Image Width and Height
            gif_fp.write(struct.pack("<B", 0b10000111)) # flags

            # Local Color Table, Table Based Image Data
            # (omiting the embedded 1-byte GIF Trailer here)
            gif_fp.write(raw_frame_data[:-1])

        # GIF Trailer
        gif_fp.write(b"\x3B")


if __name__ == "__main__":
    main()

