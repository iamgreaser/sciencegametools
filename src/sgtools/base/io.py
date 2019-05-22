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


class EndOfFileReached(Exception):
    pass


class BitReader(metaclass=ABCMeta):
    """Abstract interface for a bit-level reader stream."""
    __slots__ = (
        "_fp",
    )

    def __init__(self, fp): # type: (IO[bytes]) -> None
        self._fp = fp # type: IO[bytes]

    @abstractmethod
    def sync(self): # type: () -> None
        """Aligns the file cursor to the nearest byte."""
        raise NotImplementedError()

    @abstractmethod
    def readbits(self, total): # type: (int) -> int
        """Reads a fixed number of bits and returns the result."""
        raise NotImplementedError()
        

class BitReaderLe(BitReader):
    """Little-endian unswapped bit reader."""
    __slots__ = (
        "_brem",
        "_bval",
    )

    def __init__(self, fp): # type: (IO[bytes]) -> None
        super().__init__(fp)
        self._brem = 0 # type: int
        self._bval = 0 # type: int

    def sync(self): # type: () -> None
        self._brem = 0

    def readbits(self, total): # type: (int) -> int
        outv = 0 # type: int

        for i in range(total):
            if self._brem < 1:
                assert self._brem == 0
                b = self._fp.read(1)
                if b == b"":
                    raise EndOfFileReached("This is DEFINITELY the end of the file.")
                self._bval = b[0]
                self._brem = 8

            if (self._bval & 0x01) != 0:
                outv |= 1 << i
            self._bval >>= 1

            self._brem -= 1

        return outv
