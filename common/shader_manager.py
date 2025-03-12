# based on Liberty Four: https://gtaforums.com/topic/990530-relsrc-liberty-four

import os
import numpy as np
import xml.etree.ElementTree as ETxml

import addon_utils

from .base import SetBit, GetValueFromBits

class ShaderManager:
    class ShaderInfoParam:
        def __init__(self):
            self.type = np.str_('')
            self.name = np.str_('')
            self.custom = np.bool_(False)
            self.staticValue : list = [np.str_("null")]

    class ShaderElement:
        def __init__(self):
            self.usage = np.str_('')
            self.type = np.str_('')

    class ShaderInfo:
        def __init__(self):
            self.preset = np.str_('')
            self.index = np.int32(0)
            self.name = np.str_('')
            self.vertexFormat = np.uint32(0)
            self.drawBucket = np.int32(0)
            self.blockSize = np.int32(0)
            self.skinned = np.bool_(False)
            self.elementTypes = np.longlong(0)
            self.param : list = []
            self.element : list = []

    def ReadShaderManager():
        filePath = ""

        for mod in addon_utils.modules():
            if mod.bl_info['name'] == "LibertyToolBox":
                filePath = os.path.dirname(mod.__file__)

        tree = ETxml.parse(filePath + "\\ShaderManager.xml")
        #tree = ETxml.parse("ShaderManager.xml") ### testing
        
        root = tree.getroot()
        
        manager = []

        shaderIndex = 0
        for shader in root:
            manager.append(ShaderManager.ShaderInfo())
            for value in shader:
                if (value.tag == "Preset"):
                    manager[shaderIndex].preset = value.text
                if (value.tag == "Index"):
                    manager[shaderIndex].index = int(value.text)
                if (value.tag == "Name"):
                    manager[shaderIndex].name = value.text
                if (value.tag == "DrawBucket"):
                    manager[shaderIndex].drawBucket = int(value.text)
                if (value.tag == "BlockSize"):
                    manager[shaderIndex].blockSize = int(value.text)
                if (value.tag == "Skinned"):
                    manager[shaderIndex].skinned = bool(value.text)
                
                if (value.tag == "Params"):
                    paramIndex = 0
                    for params in value:
                        manager[shaderIndex].param.append(ShaderManager.ShaderInfoParam())
                        manager[shaderIndex].param[paramIndex].custom = True
                        if (params.tag == "Item"):
                            for item in params:
                                if (item.tag == "Type"):
                                    manager[shaderIndex].param[paramIndex].type = item.text
                                if (item.tag == "Name"):
                                    manager[shaderIndex].param[paramIndex].name = item.text
                                if (item.tag == "StaticValue"):
                                    manager[shaderIndex].param[paramIndex].custom = False
                                    manager[shaderIndex].param[paramIndex].staticValue = item.text.split(";")

                            paramIndex += 1

                if (value.tag == "Elements"):
                    elementIndex = 0
                    for elements in value:
                        manager[shaderIndex].element.append(ShaderManager.ShaderElement())
                        if (elements.tag == "Item"):
                            for item in elements:
                                if (item.tag == "Usage"):
                                    manager[shaderIndex].element[elementIndex].usage = item.text
                                    
                                    if (item.text == "position"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 0, 1, 1)
                                    elif (item.text == "blendWeight"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 1, 1, 1)
                                    elif (item.text == "blendIndex"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 2, 1, 1)
                                    elif (item.text == "normal"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 3, 1, 1)
                                    elif (item.text == "color"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 4, 1, 1)
                                    elif (item.text == "specular"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 5, 1, 1)
                                    elif (item.text == "texCoord0"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 6, 1, 1)
                                    elif (item.text == "texCoord1"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 7, 1, 1)
                                    elif (item.text == "texCoord2"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 8, 1, 1)
                                    elif (item.text == "texCoord3"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 9, 1, 1)
                                    elif (item.text == "texCoord4"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 10, 1, 1)
                                    elif (item.text == "texCoord5"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 11, 1, 1)
                                    elif (item.text == "texCoord6"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 12, 1, 1)
                                    elif (item.text == "texCoord7"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 13, 1, 1)
                                    elif (item.text == "tangent"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 14, 1, 1)
                                    elif (item.text == "binormal"):
                                        manager[shaderIndex].vertexFormat = SetBit(manager[shaderIndex].vertexFormat, 15, 1, 1)
                                    
                                if (item.tag == "Type"):
                                    manager[shaderIndex].element[elementIndex].type = item.text
                                    elementType = 0
                                    if (item.text == "float16"):
                                        elementType = 0
                                    elif (item.text == "float16_2"):
                                        elementType = 1
                                    elif (item.text == "float16_3"):
                                        elementType = 2
                                    elif (item.text == "float16_4"):
                                        elementType = 3
                                    elif (item.text == "float"):
                                        elementType = 4
                                    elif (item.text == "float2"):
                                        elementType = 5
                                    elif (item.text == "float3"):
                                        elementType = 6
                                    elif (item.text == "float4"):
                                        elementType = 7
                                    elif (item.text == "ubyte4"):
                                        elementType = 8
                                    elif (item.text == "d3dcolor"):
                                        elementType = 9
                                    elif (item.text == "dec3n"):
                                        elementType = 10
                                    elif (item.text == "ushort2"):
                                        elementType = 14

                                    if (manager[shaderIndex].element[elementIndex].usage == "position"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 0, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "blendWeight"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 4, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "blendIndex"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 8, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "normal"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 12, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "color"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 16, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "specular"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 20, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "texCoord0"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 24, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "texCoord1"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 28, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "texCoord2"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 32, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "texCoord3"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 36, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "texCoord4"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 40, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "texCoord5"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 44, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "texCoord6"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 48, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "texCoord7"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 52, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "tangent"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 56, elementType, 0x4)
                                    elif (manager[shaderIndex].element[elementIndex].usage == "binormal"):
                                        manager[shaderIndex].elementTypes = SetBit(manager[shaderIndex].elementTypes, 60, elementType, 0x4)

                            elementIndex += 1

            shaderIndex += 1

        return manager

    def GetStride(elementTypes, vertexFormat):
        stride = 0
        for i in range(0, 16):
            if (GetValueFromBits(vertexFormat, 1, i) != 0):
                type = GetValueFromBits(elementTypes, 4, i * 4)
                if (type == 0):
                    stride += 2
                elif (type == 1):
                    stride += 4
                elif (type == 2):
                    stride += 6
                elif (type == 3):
                    stride += 8
                elif (type == 4):
                    stride += 4
                elif (type == 5):
                    stride += 8
                elif (type == 6):
                    stride += 12
                elif (type == 7):
                    stride += 16
                elif (type == 8):
                    stride += 4
                elif (type == 9):
                    stride += 4
                elif (type == 10):
                    stride += 4
                elif (type == 14):
                    stride += 4
        return stride
    
    def GetShaderIndex(manager, preset):
        for i in range(0, len(manager)):
            if (manager[i].preset == preset):
                return i
