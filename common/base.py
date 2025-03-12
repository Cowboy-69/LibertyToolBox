# based on Liberty Four: https://gtaforums.com/topic/990530-relsrc-liberty-four

import numpy as np
from typing import overload

class VirtualTables:
    gtaDrawable = np.uint(0x695254)
    gtaFragType = np.uint(0x695238)
    pgDictionary_gtaDrawable = np.uint(0x6953A4)
    pgDictionary_grcTexturePC = np.uint(0x695384)
    pgDictionary_grcTexture = np.uint(0x6A08A0)
    fragDrawable = np.uint(0x6A32DC)
    grmShaderGroup = np.uint(0x6B1644)
    grmShaderFx = np.uint(0x6B223C)
    grmModel = np.uint(0x6B0234)
    grmGeometry = np.uint(0x6B48F4)
    grcVertexBufferD3D = np.uint(0x6BBAD8)
    grcIndexBufferD3D = np.uint(0x6BB870)
    grcTexture = np.uint(0x6B675C)
    grcTexturePC = np.uint(0x6B1D94)
    phArchetypeDamp = np.uint(0x69A5BC)
    phBoundComposite = np.uint(0x69BBEC)
    phBoundBox = np.uint(0x69D56C)
    phBoundGeometry = np.uint(0x69AAF4)
    phBoundCurvedGeometry = np.uint(0x69B41C)
    evtSet = np.uint(0x6A4678)
    joint = np.uint(7022456)

class RSC5Flag:
    def __init__(self):
        self.flag = np.int32(0)

    def GetVPage0(self):
        return (np.int32(self.flag >> 4)) & 0x7F

    def GetVSize(self):
        return np.int32((np.int32(self.flag >> 11)) & 0xF)
    def SetVSize(self, value):
        self.flag = (np.int32(self.flag & -30721)) | (np.int32((value & 0xF) << 11))

    def GetTotalVSize(self):
        return np.int32((self.flag & 0x7FF) << self.GetVSize() + 8)
    def GetSizeVPage0(self):
        return np.int32(4096 << self.GetVSize())

    def SetVPage0(self, value):
        self.flag = (self.flag & -2033) | (np.int32((value & 0x7F) << 4))
    def SetVPage1(self, value):
        self.flag = (self.flag & -9) | (np.int32((value & 1) << 3))
    def SetVPage2(self, value):
        self.flag = (self.flag & -5) | (np.int32((value & 1) << 2))
    def SetVPage3(self, value):
        self.flag = (self.flag & -3) | (np.int32((value & 1) << 1))
    def SetVPage4(self, value):
        self.flag = (self.flag & -2) | (value & 1)

    def GetPPage0(self):
        return (np.int32(self.flag >> 19)) & 0x7F

    def SetPPage0(self, value):
        self.flag = (self.flag & -66584577) | (np.int32((value & 0x7F) << 19))
    def SetPPage1(self, value):
        self.flag = (self.flag & -262145) | (np.int32((value & 1) << 18))
    def SetPPage2(self, value):
        self.flag = (self.flag & -131073) | (np.int32((value & 1) << 17))
    def SetPPage3(self, value):
        self.flag = (self.flag & -65537) | (np.int32((value & 1) << 16))
    def SetPPage4(self, value):
        self.flag = (self.flag & -32769) | (np.int32((value & 1) << 15))

    def GetPSize(self):
        return (np.int32(self.flag >> 26)) & 0xF
    
    def SetPSize(self, value):
        self.flag = (np.int32(self.flag & -1006632961)) | (np.int32((np.int32(value & 0xF)) << 26))

    def GetTotalPSize(self):
        return np.int32((np.int32((self.flag >> 15)) & 0x7FF) << self.GetPSize() + 8)

    def GetSizePPage0(self):
        return np.int32(4096 << self.GetPSize())
    
    def GetCompressed(self):
        return (np.int64((np.int64(self.flag >> 30)) & 1)) == 1
    
    def SetCompressed(self, value):
        self.flag = np.int32(self.flag & -1073741825) | np.int32(1) << np.int32(30)

    def GetIsRes(self):
        return ((np.int64(self.flag >> 31)) & 1) == 1
    
    def SetIsRes(self, value):
        self.flag = np.int32(self.flag & 0x7FFFFFFF) | np.int32(1) << np.int32(31)

class datBase:
    def __init__(self):
        self._vmt = np.uint32(0x2802) # Virtual Method Table

class pgBase(datBase):
    def __init__(self):
        super().__init__()

        self.pageMap = Ptr()

class Ptr():
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, _ptr : np.uint32) -> None: ...
    @overload
    def __init__(self, _offset : np.uint32, _blockType : np.uint32) -> None: ...

    def __init__(self, *args):
        if (len(args) == 0):
            self.ptr = np.uint32(0)
        elif (len(args) == 1):
            _ptr = np.uint32(args[0])
            self.ptr = np.uint32(_ptr)
        elif (len(args) == 2):
            _offset = np.uint32(args[0])
            _blockType = np.uint32(args[1])
            self.ptr = np.uint32(_offset & 0x0fffffff | (_blockType & 0xf) << 28)

    def GetOffset(self):
        value = np.int64(self.ptr & 0x0fffffff)
        return value.item()

class SimpleCollection:
    def __init__(self):
        self.data = Ptr()
        self.count = np.ushort(0)
        self.size = np.ushort(0)

class pgDictionary(pgBase):
    def __init__(self):
        super().__init__()

        self.parent = np.uint(0)
        self.usageCount = np.uint32(0) # ulong
        self.hashes = SimpleCollection()
        self.data = SimpleCollection()

        self._structSize = 0x20
        self._hashes = [] # np.uint
        self._data = [] # Ptr

    def SortData(self):
        sorted = []
        for i in range(0, self.hashes.count):
            sorted.append(self._hashes[i])
        sorted.sort()

        sortedPtr = [0] * self.data.count
        for i in range(0, self.data.count):
            for j in range(0, self.data.count):
                if (sorted[i] == self._hashes[j]):
                    sortedPtr[i] = self._data[j]

        for i in range(0, self.hashes.count):
            self._hashes[i] = sorted[i]

        for i in range(0, self.data.count):
            self._data[i] = sortedPtr[i]

def SetBit(value, pos, value2, valSize):
    returnValue = np.longlong(value) | ((value2 << (64 - valSize)) >> (64 - valSize)) << pos
    return np.longlong(returnValue)

def GetValueFromBits(value, valueSize, valuePos):
    value1 = valuePos + valueSize
    value2 = 64 - np.uint64(value1)
    value3 = np.uint64(value) << np.uint64(value2)
    value4 = 64 - np.uint64(valueSize)
    value5 = np.uint64(value3) >> np.uint64(value4)
    return value5
