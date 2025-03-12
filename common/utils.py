# based on Liberty Four: https://gtaforums.com/topic/990530-relsrc-liberty-four

import numpy as np
import math

def GetHash(hashStr, toLowerCase):
    if (toLowerCase):
        hashStr = str.lower(hashStr)
    i = np.ulonglong(0)
    hash = np.uint32(0)
    while (i != len(hashStr)):
        hash += np.uint32(ord(hashStr[i]))
        hash += np.uint32(hash << 10)
        hash ^= np.uint32(hash >> 6)

        i += np.ulonglong(1)
    hash += np.uint32(hash << 3)
    hash ^= np.uint32(hash >> 11)
    hash += np.uint32(hash << 15)
    return hash

class Vector3:
    def __init__(self, x = 0.0, y = 0.0, z = 0.0):
        self.x = np.float32(x)
        self.y = np.float32(y)
        self.z = np.float32(z)

class Vector4:
    def __init__(self, x = 0.0, y = 0.0, z = 0.0, w = 0.0):
        self.x = np.float32(x)
        self.y = np.float32(y)
        self.z = np.float32(z)
        self.w = np.float32(w)

class Matrix:
    def __init__(self):
        self.m10 = np.float32(0.0)
        self.m11 = np.float32(0.0)
        self.m12 = np.float32(0.0)
        self.m13 = np.float32(0.0)
        self.m20 = np.float32(0.0)
        self.m21 = np.float32(0.0)
        self.m22 = np.float32(0.0)
        self.m23 = np.float32(0.0)
        self.m30 = np.float32(0.0)
        self.m31 = np.float32(0.0)
        self.m32 = np.float32(0.0)
        self.m33 = np.float32(0.0)
        self.m40 = np.float32(0.0)
        self.m41 = np.float32(0.0)
        self.m42 = np.float32(0.0)
        self.m43 = np.float32(0.0)

    def GetEulerAngles(self, quat : Vector4):
        w2 = np.float64(quat.w * quat.w)
        x2 = np.float64(quat.x * quat.x)
        y2 = np.float64(quat.y * quat.y)
        z2 = np.float64(quat.z * quat.z)
        unitLength = np.float64(w2 + x2 + y2 + z2)
        abcd = np.float64(quat.w * quat.x + quat.y * quat.z)
        eps = np.float64(1e-7)

        if (abcd > (0.5 - eps) * unitLength):
            return Vector3(0, math.pi, 2 * math.atan2(quat.y, quat.w))
        elif (abcd < (-0.5 + eps) * unitLength):
            return Vector3(0, -math.pi, -2 * math.atan2(quat.y, quat.w))
        else:
            adbc = np.float64(quat.w * quat.z - quat.x * quat.y)
            acbd = np.float64(quat.w * quat.y - quat.x * quat.z)
            x = np.float32(math.atan2(2 * acbd, 1 - 2 * (y2 + x2)))
            y = np.float32(math.asin(2 * abcd / unitLength))
            z = np.float32(math.atan2(2 * adbc, 1 - 2 * (z2 + x2)))
            return Vector3(x, y, z)

    def SetRotation(self, rot : Vector3, clear = False):
        if (clear):
            self.m10 = np.float32(0.0)
            self.m11 = np.float32(0.0)
            self.m12 = np.float32(0.0)
            self.m13 = np.float32(0.0)
            self.m20 = np.float32(0.0)
            self.m21 = np.float32(0.0)
            self.m22 = np.float32(0.0)
            self.m23 = np.float32(0.0)
            self.m30 = np.float32(0.0)
            self.m31 = np.float32(0.0)
            self.m32 = np.float32(0.0)
            self.m33 = np.float32(0.0)
            self.m40 = np.float32(0.0)
            self.m41 = np.float32(0.0)
            self.m42 = np.float32(0.0)
            self.m43 = np.float32(0.0)

        tmp = np.float32([0.0] * 3)
        tmp[0] = math.cos(rot.y)
        if (tmp[0] > math.cos(rot.z)):
            tmp[0] = math.cos(rot.z)
        elif (tmp[0] > math.cos(rot.y)):
            tmp[0] = math.cos(rot.y)
        rightScale = np.float32(float(tmp[0] * 1))

        tmp[1] = math.cos(rot.x)
        if (tmp[1] > math.cos(rot.z)):
            tmp[1] = math.cos(rot.z)
        elif (tmp[1] > math.cos(rot.x)):
            tmp[1] = math.cos(rot.x)
        upScale = np.float32(float(tmp[1] * 1))

        tmp[2] = math.cos(rot.x)
        if (tmp[2] > math.cos(rot.y)):
            tmp[2] = math.cos(rot.y)
        elif (tmp[2] > math.cos(rot.x)):
            tmp[2] = math.cos(rot.x)
        atScale = np.float32(float(tmp[2] * 1)) # forward

        self.m10 = np.float32(rightScale)
        self.m11 = np.float32(-math.sin(rot.z))
        self.m12 = np.float32(math.sin(rot.y))

        self.m20 = np.float32(math.sin(rot.z))
        self.m21 = np.float32(upScale)
        self.m22 = np.float32(-math.sin(rot.x))

        self.m30 = np.float32(-math.sin(rot.y))
        self.m31 = np.float32(math.sin(rot.x))
        self.m32 = np.float32(atScale)

    def SetRotationFromQuaternion(self, quat, clear = False):
        self.SetRotation(self.GetEulerAngles(quat), clear)
