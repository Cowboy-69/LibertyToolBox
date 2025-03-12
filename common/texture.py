# based on Liberty Four: https://gtaforums.com/topic/990530-relsrc-liberty-four

import numpy as np

from .base import pgBase, Ptr
from .utils import Vector3

class grcTextureReferenceBase(pgBase):
    def __init__(self):
        super().__init__()

        self._f8 = np.ubyte(0)
        self._f9 = np.ubyte(0)
        self.usageCount = np.ushort(0)
        self._fc = np.uint32(0) # unsigned long

class grcTextureReference(grcTextureReferenceBase):
    def __init__(self):
        super().__init__()

        self._f10 = np.uint32(0) # unsigned long
        self.name = Ptr()
        self.texture = np.uint(0)

        self._structSize = np.uint(0x1c)
        self._name = np.str_('')

class grcTexturePC(pgBase):
    def __init__(self):
        super().__init__()

        self._f8 = np.ubyte(0)
        self.depth = np.ubyte(0)
        self.usageCount = np.ushort(0)
        self._fC = np.uint32(0) # ulong
        self._f10 = np.uint32(0) # ulong
        self.name = Ptr()
        self.texture = Ptr()
        self.width = np.ushort(0)
        self.height = np.ushort(0)
        self.pixelFormat = np.uint32(0) # ulong
        self.stride = np.ushort(0)
        self.textureType = np.ubyte(0)
        self.levels = np.ubyte(0)
        self._f28 = Vector3()
        self._f34 = Vector3()
        self.prev = Ptr() # previous
        self.next = Ptr() # next
        self.pixelData = Ptr()
        self._f4C = np.ubyte(0)
        self._f4D = np.ubyte(0)
        self._f4E = np.ubyte(0)
        self._f4F = np.ubyte(0)

        self._structSize = np.uint(0x50)
        self._pixelDataSize = np.uint(0)
        self._pixelDataStartPos = np.uint(0) # from dds
        self._name = np.str_()
        self._pixelData = np.ubyte(0)
