# based on Liberty Four: https://gtaforums.com/topic/990530-relsrc-liberty-four

import numpy as np
import ctypes

from .base import datBase, pgBase, Ptr, SimpleCollection
from .utils import Vector4

class grcVertexBuffer(datBase):
    def __init__(self):
        super().__init__()

        self.vertexCount = np.ushort(0)
        self.locked = np.ubyte(0)
        self.unk_f7 = np.ubyte(0)
        self.lockedData = Ptr()
        self.vertexSize = np.uint32(0) # unsigned long
        self.declarations = Ptr()
        self.lockThreadId = np.uint(0)
        self.vertexData = Ptr()

class grcVertexBufferD3D(grcVertexBuffer):
    def __init__(self):
        super().__init__()

        self.vertexBuffer = Ptr()
        self.cacheHandle = ctypes.create_string_buffer(0x20)
        self.eD3DPool = np.uint(0)
        self.lockFlags = np.uint32(0) # unsigned long
        self.nextPtr = Ptr()
        self.prevPtr = Ptr()
        self.unk_f34 = np.uint(0)
        self.unk_f38 = np.uint(0)
        self.unk_f3c = np.uint(0)

        self._structSize = np.uint(0x40)

class grcIndexBuffer(datBase):
    def __init__(self):
        super().__init__()

        self.indexCount = np.uint32(0) # unsigned long
        self.indexData = Ptr()

class grcIndexBufferD3D(grcIndexBuffer):
    def __init__(self):
        super().__init__()

        self.indexBufferBuffer = Ptr()
        self.cacheHandle = ctypes.create_string_buffer(0x20)
        self.unk_f14 = np.uint(0)
        self.lockFlags = np.uint32(0) # unsigned long
        self.nextPtr = Ptr()
        self.prevPtr = Ptr()
        self.unk_f24 = np.uint(0)
        self.unk_f28 = np.uint(0)
        self.unk_f2c = np.uint(0)

        self._structSize = np.uint(0x30)

class rageVertexDeclaration:
    def __init__(self):
        self.usedElements = np.uint32(0) # unsigned long
        self.totalSize = np.ubyte(0)
        self.unk_f6 = np.ubyte(0)
        self.storeNormalsDataFirst = np.ubyte(0)
        self.elementsCount = np.ubyte(0)
        self.elementTypes = np.longlong(0)

class GrmModel(datBase):
    def __init__(self):
        super().__init__()

        self.geometries = SimpleCollection()
        self.bounds = Ptr()
        self.shaderMappings = Ptr()
        self.offsetCount = np.ubyte(0)
        self.skinned = np.ubyte(0)
        self.unk_f16 = np.ubyte(0)
        self.boneIndex = np.ubyte(0)
        self.unk_f18 = np.ubyte(0)
        self.haveOffsetCount = np.ubyte(0)
        self.shaderMappingCount = np.ushort(0)

        self._structSize = np.uint(0x1c)
        self._geometry : list = []
        self._bounds : list = []
        self._mtlIndex : list = []

class grmGeometry(datBase):
    def __init__(self):
        super().__init__()

        self.vertexDeclaration = Ptr()
        self.unk_f8 = np.uint(0)
        self.vertexBuffers : list = [] # Ptr
        for _ in range(0, 4):
            self.vertexBuffers.append(Ptr())
        self.indexBuffers : list = [] # Ptr
        for _ in range(0, 4):
            self.indexBuffers.append(Ptr())
        self.indexCount = np.uint32(0) # unsigned long
        self.faceCount = np.uint32(0) # unsigned long
        self.vertexCount = np.ushort(0)
        self.indicesPerFace = np.ushort(0)
        self.boneMapping = Ptr()
        self.vertexStride = np.ushort(0)
        self.boneCount = np.ushort(0)
        self._InstanceVertexDeclarationD3D = Ptr()
        self._InstanceVertexBufferD3D = Ptr()
        self._UseGlobalStreamIndex = np.uint32(0) # unsigned long

        self._structSize = np.uint(0x4c)
        self._usedBones : list = [] # np.ushort

class grmLodGroup:
    def __init__(self):
        self.center = Vector4()
        self.aabbMin = Vector4()
        self.aabbMax = Vector4()
        self.models : list = [0] * 4
        self.lodDist : list = [0.0] * 4
        self.shaderUseMask : list = [0] * 4
        self.radius = np.float32(0.0)
        #self.unk_f64 = ctypes.create_string_buffer(0xc)
        self.unk_f64_1 = np.float32(0.0) #TEMP?
        self.unk_f64_2 = np.float32(0.0) #TEMP?
        self.unk_f64_3 = np.float32(0.0) #TEMP?
        self.unk_f68 = np.float32(0.0)
        self.unk_f6c = np.float32(0.0)

class rmcDrawableBase(pgBase):
    def __init__(self):
        super().__init__()

        self.shaderGroup = Ptr()

class rmcDrawable(rmcDrawableBase):
    def __init__(self):
        super().__init__()

        self.skeleton = Ptr()
        self.lodGroup = grmLodGroup()

class Drawable(rmcDrawable):
    def __init__(self):
        super().__init__()

        self.lightAttrs = SimpleCollection()

        self._structSize = np.uint(0x88)
        self._model : list = []
        for _ in range(0, 4):
            self._model.append(SimpleCollection())
        self._modelPtr : list = [0] * 4

class VertexInfo:
    def __init__(self):
        self.position = Vector4()
        self.blendWeight : list = [0.0] * 4
        self.blendIndex : list = [0] * 4 # bone index
        self.normal = Vector4()
        self.color : list = [0] * 4
        self.specular : list = [0] * 4
        self.uv0 = Vector4()
        self.uv1 = Vector4()
        self.uv2 = Vector4()
        self.uv3 = Vector4()
        self.uv4 = Vector4()
        self.uv5 = Vector4()
        self.uv6 = Vector4()
        self.uv7 = Vector4()
        self.tangent = Vector4()
        self.binormal = Vector4()

        self._mtlIndex = np.ushort(0)
        self._vertexIndex = np.uint(0)

class Geometries:
    def __init__(self):
        self.mtlIndex = np.ushort(0)
        self.indices : list = []
        self.vertices : list = []
        self.usedBlendIndex : list = []
        self.vertexStride = np.uint(0)
        self.vertexFormat = np.uint(0)
        self.types = np.longlong(0)

class Meshes:
    def __init__(self):
        self.skinned = np.bool_(False)
        self.bounds : list = []
        self.boneIndex = np.ushort(0)
        self.geometry : list = []

class LodGroups:
    def __init__(self):
        self.meshes : list = []
        self.lodDist : list = []
