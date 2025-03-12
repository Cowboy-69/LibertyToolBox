# based on Liberty Four: https://gtaforums.com/topic/990530-relsrc-liberty-four

import numpy as np

class Layout:
    def __init__(self):
        self.size = []
        self.usedPointer = [0]
        self.usedObject = [0]
        self.pointer = [0]
        self.bigObjIndex = [0]
        self.bigObjSize = [0]

    def CreateLayout(self, startPos : np.uint, flags, blockType : np.uint):
        count = len(self.size)
        self.usedPointer = [0] * count
        self.usedObject = [False] * count
        self.pointer = [0] * count
        self.bigObjIndex = -1
        self.bigObjSize = 0
        pos = startPos

        pageSize = 0

        if (blockType == 5):
            for i in range(0, count):
                if (flags.GetSizeVPage0() < self.size[i]):
                    while (flags.GetSizeVPage0() < self.size[i]):
                        flags.SetVSize(flags.GetVSize() + 1)

            pageSize = flags.GetSizeVPage0()
        elif (blockType == 6):
            for i in range(0, count):
                if (flags.GetSizePPage0() < self.size[i]):
                    while (flags.GetSizePPage0() < self.size[i]):
                        flags.SetPSize(flags.GetPSize() + 1)
                
            pageSize = flags.GetSizePPage0()

        while (not self.AllBoolsUsed(self.usedObject, count)):
            for i in range(0, count):
                if (self.size[i] > self.bigObjSize and not self.usedObject[i] and self.CheckPos(self.size[i], pageSize, pos)):
                    self.bigObjSize = self.size[i]
                    self.bigObjIndex = i

            if (self.bigObjIndex != -1):
                self.pointer[self.bigObjIndex] = pos
                self.usedObject[self.bigObjIndex] = True
                pos += self.AlignValue(self.bigObjSize, 16)
                self.bigObjIndex = -1
                self.bigObjSize = 0
            else:
                if (self.AllBoolsUsed(self.usedObject, count)):
                    break
                else:
                    pos = self.AlignValue(pos, pageSize)

        highPos = 0
        highIndex = -1
        for i in range(0, count):
            if (self.pointer[i] >= highPos):
                highPos = self.pointer[i]
                highIndex = i
        blockEnd = highPos
        blockEnd += self.size[highIndex]

        while (True):
            if (blockType == 5):
                while (flags.GetTotalVSize() < blockEnd):
                    if (flags.GetVPage0() == 127):
                        flags.SetVSize(flags.GetVSize() + 1)
                    else:
                        flags.SetVPage0(flags.GetVPage0() + 1)
            elif (blockType == 6):
                while (flags.GetTotalPSize() < blockEnd):
                    if (flags.GetPPage0() == 127):
                        flags.SetPSize(flags.GetPSize() + 1)
                    else:
                        flags.SetPPage0(flags.GetPPage0() + 1)
            break

        usedBytesInLastPage = 0
        pagesSize = [0] * 5
        if (blockType == 5):
            usedBytesInLastPage = blockEnd % flags.GetSizeVPage0()
            if (flags.GetTotalVSize() == blockEnd):
                usedBytesInLastPage = flags.GetSizeVPage0()
            pagesSize[0] = flags.GetSizeVPage0()
        elif (blockType == 6):
            usedBytesInLastPage = blockEnd % flags.GetSizePPage0()
            if (flags.GetTotalPSize() == blockEnd):
                usedBytesInLastPage = flags.GetSizePPage0()
            pagesSize[0] = flags.GetSizePPage0()

        pagesSize[1] = int(pagesSize[0] / 2)
        pagesSize[2] = int(pagesSize[0] / 4)
        pagesSize[3] = int(pagesSize[0] / 8)
        pagesSize[4] = int(pagesSize[0] / 16)

        usedPages = [False] * 5

        if (usedBytesInLastPage <= pagesSize[1] + pagesSize[2] + pagesSize[3] + pagesSize[4]):
            if (blockType == 5):
                flags.SetVPage0(flags.GetVPage0() - 1)
            elif (blockType == 6):
                flags.SetPPage0(flags.GetPPage0() - 1)
            for i in range(4, -1, -1):
                if (pagesSize[i] >= usedBytesInLastPage):
                    usedPages[i] = True
                    break
            
            if (blockType == 5):
                if (usedPages[0]):
                    flags.SetVPage0(flags.GetVPage0() + 1)
                elif (usedPages[1]):
                    flags.SetVPage1(1)
                elif (usedPages[2]):
                    flags.SetVPage2(1)
                elif (usedPages[3]):
                    flags.SetVPage3(1)
                elif (usedPages[4]):
                    flags.SetVPage4(1)
            elif (blockType == 6):
                if (usedPages[0]):
                    flags.SetPPage0(flags.GetPPage0() + 1)
                elif (usedPages[1]):
                    flags.SetPPage1(1)
                elif (usedPages[2]):
                    flags.SetPPage2(1)
                elif (usedPages[3]):
                    flags.SetPPage3(1)
                elif (usedPages[4]):
                    flags.SetPPage4(1)

        return flags
    
    def Add(self, value):
        if (type(value) is str):
            self.size.append(len(value) + 1)
        else:
            self.size.append(value)

    def GetPos(self, objSize):
        count = len(self.size)

        offset = 0

        for i in range(0, count):
            if (type(objSize) is np.str_):
                if (self.size[i] == len(objSize) + 1 and not self.usedPointer[i]):
                    offset = self.pointer[i]
                    self.usedPointer[i] = 1
                    return offset
            else:
                if (self.size[i] == objSize and not self.usedPointer[i]):
                    offset = self.pointer[i]
                    self.usedPointer[i] = 1
                    return offset
                
        return 0

    def AllBoolsUsed(self, array, count):
        for i in range(0, count):
            if (array[i] == False):
                return False
        return True

    def CheckPos(self, objectSize, pageSize, pos):
        val = True
        if (objectSize + (pos % pageSize) > pageSize):
            val = False
        return val

    def AlignValue(self, a, b):
        if (a % b != 0):
            a += (b - (a % b)) % b
        return np.int32(a)
