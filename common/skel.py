# based on Liberty Four: https://gtaforums.com/topic/990530-relsrc-liberty-four

import numpy as np

from .base import datBase, Ptr, SimpleCollection
from .utils import Vector3, Vector4

class Bone:
    def __init__(self):
        self.name = np.str_('')
        self.flags : list = []
        self.index = np.ushort(0)
        self.id = np.ushort(0)
        self.mirror = np.ushort(0)
        self.localOffset = Vector3()
        self.rotationEuler = Vector3()
        self.rotationQuaternion = Vector4()
        self.scale = Vector3()
        self.worldOffset = Vector3()
        self.orient = Vector3()
        self.sorient = Vector3()
        self.transMin = Vector3()
        self.transMax = Vector3()
        self.rotMin = Vector3()
        self.rotMax = Vector3()
        self.posInTheHierarchy = np.int64(0) # long

class Skel:
    def __init__(self):
        self.filePath = np.str_('')
        self.boneCount = np.ushort(0)
        self.flags : list = []
        self.bone : list = []

class crJointDataFile(datBase):
    def __init__(self):
        super().__init__()

        self.jointData = SimpleCollection()

class crSkeletonData:
    def __init__(self):
        self.bones = Ptr()
        self.parentBoneIndices = Ptr()
        self.boneWorldOrient = Ptr()
        self.boneWorldOrientInverted = Ptr()
        self.boneLocalTransforms = Ptr()
        self.boneCount = np.ushort(0)
        self.transLockCount = np.ushort(0)
        self.rotLockCount = np.ushort(0)
        self.scaleLockCount = np.ushort(0)
        self.flags = np.int32(0)
        self.boneIdMappings = SimpleCollection()
        self.usageCount = np.short(0)
        self.unk_f2a = np.short(0)
        self.CRC = np.uint(0)
        self.jointDataFileName = Ptr()
        self.jointDataFile = crJointDataFile()

        self._structSize = np.uint(0x40)
        self._flags : list = []

class crBone:
    def __init__(self):
        self.name = Ptr()
        self.flags = np.uint(0)
        self.parallelOnHierarchy = Ptr()
        self.nextOnHierarchy = Ptr()
        self.pastOnHierarchy = Ptr()
        self.boneIndex = np.ushort(0)
        self.boneId = np.ushort(0)
        self.mirror = np.ushort(0)
        self.transFlags = np.ubyte(0)
        self.rotFlags = np.ubyte(0)
        self.scaleFlags = np.ubyte(0)
        self.unk_f1d = np.ubyte(0)
        self.unk_f1e = np.ubyte(0)
        self.unk_f1f = np.ubyte(0)
        self.offset = Vector3()
        self.hash = np.uint(0)
        self.rotationEuler = Vector4()
        self.rotationQuaternion = Vector4()
        self.scale = Vector3()
        self.unk_f5c = np.uint(0)
        self.parentModelOffset = Vector4()
        self.orient = Vector4()
        self.sorient = Vector4()
        self.transMin = Vector4()
        self.transMax = Vector4()
        self.rotMin = Vector4()
        self.rotMax = Vector4()
        self.jointData = Ptr()
        self.unk_fD4 = np.uint(0)
        self.unk_fD8 = np.uint(0)
        self.unk_fDC = np.uint(0)

        self._structSize = np.uint(0xe0)
        self._boneOffset = np.uint(0)
        self._name = np.str_('')
        self._flags : list = []
