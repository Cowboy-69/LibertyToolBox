# based on Liberty Four: https://gtaforums.com/topic/990530-relsrc-liberty-four

import ctypes
import numpy as np
import mmap
from enum import Enum

class PixelFormatDDS:
    def __init__(self):
        self.size = np.uint(0)
        self.flags = np.uint(0)
        self.fourCC = np.uint(0)
        self.RGBBitCount = np.uint(0)
        self.RBitMask = np.uint(0)
        self.GBitMask = np.uint(0)
        self.BBitMask = np.uint(0)
        self.ABitMask = np.uint(0)

    def Initialize(size, flags, fourCC, RGBBitCount, RBitMask, GBitMask, BBitMask, ABitMask):
        pixelFormat = PixelFormatDDS()

        pixelFormat.size = size
        pixelFormat.flags = flags
        if (type(fourCC) is str):
            pixelFormat.fourCC = np.uint(np.ubyte(ord(fourCC[0])))
            pixelFormat.fourCC += np.uint(np.ubyte(ord(fourCC[1]))) << 8
            pixelFormat.fourCC += np.uint(np.ubyte(ord(fourCC[2]))) << 16
            pixelFormat.fourCC += np.uint(np.ubyte(ord(fourCC[3]))) << 24
        else:
            pixelFormat.fourCC = fourCC
        pixelFormat.RGBBitCount = RGBBitCount
        pixelFormat.RBitMask = RBitMask
        pixelFormat.GBitMask = GBitMask
        pixelFormat.BBitMask = BBitMask
        pixelFormat.ABitMask = ABitMask

        return pixelFormat

    def ArePixelFormatsEqual(firstPixelFormat, secondPixelFormat):
        if (firstPixelFormat.size != secondPixelFormat.size):
            return False
        if (firstPixelFormat.flags != secondPixelFormat.flags):
            return False
        if (firstPixelFormat.fourCC != secondPixelFormat.fourCC):
            return False
        if (firstPixelFormat.RGBBitCount != secondPixelFormat.RGBBitCount):
            return False
        if (firstPixelFormat.RBitMask != secondPixelFormat.RBitMask):
            return False
        if (firstPixelFormat.GBitMask != secondPixelFormat.GBitMask):
            return False
        if (firstPixelFormat.BBitMask != secondPixelFormat.BBitMask):
            return False
        if (firstPixelFormat.ABitMask != secondPixelFormat.ABitMask):
            return False
        return True

class PixelFormatTypes(Enum):
    DXT1 = 0
    DXT2 = 1
    DXT3 = 2
    DXT4 = 3
    DXT5 = 4
    X8R8G8B8 = 5
    A8R8G8B8 = 6
    L8 = 7
    R8G8B8 = 8
    R5G6B5 = 9
    X1R5G5B5 = 10
    A1R5G5B5 = 11
    A4R4G4B4 = 12
    R3G3B2 = 13
    A8 = 14
    A8R3G3B2 = 15
    X4R4G4B4 = 16
    A2B10G10R10 = 17
    A8B8G8R8 = 18
    X8B8G8R8 = 19
    G16R16 = 20
    A2R10G10B10 = 21
    A16B16G16R16 = 22
    A8L8 = 23
    A4L4 = 24

class UniversalPixel:
    def __init__(self):
        self.r = np.ushort(0) # red
        self.g = np.ushort(0) # green
        self.b = np.ushort(0) # blue
        self.a = np.ushort(0) # alpha
        self.l = np.ushort(0) # luminance

class TextureDDS:
    def __init__(self):
        self.DDS_MAGIC = np.uint(0x20534444) # "DDS " string

        self.DDS_FOURCC =           np.int32(0x00000004)  # DDPF_FOURCC
        self.DDS_RGB =              np.int32(0x00000040)  # DDPF_RGB
        self.DDS_RGBA =             np.int32(0x00000041)  # DDPF_RGB | DDPF_ALPHAPIXELS
        self.DDS_LUMINANCE =        np.int32(0x00020000)  # DDPF_LUMINANCE
        self.DDS_LUMINANCEA =       np.int32(0x00020001)  # DDPF_LUMINANCE | DDPF_ALPHAPIXELS
        self.DDS_ALPHAPIXELS =      np.int32(0x00000001)  # DDPF_ALPHAPIXELS
        self.DDS_ALPHA =            np.int32(0x00000002)  # DDPF_ALPHA
        self.DDS_PAL8 =             np.int32(0x00000020)  # DDPF_PALETTEINDEXED8
        self.DDS_PAL8A =            np.int32(0x00000021)  # DDPF_PALETTEINDEXED8 | DDPF_ALPHAPIXELS
        self.DDS_BUMPDUDV =         np.int32(0x00080000)  # DDPF_BUMPDUDV
        self.DDS_BUMPLUMINANCE =    np.int32(0x00040000)

        self._size = np.uint(0)
        self._flags = np.uint(0)
        self._height = np.uint(0)
        self._width = np.uint(0)
        self._pitchOrLinearSize = np.uint(0)
        self._depth = np.uint(0)
        self._mipMapCount = np.uint(0)
        self._reserved1 = [np.uint(0)] * 11
        self._ddspf = PixelFormatDDS()
        self._caps = np.uint(0)
        self._caps2 = np.uint(0)
        self._caps3 = np.uint(0)
        self._caps4 = np.uint(0)
        self._reserved2 = np.uint(0)

        self.DDSPF_DXT1 = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "DXT1", 0, 0, 0, 0, 0)
        self.DDSPF_DXT2 = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "DXT2", 0, 0, 0, 0, 0)
        self.DDSPF_DXT3 = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "DXT3", 0, 0, 0, 0, 0)
        self.DDSPF_DXT4 = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "DXT4", 0, 0, 0, 0, 0)
        self.DDSPF_DXT5 = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "DXT5", 0, 0, 0, 0, 0)
        self.DDSPF_BC4_UNORM = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "BC4U", 0, 0, 0, 0, 0)
        self.DDSPF_BC4_SNORM = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "BC4S", 0, 0, 0, 0, 0)
        self.DDSPF_BC5_UNORM = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "BC5U", 0, 0, 0, 0, 0)
        self.DDSPF_BC5_SNORM = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "BC4S", 0, 0, 0, 0, 0)
        self.DDSPF_R8G8_B8G8 = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "RGBG", 0, 0, 0, 0, 0)
        self.DDSPF_G8R8_G8B8 = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "GRGB", 0, 0, 0, 0, 0)
        self.DDSPF_YUY2 = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "YUY2", 0, 0, 0, 0, 0)
        self.DDSPF_UYVY = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, "UYVY", 0, 0, 0, 0, 0)
        
        self.DDSPF_A16B16G16R16 = PixelFormatDDS.Initialize(0x20, self.DDS_FOURCC, 0x00000024, 0, 0, 0, 0, 0)
        self.DDSPF_A8R8G8B8 = PixelFormatDDS.Initialize(0x20, self.DDS_RGBA, 0, 32, 0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000)
        self.DDSPF_X8R8G8B8 = PixelFormatDDS.Initialize(0x20, self.DDS_RGB,  0, 32, 0x00ff0000, 0x0000ff00, 0x000000ff, 0)
        self.DDSPF_A8B8G8R8 = PixelFormatDDS.Initialize(0x20, self.DDS_RGBA, 0, 32, 0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000)
        self.DDSPF_X8B8G8R8 = PixelFormatDDS.Initialize(0x20, self.DDS_RGB,  0, 32, 0x000000ff, 0x0000ff00, 0x00ff0000, 0)
        self.DDSPF_G16R16 = PixelFormatDDS.Initialize(0x20, self.DDS_RGB,  0, 32, 0x0000ffff, 0xffff0000, 0, 0)
        self.DDSPF_R5G6B5 = PixelFormatDDS.Initialize(0x20, self.DDS_RGB, 0, 16, 0xf800, 0x07e0, 0x001f, 0)
        self.DDSPF_A1R5G5B5 = PixelFormatDDS.Initialize(0x20, self.DDS_RGBA, 0, 16, 0x7c00, 0x03e0, 0x001f, 0x8000)
        self.DDSPF_X1R5G5B5 = PixelFormatDDS.Initialize(0x20, self.DDS_RGB, 0, 16, 0x7c00, 0x03e0, 0x001f, 0)
        self.DDSPF_A4R4G4B4 = PixelFormatDDS.Initialize(0x20, self.DDS_RGBA, 0, 16, 0x0f00, 0x00f0, 0x000f, 0xf000)
        self.DDSPF_X4R4G4B4 = PixelFormatDDS.Initialize(0x20, self.DDS_RGB, 0, 16, 0x0f00, 0x00f0, 0x000f, 0)
        self.DDSPF_R8G8B8 = PixelFormatDDS.Initialize(0x20, self.DDS_RGB, 0, 24, 0xff0000, 0x00ff00, 0x0000ff, 0)
        self.DDSPF_A8R3G3B2 = PixelFormatDDS.Initialize(0x20, self.DDS_RGBA, 0, 16, 0x00e0, 0x001c, 0x0003, 0xff00)
        self.DDSPF_R3G3B2 = PixelFormatDDS.Initialize(0x20, self.DDS_RGB, 0, 8, 0xe0, 0x1c, 0x03, 0)
        self.DDSPF_A4L4 = PixelFormatDDS.Initialize(0x20, self.DDS_LUMINANCEA, 0, 8, 0x0f, 0, 0, 0xf0)
        self.DDSPF_L8 = PixelFormatDDS.Initialize(0x20, self.DDS_LUMINANCE, 0, 8, 0xff, 0, 0, 0)
        self.DDSPF_L16 = PixelFormatDDS.Initialize(0x20, self.DDS_LUMINANCE, 0, 16, 0xffff, 0, 0, 0)
        self.DDSPF_A8L8 = PixelFormatDDS.Initialize(0x20, self.DDS_LUMINANCEA, 0, 16, 0x00ff, 0, 0, 0xff00)
        self.DDSPF_A8L8_ALT = PixelFormatDDS.Initialize(0x20, self.DDS_LUMINANCEA, 0, 8, 0x00ff, 0, 0, 0xff00)
        self.DDSPF_L8_NVTT1 = PixelFormatDDS.Initialize(0x20, self.DDS_RGB, 0, 8, 0xff, 0, 0, 0)
        self.DDSPF_L16_NVTT1 = PixelFormatDDS.Initialize(0x20, self.DDS_RGB, 0, 16, 0xffff, 0, 0, 0)
        self.DDSPF_A8L8_NVTT1 = PixelFormatDDS.Initialize(0x20, self.DDS_RGBA, 0, 16, 0x00ff, 0, 0, 0xff00)
        self.DDSPF_A8 = PixelFormatDDS.Initialize(0x20, self.DDS_ALPHA, 0, 8, 0, 0, 0, 0xff)
        self.DDSPF_V8U8 = PixelFormatDDS.Initialize(0x20, self.DDS_BUMPDUDV, 0, 16, 0x00ff, 0xff00, 0, 0)
        self.DDSPF_Q8W8V8U8 = PixelFormatDDS.Initialize(0x20, self.DDS_BUMPDUDV, 0, 32, 0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000)
        self.DDSPF_V16U16 = PixelFormatDDS.Initialize(0x20, self.DDS_BUMPDUDV, 0, 32, 0x0000ffff, 0xffff0000, 0, 0)
        self.DDSPF_A2R10G10B10 = PixelFormatDDS.Initialize(0x20, self.DDS_RGBA, 0, 32, 0x000003ff, 0x000ffc00, 0x3ff00000, 0xc0000000)
        self.DDSPF_A2B10G10R10 = PixelFormatDDS.Initialize(0x20, self.DDS_RGBA, 0, 32, 0x3ff00000, 0x000ffc00, 0x000003ff, 0xc0000000)

        self.format = PixelFormatTypes.DXT1
        self.levels = np.uint(0)
        self.stride = np.uint(0)
        self.height = np.uint(0)
        self.width = np.uint(0)
        self.dataSize = [] # np.uint
        self.data = [] # np.ubyte

    def UpdateInfo(self):
        # format
        if (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_DXT1)):
            self.format = PixelFormatTypes.DXT1
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_DXT2)):
            self.format = PixelFormatTypes.DXT2
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_DXT3)):
            self.format = PixelFormatTypes.DXT3
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_DXT4)):
            self.format = PixelFormatTypes.DXT4
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_DXT5)):
            self.format = PixelFormatTypes.DXT5
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_X8R8G8B8)):
            self.format = PixelFormatTypes.X8R8G8B8
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A8R8G8B8)):
            self.format = PixelFormatTypes.A8R8G8B8
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_L8)):
            self.format = PixelFormatTypes.L8
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_R8G8B8)):
            self.format = PixelFormatTypes.R8G8B8
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_R5G6B5)):
            self.format = PixelFormatTypes.R5G6B5
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_X1R5G5B5)):
            self.format = PixelFormatTypes.X1R5G5B5
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A1R5G5B5)):
            self.format = PixelFormatTypes.A1R5G5B5
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A4R4G4B4)):
            self.format = PixelFormatTypes.A4R4G4B4
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_R3G3B2)):
            self.format = PixelFormatTypes.R3G3B2
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A8)):
            self.format = PixelFormatTypes.A8
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A8R3G3B2)):
            self.format = PixelFormatTypes.A8R3G3B2
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_X4R4G4B4)):
            self.format = PixelFormatTypes.X4R4G4B4
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A2B10G10R10)):
            self.format = PixelFormatTypes.A2B10G10R10
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A8B8G8R8)):
            self.format = PixelFormatTypes.A8B8G8R8
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_X8B8G8R8)):
            self.format = PixelFormatTypes.X8B8G8R8
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_G16R16)):
            self.format = PixelFormatTypes.G16R16
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A2R10G10B10)):
            self.format = PixelFormatTypes.A2R10G10B10
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A16B16G16R16)):
            self.format = PixelFormatTypes.A16B16G16R16
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A8L8)):
            self.format = PixelFormatTypes.A8L8
        elif (PixelFormatDDS.ArePixelFormatsEqual(self._ddspf, self.DDSPF_A4L4)):
            self.format = PixelFormatTypes.A4L4
        
        self.height = self._height
        self.width = self._width
        # stride
        if (self.format == PixelFormatTypes.DXT1):
            self.stride = np.uint(((max(1, np.uint((self.width + 3) / 4)) * 8) * max(1, np.uint((self.height + 3) / 4)) / self.height))
        elif (self.format == PixelFormatTypes.DXT2):
            self.stride = np.uint((max(1, np.uint((self.width + 3) / 4)) * 16) * max(1, np.uint((self.height + 3) / 4)) / self.height)
        elif (self.format == PixelFormatTypes.DXT3):
            self.stride = np.uint((max(1, np.uint((self.width + 3) / 4)) * 16) * max(1, np.uint((self.height + 3) / 4)) / self.height)
        elif (self.format == PixelFormatTypes.DXT4):
            self.stride = np.uint((max(1, np.uint((self.width + 3) / 4)) * 16) * max(1, np.uint((self.height + 3) / 4)) / self.height)
        elif (self.format == PixelFormatTypes.DXT5):
            self.stride = np.uint((max(1, np.uint((self.width + 3) / 4)) * 16) * max(1, np.uint((self.height + 3) / 4)) / self.height)
        elif (self.format == PixelFormatTypes.A16B16G16R16):
            self.stride = np.uint((self.width * 64 + 7) / 8)
        else:
            self.stride = np.uint((self.width * self._ddspf.RGBBitCount + 7) / 8)

        self.levels = self._mipMapCount
        self.dataSize.append(self.stride * self.height)
        for i in range(2, self.levels):
            self.dataSize.append((self.stride * self.height) >> ((i - 1) * 2))

    def SetInfo(self, heigh, width, size, depth, levels, format):
        self._height = heigh
        self._width = width
        self._pitchOrLinearSize = size
        self._depth = depth
        self._mipMapCount = levels

        if (format == PixelFormatTypes.DXT1):
            self._ddspf = self.DDSPF_DXT1
        elif (format == PixelFormatTypes.DXT2):
            self._ddspf = self.DDSPF_DXT2
        elif (format == PixelFormatTypes.DXT3):
            self._ddspf = self.DDSPF_DXT3
        elif (format == PixelFormatTypes.DXT4):
            self._ddspf = self.DDSPF_DXT4
        elif (format == PixelFormatTypes.DXT5):
            self._ddspf = self.DDSPF_DXT5
        elif (format == PixelFormatTypes.X8R8G8B8):
            self._ddspf = self.DDSPF_X8R8G8B8
        elif (format == PixelFormatTypes.A8R8G8B8):
            self._ddspf = self.DDSPF_A8R8G8B8
        elif (format == PixelFormatTypes.L8):
            self._ddspf = self.DDSPF_L8
        elif (format == PixelFormatTypes.R8G8B8):
            self._ddspf = self.DDSPF_R8G8B8
        elif (format == PixelFormatTypes.R5G6B5):
            self._ddspf = self.DDSPF_R5G6B5
        elif (format == PixelFormatTypes.X1R5G5B5):
            self._ddspf = self.DDSPF_X1R5G5B5
        elif (format == PixelFormatTypes.A1R5G5B5):
            self._ddspf = self.DDSPF_A1R5G5B5
        elif (format == PixelFormatTypes.A4R4G4B4):
            self._ddspf = self.DDSPF_A4R4G4B4
        elif (format == PixelFormatTypes.R3G3B2):
            self._ddspf = self.DDSPF_R3G3B2
        elif (format == PixelFormatTypes.A8):
            self._ddspf = self.DDSPF_A8
        elif (format == PixelFormatTypes.A8R3G3B2):
            self._ddspf = self.DDSPF_A8R3G3B2
        elif (format == PixelFormatTypes.X4R4G4B4):
            self._ddspf = self.DDSPF_X4R4G4B4
        elif (format == PixelFormatTypes.A2B10G10R10):
            self._ddspf = self.DDSPF_A2B10G10R10
        elif (format == PixelFormatTypes.X8B8G8R8):
            self._ddspf = self.DDSPF_X8B8G8R8
        elif (format == PixelFormatTypes.G16R16):
            self._ddspf = self.DDSPF_G16R16
        elif (format == PixelFormatTypes.A2R10G10B10):
            self._ddspf = self.DDSPF_A2R10G10B10
        elif (format == PixelFormatTypes.A16B16G16R16):
            self._ddspf = self.DDSPF_A16B16G16R16
        elif (format == PixelFormatTypes.A8L8):
            self._ddspf = self.DDSPF_A8L8
        elif (format == PixelFormatTypes.A4L4):
            self._ddspf = self.DDSPF_A4L4
        self.UpdateInfo()

    def Load(self, filePath):
        file = open(filePath, mode='rb')
        mapPointer = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        file.close()

        ddsMagic = np.frombuffer(mapPointer.read(4), dtype=np.uint)

        if (ddsMagic != self.DDS_MAGIC):
            return

        self._size = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._flags = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._height = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._width = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._pitchOrLinearSize = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._depth = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._mipMapCount = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        for i in range(0, 11):
            self._reserved1.append(np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item())
        self._ddspf.size = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._ddspf.flags = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._ddspf.fourCC = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._ddspf.RGBBitCount = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._ddspf.RBitMask = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._ddspf.GBitMask = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._ddspf.BBitMask = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._ddspf.ABitMask = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._caps = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._caps2 = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._caps3 = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._caps4 = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()
        self._reserved2 = np.frombuffer(mapPointer.read(4), dtype=np.uint)[0].item()

        height = self._height
        width = self._width

        for i in range(1, self._mipMapCount):
            if ((height < 8 and width < 8) or (height == 1 or width == 1)):
                self._mipMapCount = i
                break
            height = np.uint(height / 2)
            width = np.uint(width / 2)

        stride = np.uint(0)
        if (self._ddspf.flags == 0x00000004):
            if (self._ddspf.fourCC == 0x31545844): # dxt1
                stride = np.uint(((max(1, np.uint((self._width + 1) / 4)) * 8) * max(1, np.uint((self._height + 3) / 4)) / self._height))
            elif (self._ddspf.fourCC == 0x24): # 64
                stride = np.uint(((max(1, np.uint((self._width + 1) / 4)) * 64) * max(1, np.uint((self._height + 3) / 4)) / self._height))
            else:
                stride = np.uint(((max(1, np.uint((self._width + 1) / 4)) * 16) * max(1, np.uint((self._height + 3) / 4)) / self._height))
        else:
            stride = ((self._width * self._ddspf.RGBBitCount + 7) / 8)

        dataSize = stride * self._height
        for i in range(2, self._mipMapCount + 1):
            dataSize += (stride * self._height) >> ((i - 1) * 2)
        
        self.data = ctypes.create_string_buffer(dataSize.item())
        ctypes.memmove(ctypes.addressof(self.data), mapPointer.read(dataSize), dataSize)

        self.UpdateInfo()

    #TODO def Save
