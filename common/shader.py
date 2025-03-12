# based on Liberty Four: https://gtaforums.com/topic/990530-relsrc-liberty-four

import numpy as np

from .base import datBase, pgBase, Ptr, SimpleCollection

class Shaders:
    def __init__(self):
        self.preset = np.str_('')
        self.name = np.str_('')

class ShaderGroup(datBase):
    def __init__(self):
        super().__init__()

        self.texture = Ptr()
        self.shaders = SimpleCollection()
        self.unk_f10 = SimpleCollection()
        self.unk_f18 = SimpleCollection()
        self.unk_f20 = SimpleCollection()
        self.unk_f28 = SimpleCollection()
        self.unk_f30 = SimpleCollection()
        self.unk_f38 = SimpleCollection()
        self.vertexFormat = SimpleCollection()
        self.indexMapping = SimpleCollection()
        
        self._structSize = np.uint(0x50)
        self._shader : list = [] # Ptr
        self._index : list = [] # np.uint
        self._vertexFormat : list = [] # np.uint

class grmShaderEffect:
    def __init__(self):
        self.parameters = Ptr()
        self.cachedEffect = Ptr()
        self.parameterCount = np.uint32(0) # unsigned long
        self.effectSize = np.uint(0)
        self.parameterTypes = Ptr()
        self.hash = np.uint32(0) # fxc file hash (unsigned long)
        self.unkf18 = np.uint(0)
        self.unkf1c = np.uint(0)
        self.paramsHash = Ptr()
        self.unkf24 = np.uint(0)
        self.unkf28 = np.uint(0)
        self.unkf2c = np.uint(0)

class grmShader(pgBase):
    def __init__(self):
        super().__init__()

        self.unk_f8 = np.ubyte(0)
        self.drawBucket = np.ubyte(0)
        self.unk_fa = np.ubyte(0)
        self.unk_fb = np.ubyte(0)
        self.unk_fc = np.ushort(0)
        self.index = np.ushort(0)
        self.unk_f10 = np.uint32(0) # unsigned long
        self.effect = grmShaderEffect()

class ShaderFX(grmShader):
    def __init__(self):
        super().__init__()

        self.name = Ptr()
        self.spsName = Ptr()
        self.unk_f4c = np.uint(0)
        self.unk_f50 = np.uint(0)
        self.unk_f54 = np.uint(0)
        self.unk_f58 = np.uint(0)
        
        self._structSize = np.uint(0x5c)
        self._name = np.str_("")
        self._sps = np.str_("")
        self._parameter : list = [] # Ptr
        self._type : list = [] # np.ubyte
        self._paramHash : list = [] # np.uint
