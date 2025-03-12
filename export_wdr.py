# based on Liberty Four: https://gtaforums.com/topic/990530-relsrc-liberty-four

import struct
import zlib
import numpy as np
import ctypes
import math

import bpy
import bmesh
from mathutils import Vector

from .common.utils import GetHash, Vector3, Vector4, Matrix
from .common.base import VirtualTables, RSC5Flag, datBase, pgBase, Ptr, SimpleCollection, pgDictionary, SetBit, GetValueFromBits
from .common.shader_manager import ShaderManager
from .common.layout import Layout
from .common.shader import Shaders, ShaderFX, ShaderGroup, grmShaderEffect, grmShader
from .common.skel import crBone, crSkeletonData, crJointDataFile, Skel, Bone
from .common.lod_group import Drawable, LodGroups, Meshes, Geometries, VertexInfo
from .common.lod_group import grmGeometry, GrmModel, rageVertexDeclaration, grcIndexBufferD3D, grcIndexBuffer, grcVertexBufferD3D, grcVertexBuffer
from .common.texture import grcTextureReference, grcTextureReferenceBase, grcTexturePC
from .common.texture_dds import TextureDDS, PixelFormatDDS, PixelFormatTypes

class ObjectInfo:
    def __init__(self):
        self.shaders = []

        self.textures = []

        self.skel = Skel()

        self.lodGroups = []
        for _ in range(0, 4):
            self.lodGroups.append(LodGroups())

class TextureInfo:
    def __init__(self):
        self.filePath = np.str_()
        self.fileName = np.str_()
        self.texture = 0

class Exporter:
    shaderManager = []

    blenderCollections = []
    blenderMeshes = []
    blenderEmpties = []
    blenderArmature = 0
    blenderBones = []

    objectInfo = ObjectInfo()

    textureDictionary = pgDictionary()

    flags = RSC5Flag()

    cpuLayout = Layout()
    gpuLayout = Layout()

    drawable = Drawable()
    shaderGroup = ShaderGroup()
    shaderFX : list = []

def start_export(options):
    Exporter.blenderCollections = []
    Exporter.blenderMeshes = []
    Exporter.blenderEmpties = []
    Exporter.blenderArmature = 0
    Exporter.blenderBones = []

    Exporter.objectInfo = ObjectInfo()

    Exporter.textureDictionary = pgDictionary()

    Exporter.flags = RSC5Flag()

    Exporter.cpuLayout = Layout()
    Exporter.gpuLayout = Layout()

    Exporter.drawable = Drawable()
    Exporter.shaderGroup = ShaderGroup()
    Exporter.shaderFX = []

    #####################################################################
    ###################### Data collection section ######################
    #####################################################################

    # Counting the number of Blender objects in the active collection
    totalBlenderMeshes = 0
    totalBlenderEmpties = 0
    totalBlenderArmatures = 0
    for blenderObject in bpy.context.collection.objects:
        if (blenderObject.type == "MESH"):
            totalBlenderMeshes += 1
        elif (blenderObject.type == "EMPTY"):
            totalBlenderEmpties += 1
        elif (blenderObject.type == "ARMATURE"):
            totalBlenderArmatures += 1

    if (totalBlenderArmatures > 1 or totalBlenderArmatures > 0 and totalBlenderEmpties > 0):
        return "ERROR_NOTHING"

    Exporter.blenderEmpties = [0] * totalBlenderEmpties

    # Put Blender objects from the active collection into variables
    currentMeshIndex = 0
    currentEmptyIndex = 0
    previousTotalEmptyParents = 0
    for blenderObject in bpy.context.collection.objects:
        if (blenderObject.type == "MESH"):
            if (len(blenderObject.material_slots) == 0):
                continue

            if (blenderObject.hide_get()):
                continue

            #TODO LOD levels
            if (currentMeshIndex > 0):
                continue
            
            Exporter.blenderMeshes.append(blenderObject)

            currentMeshIndex += 1
        elif (blenderObject.type == "EMPTY"):
            if (blenderObject.hide_get()):
                continue

            #TEMP!
            if (blenderObject.libertytool_bone.index == -1):
                totalEmptyParents = 0
                totalEmptyChildren = len(blenderObject.children)
                if (blenderObject.parent):
                    currentParent = blenderObject.parent
                    totalEmptyParents += 1
                    while (True):
                        if (currentParent.parent):
                            currentParent = currentParent.parent
                            totalEmptyParents += 1
                        else:
                            break

                if (previousTotalEmptyParents != totalEmptyParents):
                    currentEmptyIndex = 0
                    previousTotalEmptyParents = totalEmptyParents

                Exporter.blenderEmpties[totalEmptyParents + currentEmptyIndex] = blenderObject
            else:
                Exporter.blenderEmpties[blenderObject.libertytool_bone.index] = blenderObject
            
            currentEmptyIndex += 1
        elif (blenderObject.type == "ARMATURE"):
            if (blenderObject.hide_get()):
                continue

            Exporter.blenderArmature = blenderObject

    if (len(Exporter.blenderMeshes) == 0 and len(Exporter.blenderEmpties) == 0 and Exporter.blenderArmature == 0):
        return "ERROR_NOTHING"
    
    if (not Exporter.shaderManager):
        Exporter.shaderManager = ShaderManager.ReadShaderManager()

    # Blender AABB
    Exporter.drawable.lodGroup.aabbMin.x = Exporter.blenderMeshes[0].bound_box[0][0]
    Exporter.drawable.lodGroup.aabbMin.y = Exporter.blenderMeshes[0].bound_box[0][1]
    Exporter.drawable.lodGroup.aabbMin.z = Exporter.blenderMeshes[0].bound_box[0][2]
    Exporter.drawable.lodGroup.aabbMax.x = Exporter.blenderMeshes[0].bound_box[6][0]
    Exporter.drawable.lodGroup.aabbMax.y = Exporter.blenderMeshes[0].bound_box[6][1]
    Exporter.drawable.lodGroup.aabbMax.z = Exporter.blenderMeshes[0].bound_box[6][2]

    # Blender bound center
    boxCenter = 0.125 * sum((Vector(bound) for bound in Exporter.blenderMeshes[0].bound_box), Vector())
    Exporter.drawable.lodGroup.center.x = boxCenter.x
    Exporter.drawable.lodGroup.center.y = boxCenter.y
    Exporter.drawable.lodGroup.center.z = boxCenter.z

    # Blender bound radius
    #TEMP?
    aabbMin = Vector3(Exporter.drawable.lodGroup.aabbMin.x, Exporter.drawable.lodGroup.aabbMin.y, Exporter.drawable.lodGroup.aabbMin.z)
    aabbMax = Vector3(Exporter.drawable.lodGroup.aabbMax.x, Exporter.drawable.lodGroup.aabbMax.y, Exporter.drawable.lodGroup.aabbMax.z)
    distanceBetweenAABB = Vector3()
    distanceBetweenAABB.x = aabbMin.x - aabbMax.x
    distanceBetweenAABB.y = aabbMin.y - aabbMax.y
    distanceBetweenAABB.z = aabbMin.z - aabbMax.z
    Exporter.drawable.lodGroup.radius = math.sqrt(distanceBetweenAABB.x * distanceBetweenAABB.x + 
                                         distanceBetweenAABB.y * distanceBetweenAABB.y +
                                         distanceBetweenAABB.z * distanceBetweenAABB.z)
    
    materialNames = []

    # Blender meshes
    #TODO lodGroups[i].meshes[k].geometry[k]
    for i in range(0, len(Exporter.blenderMeshes)):
        originalBlenderMesh = Exporter.blenderMeshes[i]

        Exporter.objectInfo.lodGroups[i].meshes.append(Meshes())

        # Is it skinned?
        for modifier in Exporter.blenderMeshes[i].modifiers:
            if (modifier.type != "ARMATURE"):
                continue

            Exporter.objectInfo.lodGroups[i].meshes[0].skinned = True

            break

        # General mesh bound
        bound = Vector4()
        bound.x = Exporter.drawable.lodGroup.center.x
        bound.y = Exporter.drawable.lodGroup.center.y
        bound.z = Exporter.drawable.lodGroup.center.z
        bound.w = Exporter.drawable.lodGroup.radius #TEMP?
        Exporter.objectInfo.lodGroups[i].meshes[0].bounds.append(bound)

        materialSlotSize = len(originalBlenderMesh.material_slots)

        # Fill the list of geometries based on the number of material slots
        for j in range(0, materialSlotSize):
            Exporter.objectInfo.lodGroups[i].meshes[0].geometry.append(Geometries())

        bm = bmesh.new()

        # Triangulate Blender mesh faces
        bm.from_mesh(originalBlenderMesh.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(originalBlenderMesh.data)

        bm.free()

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        for blenderObject in bpy.context.selected_objects:
            blenderObject.select_set(False)

        # Select mesh object
        bpy.context.view_layer.objects.active = originalBlenderMesh
        bpy.context.view_layer.objects.active.select_set(True)

        # Duplicate mesh object
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.duplicate(linked=False)

        if (options["modifyGeometry"]):
            # In WDR files, UV information is stored in vertices (per vertex UV), while in Blender it is stored in loops.
            # Therefore, we use this trick to place the UVs correctly later on
            
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.tris_convert_to_quads()
            bpy.ops.mesh.mark_sharp()
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            #bpy.ops.mesh.quads_convert_to_tris(quad_method='FIXED', ngon_method='CLIP')

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.modifier_add(type="EDGE_SPLIT")
            bpy.ops.object.modifier_apply(modifier="EdgeSplit")

        duplicatedBlenderMesh = bpy.context.view_layer.objects.active
        duplicatedBlenderMesh.select_set(True)

        # In WDR files, materials have each vertex index starting at zero, and Blender doesn't take this into account.
        # Therefore, we use this trick to properly place geometry information, as well as material bounds later on.
        # Separate the mesh by material
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.separate(type='MATERIAL')
        bpy.ops.object.mode_set(mode='OBJECT')

        #try:
        for j in range(0, materialSlotSize):
            materialNames.append(originalBlenderMesh.material_slots[j].name)

        mtlIndex = 0
        for j in range(0, materialSlotSize):
            selectedObject = bpy.context.selected_objects[j]

            for blenderObject in bpy.context.selected_objects:
                if (blenderObject.material_slots[0].name != materialNames[j]):
                    continue

                selectedObject = blenderObject

            Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].mtlIndex = mtlIndex

            # Calculate tangents
            selectedObject.data.calc_tangents()

            # Material bound
            # Blender AABB
            aabbMin = Vector3()
            aabbMin.x = selectedObject.bound_box[0][0]
            aabbMin.y = selectedObject.bound_box[0][1]
            aabbMin.z = selectedObject.bound_box[0][2]
            aabbMax = Vector3()
            aabbMax.x = selectedObject.bound_box[6][0]
            aabbMax.y = selectedObject.bound_box[6][1]
            aabbMax.z = selectedObject.bound_box[6][2]

            # Blender bound center
            boxCenter = 0.125 * sum((Vector(bound) for bound in selectedObject.bound_box), Vector())
            center = Vector3()
            center.x = boxCenter.x
            center.y = boxCenter.y
            center.z = boxCenter.z

            # Blender bound radius
            #TEMP?
            distanceBetweenAABB = Vector3()
            distanceBetweenAABB.x = aabbMin.x - aabbMax.x
            distanceBetweenAABB.y = aabbMin.y - aabbMax.y
            distanceBetweenAABB.z = aabbMin.z - aabbMax.z
            radius = math.sqrt(distanceBetweenAABB.x * distanceBetweenAABB.x + 
                                                distanceBetweenAABB.y * distanceBetweenAABB.y +
                                                distanceBetweenAABB.z * distanceBetweenAABB.z)

            # Material bound
            if (materialSlotSize > 1):
                bound = Vector4()
                bound.x = center.x
                bound.y = center.y
                bound.z = center.z
                bound.w = radius
                Exporter.objectInfo.lodGroups[i].meshes[0].bounds.append(bound)

            # Vertices
            for vertexID, vertex in enumerate(selectedObject.data.vertices):
                vertexInfo = VertexInfo()

                vertexInfo.position.x = vertex.co.x
                vertexInfo.position.y = vertex.co.y
                vertexInfo.position.z = vertex.co.z

                Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices.append(vertexInfo)

                # Vertex weights from vertex groups
                if (Exporter.objectInfo.lodGroups[i].meshes[0].skinned):
                    groupID = 0
                    for mainVertexGroup in selectedObject.vertex_groups:
                        group_index = mainVertexGroup.index

                        if group_index in [i.group for i in vertex.groups]:
                            for boneID, bone in enumerate(Exporter.blenderArmature.data.bones):
                                if (bone.name != mainVertexGroup.name):
                                    continue

                                Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID].blendIndex[groupID] = boneID

                                if (boneID not in Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].usedBlendIndex):
                                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].usedBlendIndex.append(np.ushort(boneID))

                                break

                            weight = vertex.groups[[vertGroup.group for vertGroup in vertex.groups].index(group_index)].weight

                            Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID].blendWeight[groupID] = weight

                            groupID += 1

            # Sort blendWeight and blendIndex by weights in ascending order
            if (Exporter.objectInfo.lodGroups[i].meshes[0].skinned):
                for vertexID in range(0, len(Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices)):
                    vertexInfo = Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID]

                    weights, indices = zip(*sorted(zip(vertexInfo.blendWeight, vertexInfo.blendIndex), reverse=True))
                    
                    weights = list(weights) # from tuple to list
                    indices = list(indices) # from tuple to list
                    
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID].blendWeight[0] = weights[2] # Swap the first and third values
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID].blendWeight[1] = weights[1]
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID].blendWeight[2] = weights[0] # Swap the first and third values
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID].blendWeight[3] = weights[3]
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID].blendIndex[0] = indices[2] # Swap the first and third values
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID].blendIndex[1] = indices[1]
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID].blendIndex[2] = indices[0] # Swap the first and third values
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[vertexID].blendIndex[3] = indices[3]

            # Loops
            currentLoopIndex = 0
            for loop in selectedObject.data.loops:
                Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].indices.append(loop.vertex_index)

                # Vertex UV
                for layerID, uv_layer in enumerate(selectedObject.data.uv_layers):
                    if (layerID == 0):
                        #Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv0.x = selectedObject.data.uv_layers[0].uv[loop.index].vector.x
                        #Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv0.y = -selectedObject.data.uv_layers[0].uv[loop.index].vector.y

                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv0.x = uv_layer.data[loop.index].uv.x
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv0.y = -uv_layer.data[loop.index].uv.y
                    elif (layerID == 1):
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv1.x = uv_layer.data[loop.index].uv.x
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv1.y = -uv_layer.data[loop.index].uv.y
                    elif (layerID == 2):
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv2.x = uv_layer.data[loop.index].uv.x
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv2.y = -uv_layer.data[loop.index].uv.y
                    elif (layerID == 3):
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv3.x = uv_layer.data[loop.index].uv.x
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv3.y = -uv_layer.data[loop.index].uv.y
                    elif (layerID == 4):
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv4.x = uv_layer.data[loop.index].uv.x
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv4.y = -uv_layer.data[loop.index].uv.yy
                    elif (layerID == 5):
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv5.x = uv_layer.data[loop.index].uv.x
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv5.y = -uv_layer.data[loop.index].uv.yy
                    elif (layerID == 6):
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv6.x = uv_layer.data[loop.index].uv.x
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv6.y = -uv_layer.data[loop.index].uv.yy
                    elif (layerID == 7):
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv7.x = uv_layer.data[loop.index].uv.x
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].uv7.y = -uv_layer.data[loop.index].uv.y

                # Vertex normal
                Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].normal.x = loop.normal.x
                Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].normal.y = loop.normal.y
                Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].normal.z = loop.normal.z

                # Vertex tangent
                Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].tangent.x = loop.tangent.x
                Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].tangent.y = loop.tangent.y
                Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].tangent.z = loop.tangent.z

                # Vertex binormal
                #Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].binormal.x = loop.bitangent.x
                #Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].binormal.y = loop.bitangent.y
                #Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].binormal.z = loop.bitangent.z

                # Vertex color
                if (len(selectedObject.data.vertex_colors) == 0):
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].color[0] = 127
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].color[1] = 127
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].color[2] = 127
                    Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].color[3] = 255
                else:
                    # If the mesh has no vertex colors, set the following colors
                    for color in selectedObject.data.vertex_colors:
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].color[0] = int(color.data[loop.index].color[2] * 255)
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].color[1] = int(color.data[loop.index].color[1] * 255)
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].color[2] = int(color.data[loop.index].color[0] * 255)
                        Exporter.objectInfo.lodGroups[i].meshes[0].geometry[mtlIndex].vertices[loop.vertex_index].color[3] = int(color.data[loop.index].color[3] * 255)

                currentLoopIndex += 1

            mtlIndex += 1
        
        duplicatedBlenderMesh.select_set(True)
        #except:
            #bpy.ops.object.delete()
            #return "ERROR_CODE_1"
    
    # Blender model materials
    #TODO lodGroups[i].meshes[k].geometry[k]
    for i in range(0, len(Exporter.blenderMeshes)):
        try:
            currentShaderIndex = 0
            mtlIndex = 0
            for j in range(0, materialSlotSize):
                material_slot = bpy.context.selected_objects[j].material_slots[0]

                for blenderObject in bpy.context.selected_objects:
                    if (blenderObject.material_slots[0].name != materialNames[j]):
                        continue

                    material_slot = blenderObject.material_slots[0]

                Exporter.objectInfo.shaders.append(Shaders())

                if (material_slot.material.libertytool_drawable.shader_category == "general"):
                    Exporter.objectInfo.shaders[currentShaderIndex].preset = material_slot.material.libertytool_drawable.shaders_general
                elif (material_slot.material.libertytool_drawable.shader_category == "vehicle"):
                    Exporter.objectInfo.shaders[currentShaderIndex].preset = material_slot.material.libertytool_drawable.shaders_vehicle
                elif (material_slot.material.libertytool_drawable.shader_category == "ped"):
                    Exporter.objectInfo.shaders[currentShaderIndex].preset = material_slot.material.libertytool_drawable.shaders_ped
                elif (material_slot.material.libertytool_drawable.shader_category == "other"):
                    Exporter.objectInfo.shaders[currentShaderIndex].preset = material_slot.material.libertytool_drawable.shaders_other

                textureSampler = "null"
                bumpSampler = "null"
                specSampler = "null"
                environmentSampler = "null"

                # Check texture names in Principled BSDF
                for link in material_slot.material.node_tree.links:
                    node = link.from_node
                    socket = link.to_socket
                    
                    # Diffuse
                    if (material_slot.material.libertytool_drawable.embed_diffuse_texture or material_slot.material.libertytool_drawable.diffuse_texture_name == ''):
                        if (node.type == "TEX_IMAGE" and socket.name == "Base Color"):
                            textureSampler = str.split(node.image.name, ".")[0]

                            # Embed texture in exported file
                            if (material_slot.material.libertytool_drawable.embed_diffuse_texture):
                                filePath = node.image.filepath_from_user()
                                fileName = str.split(node.image.name, ".")[0]
                                fileExtension = str.split(node.image.name, ".")[1]
                                if (fileExtension == str.lower("dds")):
                                    bIsTextureAlreadyExists = False
                                    
                                    for texture in Exporter.objectInfo.textures:
                                        if (texture.fileName != fileName):
                                            continue

                                        bIsTextureAlreadyExists = True

                                        break

                                    if (not bIsTextureAlreadyExists):
                                        texture = TextureDDS()
                                        texture.Load(filePath)

                                        textureInfo = TextureInfo()
                                        textureInfo.filePath = filePath
                                        textureInfo.fileName = fileName
                                        textureInfo.texture = texture

                                        Exporter.objectInfo.textures.append(textureInfo)

                    # Normal/Bump
                    if (material_slot.material.libertytool_drawable.embed_bump_texture or material_slot.material.libertytool_drawable.embed_bump_texture == ''):
                        if (node.type == "TEX_IMAGE" and socket.name == "Normal"):
                            bumpSampler = str.split(node.image.name, ".")[0]

                            # Embed texture in exported file
                            if (material_slot.material.libertytool_drawable.embed_bump_texture):
                                filePath = node.image.filepath_from_user()
                                fileName = str.split(node.image.name, ".")[0]
                                fileExtension = str.split(node.image.name, ".")[1]
                                if (fileExtension == str.lower("dds")):
                                    bIsTextureAlreadyExists = False

                                    for texture in Exporter.objectInfo.textures:
                                        if (texture.fileName != fileName):
                                            continue

                                        bIsTextureAlreadyExists = True

                                        break

                                    if (not bIsTextureAlreadyExists):
                                        texture = TextureDDS()
                                        texture.Load(filePath)

                                        textureInfo = TextureInfo()
                                        textureInfo.filePath = filePath
                                        textureInfo.fileName = fileName
                                        textureInfo.texture = texture

                                        Exporter.objectInfo.textures.append(textureInfo)

                    # Specular
                    if (material_slot.material.libertytool_drawable.embed_specular_texture or material_slot.material.libertytool_drawable.embed_specular_texture == ''):
                        if (node.type == "TEX_IMAGE" and socket.name == "Specular Tint"):
                            specSampler = str.split(node.image.name, ".")[0]

                            # Embed texture in exported file
                            if (material_slot.material.libertytool_drawable.embed_specular_texture):
                                filePath = node.image.filepath_from_user()
                                fileName = str.split(node.image.name, ".")[0]
                                fileExtension = str.split(node.image.name, ".")[1]
                                if (fileExtension == str.lower("dds")):
                                    bIsTextureAlreadyExists = False

                                    for texture in Exporter.objectInfo.textures:
                                        if (texture.fileName != fileName):
                                            continue

                                        bIsTextureAlreadyExists = True

                                        break

                                    if (not bIsTextureAlreadyExists):
                                        texture = TextureDDS()
                                        texture.Load(filePath)

                                        textureInfo = TextureInfo()
                                        textureInfo.filePath = filePath
                                        textureInfo.fileName = fileName
                                        textureInfo.texture = texture

                                        Exporter.objectInfo.textures.append(textureInfo)

                    # Environment
                    if (material_slot.material.libertytool_drawable.embed_environment_texture or material_slot.material.libertytool_drawable.embed_environment_texture == ''):
                        if (node.type == "TEX_IMAGE" and socket.name == "Sheen Tint"):
                            environmentSampler = str.split(node.image.name, ".")[0]

                            # Embed texture in exported file
                            if (material_slot.material.libertytool_drawable.embed_environment_texture):
                                filePath = node.image.filepath_from_user()
                                fileName = str.split(node.image.name, ".")[0]
                                fileExtension = str.split(node.image.name, ".")[1]
                                if (fileExtension == str.lower("dds")):
                                    bIsTextureAlreadyExists = False
                                    
                                    for texture in Exporter.objectInfo.textures:
                                        if (texture.fileName != fileName):
                                            continue

                                        bIsTextureAlreadyExists = True

                                        break

                                    if (not bIsTextureAlreadyExists):
                                        texture = TextureDDS()
                                        texture.Load(filePath)

                                        textureInfo = TextureInfo()
                                        textureInfo.filePath = filePath
                                        textureInfo.fileName = fileName
                                        textureInfo.texture = texture

                                        Exporter.objectInfo.textures.append(textureInfo)

                # Check texture names in DrawableMaterialProperties
                if (material_slot.material.libertytool_drawable.diffuse_texture_name and not material_slot.material.libertytool_drawable.embed_diffuse_texture):
                    textureSampler = material_slot.material.libertytool_drawable.diffuse_texture_name
                if (material_slot.material.libertytool_drawable.bump_texture_name and not material_slot.material.libertytool_drawable.embed_bump_texture):
                    bumpSampler = material_slot.material.libertytool_drawable.bump_texture_name
                if (material_slot.material.libertytool_drawable.specular_texture_name and not material_slot.material.libertytool_drawable.embed_specular_texture):
                    specSampler = material_slot.material.libertytool_drawable.specular_texture_name
                if (material_slot.material.libertytool_drawable.environment_texture_name and not material_slot.material.libertytool_drawable.embed_environment_texture):
                    environmentSampler = material_slot.material.libertytool_drawable.environment_texture_name

                params = Exporter.shaderManager[ShaderManager.GetShaderIndex(Exporter.shaderManager, Exporter.objectInfo.shaders[currentShaderIndex].preset)].param

                currentCustomParam = 0
                for i in range(0, len(params)):
                    if (params[i].staticValue[0] != "null"):
                        continue

                    currentCustomParam += 1

                customParamSize = currentCustomParam

                # Put Blender material settings into shader settings
                Exporter.objectInfo.shaders[currentShaderIndex].param = ["null"] * customParamSize
                currentCustomParam = 0
                for i in range(0, len(params)):
                    if (params[i].staticValue[0] != "null"):
                        continue

                    if (params[i].name == "texturesampler"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = textureSampler
                    elif (params[i].name == "bumpsampler"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = bumpSampler
                    elif (params[i].name == "specsampler"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = specSampler
                    elif (params[i].name == "environmentsampler"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = environmentSampler
                    elif (params[i].name == "specularfactor"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = str(material_slot.material.libertytool_drawable.specular_factor)
                    elif (params[i].name == "specularcolorfactor"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = str(material_slot.material.libertytool_drawable.specular_color_factor)
                    elif (params[i].name == "specmapintmask"):
                        specMapIntMask = str()
                        specMapIntMask += str(material_slot.material.libertytool_drawable.spec_map_int_mask[0])
                        specMapIntMask += ";"
                        specMapIntMask += str(material_slot.material.libertytool_drawable.spec_map_int_mask[1])
                        specMapIntMask += ";"
                        specMapIntMask += str(material_slot.material.libertytool_drawable.spec_map_int_mask[2])
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = specMapIntMask
                    elif (params[i].name == "bumpiness"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = str(material_slot.material.libertytool_drawable.bumpiness)
                    elif (params[i].name == "reflectivepower"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = str(material_slot.material.libertytool_drawable.reflective_power)
                    elif (params[i].name == "zshift"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = str(material_slot.material.libertytool_drawable.z_shift)
                    elif (params[i].name == "emissivemultiplier"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = str(material_slot.material.libertytool_drawable.emissive_multiplier)
                    elif (params[i].name == "parallaxscalebias"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = str(material_slot.material.libertytool_drawable.parallax_scale_bias)
                    elif (params[i].name == "dirtdecalmask"):
                        dirtDecalMask = str()
                        dirtDecalMask += str(material_slot.material.libertytool_drawable.dirt_decal_mask[0])
                        dirtDecalMask += ";"
                        dirtDecalMask += str(material_slot.material.libertytool_drawable.dirt_decal_mask[1])
                        dirtDecalMask += ";"
                        dirtDecalMask += str(material_slot.material.libertytool_drawable.dirt_decal_mask[2])
                        dirtDecalMask += ";"
                        dirtDecalMask += str(material_slot.material.libertytool_drawable.dirt_decal_mask[3])
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = dirtDecalMask
                    elif (params[i].name == "subcolor"):
                        subColor = str()
                        subColor += str(material_slot.material.libertytool_drawable.sub_color[0])
                        subColor += ";"
                        subColor += str(material_slot.material.libertytool_drawable.sub_color[1])
                        subColor += ";"
                        subColor += str(material_slot.material.libertytool_drawable.sub_color[2])
                        subColor += ";"
                        subColor += str(material_slot.material.libertytool_drawable.sub_color[3])
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = subColor
                    elif (params[i].name == "ordernumber"):
                        orderNumber = material_slot.material.libertytool_drawable.order_number
                        bytesOrderNumber = struct.pack('>l', orderNumber - 1)
                        denormalOrderNumber = struct.unpack('>f', bytesOrderNumber)[0]
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = str(denormalOrderNumber)
                    elif (params[i].name == "fade_thickness"):
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = str(material_slot.material.libertytool_drawable.fade_thickness)
                    elif (params[i].name == "gWorldInstanceMatrix"):
                        worldInstanceMatrix = str()
                        worldInstanceMatrix += str(material_slot.material.libertytool_drawable.world_instance_matrix[0])
                        worldInstanceMatrix += ";"
                        worldInstanceMatrix += str(material_slot.material.libertytool_drawable.world_instance_matrix[1])
                        worldInstanceMatrix += ";"
                        worldInstanceMatrix += str(material_slot.material.libertytool_drawable.world_instance_matrix[2])
                        worldInstanceMatrix += ";"
                        worldInstanceMatrix += str(material_slot.material.libertytool_drawable.world_instance_matrix[3])
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = worldInstanceMatrix
                    elif (params[i].name == "gWorldInstanceInverseTranspose"):
                        worldInstanceInverseTranspose = str()
                        worldInstanceInverseTranspose += str(material_slot.material.libertytool_drawable.world_instance_inverse_transpose[0])
                        worldInstanceInverseTranspose += ";"
                        worldInstanceInverseTranspose += str(material_slot.material.libertytool_drawable.world_instance_inverse_transpose[1])
                        worldInstanceInverseTranspose += ";"
                        worldInstanceInverseTranspose += str(material_slot.material.libertytool_drawable.world_instance_inverse_transpose[2])
                        worldInstanceInverseTranspose += ";"
                        worldInstanceInverseTranspose += str(material_slot.material.libertytool_drawable.world_instance_inverse_transpose[3])
                        Exporter.objectInfo.shaders[currentShaderIndex].param[currentCustomParam] = worldInstanceInverseTranspose
                    else:
                        currentCustomParam -= 1

                    currentCustomParam += 1

                currentShaderIndex += 1
        except:
            bpy.ops.object.delete()
            return "ERROR_CODE_2"

    # Delete cloned Blender objects
    bpy.ops.object.delete()

    # Blender collection
    # Bone flags
    if (bpy.context.collection.libertytool_skel.flag_have_bone_world_orientation):
        Exporter.objectInfo.skel.flags.append("HaveBoneMappings")
    if (bpy.context.collection.libertytool_skel.flag_have_bone_mappings):
        Exporter.objectInfo.skel.flags.append("HaveBoneWorldOrient")
    if (bpy.context.collection.libertytool_skel.flag_authored_orientation):
        Exporter.objectInfo.skel.flags.append("AuthoredOrientation")
    if (bpy.context.collection.libertytool_skel.flag_unk0):
        Exporter.objectInfo.skel.flags.append("unk0")

    # Bone count
    Exporter.objectInfo.skel.boneCount = len(Exporter.blenderEmpties)

    # Blender bones (armature)
    if (Exporter.blenderArmature):
        for boneID, blenderBone in enumerate(Exporter.blenderArmature.data.bones):
            totalParents = 0
            if (blenderBone.parent):
                blenderObject = blenderBone.parent
                totalParents += 1
                while (True):
                    if (blenderObject.parent):
                        blenderObject = blenderObject.parent
                        totalParents += 1
                    else:
                        break

            bone = Bone()
            
            bone.posInTheHierarchy = totalParents

            bone.name = blenderBone.name

            bone.id = boneID

            bone.index = boneID
            bone.mirror = boneID

            # Positions
            bone.localOffset.x = blenderBone.matrix_local.translation.x
            bone.localOffset.y = blenderBone.matrix_local.translation.y
            bone.localOffset.z = blenderBone.matrix_local.translation.z
            bone.worldOffset.x = (Exporter.blenderArmature.location + blenderBone.head_local).x
            bone.worldOffset.y = (Exporter.blenderArmature.location + blenderBone.head_local).y
            bone.worldOffset.z = (Exporter.blenderArmature.location + blenderBone.head_local).z

            # Rotations
            rotation_mode = "XYZ"
            if (bpy.context.collection.libertytool_skel.override_rotation_mode != "dont_override"):
                rotation_mode = bpy.context.collection.libertytool_skel.override_rotation_mode
            else:
                rotation_mode = Exporter.blenderArmature.rotation_mode

            blenderRotationEuler = blenderBone.matrix.to_euler()
            blenderRotationQuaternion = blenderBone.matrix.to_euler().to_quaternion()
            rotationEuler = Vector3()
            rotationQuaternion = Vector4()
            
            if (rotation_mode == "XZY"):
                rotationEuler.x = blenderRotationEuler.x
                rotationEuler.y = blenderRotationEuler.z
                rotationEuler.z = blenderRotationEuler.y
                rotationQuaternion.x = blenderRotationQuaternion.x
                rotationQuaternion.y = blenderRotationQuaternion.z
                rotationQuaternion.z = blenderRotationQuaternion.y
                rotationQuaternion.w = blenderRotationQuaternion.w
            elif (rotation_mode == "YXZ"):
                rotationEuler.x = blenderRotationEuler.y
                rotationEuler.y = blenderRotationEuler.x
                rotationEuler.z = blenderRotationEuler.z
                rotationQuaternion.x = blenderRotationQuaternion.y
                rotationQuaternion.y = blenderRotationQuaternion.x
                rotationQuaternion.z = blenderRotationQuaternion.z
                rotationQuaternion.w = blenderRotationQuaternion.w
            elif (rotation_mode == "YZX"):
                rotationEuler.x = blenderRotationEuler.y
                rotationEuler.y = blenderRotationEuler.z
                rotationEuler.z = blenderRotationEuler.x
                rotationQuaternion.x = blenderRotationQuaternion.y
                rotationQuaternion.y = blenderRotationQuaternion.z
                rotationQuaternion.z = blenderRotationQuaternion.x
                rotationQuaternion.w = blenderRotationQuaternion.w
            elif (rotation_mode == "ZXY"):
                rotationEuler.x = blenderRotationEuler.z
                rotationEuler.y = blenderRotationEuler.x
                rotationEuler.z = blenderRotationEuler.y
                rotationQuaternion.x = blenderRotationQuaternion.z
                rotationQuaternion.y = blenderRotationQuaternion.x
                rotationQuaternion.z = blenderRotationQuaternion.y
                rotationQuaternion.w = blenderRotationQuaternion.w
            elif (rotation_mode == "ZYX"):
                rotationEuler.x = blenderRotationEuler.z
                rotationEuler.y = blenderRotationEuler.y
                rotationEuler.z = blenderRotationEuler.x
                rotationQuaternion.x = blenderRotationQuaternion.z
                rotationQuaternion.y = blenderRotationQuaternion.y
                rotationQuaternion.z = blenderRotationQuaternion.x
                rotationQuaternion.w = blenderRotationQuaternion.w
            else:
                rotationEuler.x = blenderRotationEuler.x
                rotationEuler.y = blenderRotationEuler.y
                rotationEuler.z = blenderRotationEuler.z
                rotationQuaternion.x = blenderRotationQuaternion.x
                rotationQuaternion.y = blenderRotationQuaternion.y
                rotationQuaternion.z = blenderRotationQuaternion.z
                rotationQuaternion.w = blenderRotationQuaternion.w
            
            bone.rotationEuler.x = rotationEuler.x
            bone.rotationEuler.y = rotationEuler.y
            bone.rotationEuler.z = rotationEuler.z
            bone.rotationQuaternion.x = rotationQuaternion.x
            bone.rotationQuaternion.y = rotationQuaternion.y
            bone.rotationQuaternion.z = rotationQuaternion.z
            bone.rotationQuaternion.w = rotationQuaternion.w
            bone.orient.x = rotationEuler.x
            bone.orient.y = rotationEuler.y
            bone.orient.z = rotationEuler.z

            #TEMP?
            bone.rotMin.x = -math.pi
            bone.rotMin.y = -math.pi
            bone.rotMin.z = -math.pi
            bone.rotMax.x = math.pi
            bone.rotMax.y = math.pi
            bone.rotMax.z = math.pi
            
            # Bone flags
            if (blenderBone.libertytool_bone.flag_lock_rotation_xyz):
                bone.flags.append("LockRotationXYZ")
            if (blenderBone.libertytool_bone.flag_lock_rotation_x):
                bone.flags.append("LockRotationX")
            if (blenderBone.libertytool_bone.flag_lock_rotation_y):
                bone.flags.append("LockRotationY")
            if (blenderBone.libertytool_bone.flag_lock_rotation_z):
                bone.flags.append("LockRotationZ")
            if (blenderBone.libertytool_bone.flag_limit_rotation_x):
                bone.flags.append("LimitRotationX")
            if (blenderBone.libertytool_bone.flag_limit_rotation_y):
                bone.flags.append("LimitRotationY")
            if (blenderBone.libertytool_bone.flag_limit_rotation_z):
                bone.flags.append("LimitRotationZ")
            if (blenderBone.libertytool_bone.flag_lock_translation_x or boneID == 0 and bpy.context.collection.libertytool_skel.force_lock_location_armature):
                bone.flags.append("LockTranslationX")
            if (blenderBone.libertytool_bone.flag_lock_translation_y or boneID == 0 and bpy.context.collection.libertytool_skel.force_lock_location_armature):
                bone.flags.append("LockTranslationY")
            if (blenderBone.libertytool_bone.flag_lock_translation_z or boneID == 0 and bpy.context.collection.libertytool_skel.force_lock_location_armature):
                bone.flags.append("LockTranslationZ")
            if (blenderBone.libertytool_bone.flag_limit_translation_x):
                bone.flags.append("LimitTranslationX")
            if (blenderBone.libertytool_bone.flag_limit_translation_y):
                bone.flags.append("LimitTranslationY")
            if (blenderBone.libertytool_bone.flag_limit_translation_z):
                bone.flags.append("LimitTranslationZ")
            if (blenderBone.libertytool_bone.flag_lock_scale_x):
                bone.flags.append("LockScaleX")
            if (blenderBone.libertytool_bone.flag_lock_scale_y):
                bone.flags.append("LockScaleY")
            if (blenderBone.libertytool_bone.flag_lock_scale_z):
                bone.flags.append("LockScaleZ")
            if (blenderBone.libertytool_bone.flag_limit_scale_x):
                bone.flags.append("LimitScaleX")
            if (blenderBone.libertytool_bone.flag_limit_scale_y):
                bone.flags.append("LimitScaleY")
            if (blenderBone.libertytool_bone.flag_limit_scale_z):
                bone.flags.append("LimitScaleZ")
            if (blenderBone.libertytool_bone.flag_invisible):
                bone.flags.append("Invisible")

            Exporter.objectInfo.skel.bone.append(bone)

    # Blender empties
    for i in range(0, len(Exporter.blenderEmpties)):
        Exporter.objectInfo.skel.bone.append(Bone())

        Exporter.objectInfo.skel.bone[i].name = Exporter.blenderEmpties[i].name

        totalParents = 0
        if (Exporter.blenderEmpties[i].parent):
            blenderObject = Exporter.blenderEmpties[i].parent
            totalParents += 1
            while (True):
                if (blenderObject.parent):
                    blenderObject = blenderObject.parent
                    totalParents += 1
                else:
                    break
        Exporter.objectInfo.skel.bone[i].posInTheHierarchy = totalParents

        # Bone id
        if (Exporter.blenderEmpties[i].libertytool_bone.id == -1):
            Exporter.objectInfo.skel.bone[i].id = i #TEMP?
        else:
            Exporter.objectInfo.skel.bone[i].id = Exporter.blenderEmpties[i].libertytool_bone.id

        # Bone index
        if (Exporter.blenderEmpties[i].libertytool_bone.index == -1):
            Exporter.objectInfo.skel.bone[i].index = i #TEMP?
        else:
            Exporter.objectInfo.skel.bone[i].index = Exporter.blenderEmpties[i].libertytool_bone.index

        # Bone mirror
        if (Exporter.blenderEmpties[i].libertytool_bone.mirror == -1):
            Exporter.objectInfo.skel.bone[i].mirror = i #TEMP?
        else:
            Exporter.objectInfo.skel.bone[i].mirror = Exporter.blenderEmpties[i].libertytool_bone.mirror

        # Positions
        Exporter.objectInfo.skel.bone[i].localOffset.x = Exporter.blenderEmpties[i].matrix_local.translation.x
        Exporter.objectInfo.skel.bone[i].localOffset.y = Exporter.blenderEmpties[i].matrix_local.translation.y
        Exporter.objectInfo.skel.bone[i].localOffset.z = Exporter.blenderEmpties[i].matrix_local.translation.z
        Exporter.objectInfo.skel.bone[i].worldOffset.x = Exporter.blenderEmpties[i].matrix_world.translation.x
        Exporter.objectInfo.skel.bone[i].worldOffset.y = Exporter.blenderEmpties[i].matrix_world.translation.y
        Exporter.objectInfo.skel.bone[i].worldOffset.z = Exporter.blenderEmpties[i].matrix_world.translation.z

        # Rotations
        rotation_mode = "XYZ"
        if (bpy.context.collection.libertytool_skel.override_rotation_mode != "dont_override"):
            rotation_mode = bpy.context.collection.libertytool_skel.override_rotation_mode
        else:
            rotation_mode = Exporter.blenderEmpties[i].rotation_mode

        blenderRotationEuler = Exporter.blenderEmpties[i].rotation_euler
        blenderRotationQuaternion = Exporter.blenderEmpties[i].rotation_euler.to_quaternion()
        rotationEuler = Vector3()
        rotationQuaternion = Vector4()
        
        if (rotation_mode == "XZY"):
            rotationEuler.x = blenderRotationEuler.x
            rotationEuler.y = blenderRotationEuler.z
            rotationEuler.z = blenderRotationEuler.y
            rotationQuaternion.x = blenderRotationQuaternion.x
            rotationQuaternion.y = blenderRotationQuaternion.z
            rotationQuaternion.z = blenderRotationQuaternion.y
            rotationQuaternion.w = blenderRotationQuaternion.w
        elif (rotation_mode == "YXZ"):
            rotationEuler.x = blenderRotationEuler.y
            rotationEuler.y = blenderRotationEuler.x
            rotationEuler.z = blenderRotationEuler.z
            rotationQuaternion.x = blenderRotationQuaternion.y
            rotationQuaternion.y = blenderRotationQuaternion.x
            rotationQuaternion.z = blenderRotationQuaternion.z
            rotationQuaternion.w = blenderRotationQuaternion.w
        elif (rotation_mode == "YZX"):
            rotationEuler.x = blenderRotationEuler.y
            rotationEuler.y = blenderRotationEuler.z
            rotationEuler.z = blenderRotationEuler.x
            rotationQuaternion.x = blenderRotationQuaternion.y
            rotationQuaternion.y = blenderRotationQuaternion.z
            rotationQuaternion.z = blenderRotationQuaternion.x
            rotationQuaternion.w = blenderRotationQuaternion.w
        elif (rotation_mode == "ZXY"):
            rotationEuler.x = blenderRotationEuler.z
            rotationEuler.y = blenderRotationEuler.x
            rotationEuler.z = blenderRotationEuler.y
            rotationQuaternion.x = blenderRotationQuaternion.z
            rotationQuaternion.y = blenderRotationQuaternion.x
            rotationQuaternion.z = blenderRotationQuaternion.y
            rotationQuaternion.w = blenderRotationQuaternion.w
        elif (rotation_mode == "ZYX"):
            rotationEuler.x = blenderRotationEuler.z
            rotationEuler.y = blenderRotationEuler.y
            rotationEuler.z = blenderRotationEuler.x
            rotationQuaternion.x = blenderRotationQuaternion.z
            rotationQuaternion.y = blenderRotationQuaternion.y
            rotationQuaternion.z = blenderRotationQuaternion.x
            rotationQuaternion.w = blenderRotationQuaternion.w
        else:
            rotationEuler.x = blenderRotationEuler.x
            rotationEuler.y = blenderRotationEuler.y
            rotationEuler.z = blenderRotationEuler.z
            rotationQuaternion.x = blenderRotationQuaternion.x
            rotationQuaternion.y = blenderRotationQuaternion.y
            rotationQuaternion.z = blenderRotationQuaternion.z
            rotationQuaternion.w = blenderRotationQuaternion.w
        
        Exporter.objectInfo.skel.bone[i].rotationEuler.x = rotationEuler.x
        Exporter.objectInfo.skel.bone[i].rotationEuler.y = rotationEuler.y
        Exporter.objectInfo.skel.bone[i].rotationEuler.z = rotationEuler.z
        Exporter.objectInfo.skel.bone[i].rotationQuaternion.x = rotationQuaternion.x
        Exporter.objectInfo.skel.bone[i].rotationQuaternion.y = rotationQuaternion.y
        Exporter.objectInfo.skel.bone[i].rotationQuaternion.z = rotationQuaternion.z
        Exporter.objectInfo.skel.bone[i].rotationQuaternion.w = rotationQuaternion.w
        Exporter.objectInfo.skel.bone[i].orient.x = rotationEuler.x
        Exporter.objectInfo.skel.bone[i].orient.y = rotationEuler.y
        Exporter.objectInfo.skel.bone[i].orient.z = rotationEuler.z

        #TEMP?
        Exporter.objectInfo.skel.bone[i].rotMin.x = -math.pi
        Exporter.objectInfo.skel.bone[i].rotMin.y = -math.pi
        Exporter.objectInfo.skel.bone[i].rotMin.z = -math.pi
        Exporter.objectInfo.skel.bone[i].rotMax.x = math.pi
        Exporter.objectInfo.skel.bone[i].rotMax.y = math.pi
        Exporter.objectInfo.skel.bone[i].rotMax.z = math.pi
        
        # Bone flags
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_lock_rotation_xyz):
            Exporter.objectInfo.skel.bone[i].flags.append("LockRotationXYZ")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_lock_rotation_x):
            Exporter.objectInfo.skel.bone[i].flags.append("LockRotationX")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_lock_rotation_y):
            Exporter.objectInfo.skel.bone[i].flags.append("LockRotationY")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_lock_rotation_z):
            Exporter.objectInfo.skel.bone[i].flags.append("LockRotationZ")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_limit_rotation_x):
            Exporter.objectInfo.skel.bone[i].flags.append("LimitRotationX")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_limit_rotation_y):
            Exporter.objectInfo.skel.bone[i].flags.append("LimitRotationY")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_limit_rotation_z):
            Exporter.objectInfo.skel.bone[i].flags.append("LimitRotationZ")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_lock_translation_x):
            Exporter.objectInfo.skel.bone[i].flags.append("LockTranslationX")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_lock_translation_y):
            Exporter.objectInfo.skel.bone[i].flags.append("LockTranslationY")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_lock_translation_z):
            Exporter.objectInfo.skel.bone[i].flags.append("LockTranslationZ")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_limit_translation_x):
            Exporter.objectInfo.skel.bone[i].flags.append("LimitTranslationX")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_limit_translation_y):
            Exporter.objectInfo.skel.bone[i].flags.append("LimitTranslationY")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_limit_translation_z):
            Exporter.objectInfo.skel.bone[i].flags.append("LimitTranslationZ")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_lock_scale_x):
            Exporter.objectInfo.skel.bone[i].flags.append("LockScaleX")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_lock_scale_y):
            Exporter.objectInfo.skel.bone[i].flags.append("LockScaleY")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_lock_scale_z):
            Exporter.objectInfo.skel.bone[i].flags.append("LockScaleZ")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_limit_scale_x):
            Exporter.objectInfo.skel.bone[i].flags.append("LimitScaleX")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_limit_scale_y):
            Exporter.objectInfo.skel.bone[i].flags.append("LimitScaleY")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_limit_scale_z):
            Exporter.objectInfo.skel.bone[i].flags.append("LimitScaleZ")
        if (Exporter.blenderEmpties[i].libertytool_bone.flag_invisible):
            Exporter.objectInfo.skel.bone[i].flags.append("Invisible")

    ############################################################
    ###################### Layout section ######################
    ############################################################

    Exporter.cpuLayout.Add(Exporter.shaderGroup._structSize)

    shaderSize = len(Exporter.objectInfo.shaders)

    if (len(Exporter.objectInfo.textures) > 0):
        texturesSize = len(Exporter.objectInfo.textures)
        Exporter.cpuLayout.Add(0x20)
        Exporter.cpuLayout.Add(0x4 * texturesSize) # pointer to texturePC
        Exporter.cpuLayout.Add(0x4 * texturesSize) # hash
        for i in range(0, texturesSize):
            Exporter.cpuLayout.Add(0x50) # texturePC

    Exporter.cpuLayout.Add(shaderSize * 0x4) # ptr to shaderfx
    Exporter.cpuLayout.Add(shaderSize * 0x4) # index
    Exporter.cpuLayout.Add(shaderSize * 0x4) # vertexFormat

    for i in range(0, shaderSize):
        Exporter.cpuLayout.Add(0x5c) # shaderfx
        Exporter.cpuLayout.Add(Exporter.objectInfo.shaders[i].preset)
        Exporter.cpuLayout.Add(Exporter.shaderManager[ShaderManager.GetShaderIndex(Exporter.shaderManager, Exporter.objectInfo.shaders[i].preset)].name)
        Exporter.cpuLayout.Add(Exporter.shaderManager[ShaderManager.GetShaderIndex(Exporter.shaderManager, Exporter.objectInfo.shaders[i].preset)].blockSize)

        shaderIndex = ShaderManager.GetShaderIndex(Exporter.shaderManager, Exporter.objectInfo.shaders[i].preset)
        currentCustomParam = 0
        for j in range(0, len(Exporter.shaderManager[shaderIndex].param)):
            if (Exporter.shaderManager[shaderIndex].param[j].type == "texture"):
                if (not Exporter.shaderManager[shaderIndex].param[j].custom):
                    if (Exporter.shaderManager[shaderIndex].param[j].staticValue[0] != "null"):
                        Exporter.cpuLayout.Add(0x1c) # tex ref
                        Exporter.cpuLayout.Add(Exporter.shaderManager[shaderIndex].param[j].staticValue[0])
                else:
                    if (Exporter.objectInfo.shaders[i].param[currentCustomParam] != "null"):
                        bTextureFileExists = False

                        for textureInfo in Exporter.objectInfo.textures:
                            if (textureInfo.fileName != Exporter.objectInfo.shaders[i].param[currentCustomParam]):
                                continue

                            bTextureFileExists = True

                            break
                        
                        if (not bTextureFileExists):
                            Exporter.cpuLayout.Add(0x1c) # tex ref
                            Exporter.cpuLayout.Add(Exporter.objectInfo.shaders[i].param[currentCustomParam])
                    currentCustomParam += 1
            else:
                if (Exporter.shaderManager[shaderIndex].param[j].custom):
                    currentCustomParam += 1

    # textures
    for textureInfo in Exporter.objectInfo.textures:
        Exporter.cpuLayout.Add(textureInfo.fileName)

    Exporter.cpuLayout.Add(0x210) # pBlockMap

    # skel
    boneSize = len(Exporter.objectInfo.skel.bone)
    if (boneSize > 0):
        Exporter.cpuLayout.Add(0x40) # skelData
        Exporter.cpuLayout.Add(0xe0 * boneSize) # crBone
        Exporter.cpuLayout.Add(0x4 * boneSize) # parrent bones

        Exporter.cpuLayout.Add(0x40 * boneSize) # local transform
        for i in range(0, len(Exporter.objectInfo.skel.flags)):
            if (Exporter.objectInfo.skel.flags[i] == "HaveBoneWorldOrient"):
                Exporter.cpuLayout.Add(0x80 * boneSize)
            elif (Exporter.objectInfo.skel.flags[i] == "HaveBoneMappings"):
                Exporter.cpuLayout.Add(0x4 * boneSize)
        
        for i in range(0, boneSize):
            Exporter.cpuLayout.Add(Exporter.objectInfo.skel.bone[i].name)

    # lodGroup
    for i in range(0, 4):
        meshSize = len(Exporter.objectInfo.lodGroups[i].meshes)

        if (meshSize == 0):
            continue

        Exporter.cpuLayout.Add(0x8) # modelCollection
        Exporter.cpuLayout.Add(meshSize * 0x4)

        for j in range(0, meshSize):
            Exporter.cpuLayout.Add(0x1c) # model

            if (not Exporter.objectInfo.lodGroups[i].meshes[j].skinned):
                boundsSize = len(Exporter.objectInfo.lodGroups[i].meshes[j].bounds)
                Exporter.cpuLayout.Add(boundsSize * 0x10)

            geometrySize = len(Exporter.objectInfo.lodGroups[i].meshes[j].geometry)
            Exporter.cpuLayout.Add(geometrySize * 0x2) # mtl index
            Exporter.cpuLayout.Add(geometrySize * 0x4) # geometry pointers
            for k in range(0, geometrySize):
                Exporter.cpuLayout.Add(0x4c) # geometry

                if (Exporter.objectInfo.lodGroups[i].meshes[j].skinned):
                    usedBlendIndexSize = len(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].usedBlendIndex)
                    Exporter.cpuLayout.Add(usedBlendIndexSize * 0x2) # used bones

                Exporter.cpuLayout.Add(0x40) # vertex buffer
                Exporter.cpuLayout.Add(0x30) # index buffer
                Exporter.cpuLayout.Add(0x10) # vertex declaration

    # pixels
    for i in range(0, len(Exporter.objectInfo.textures)):
        Exporter.gpuLayout.Add(len(Exporter.objectInfo.textures[i].texture.data))

    # model
    for i in range(0, 4):
        meshSize = len(Exporter.objectInfo.lodGroups[i].meshes)

        if (meshSize == 0):
            continue

        for j in range(0, meshSize):
            geometrySize = len(Exporter.objectInfo.lodGroups[i].meshes[j].geometry)
            for k in range(0, geometrySize):
                preset = Exporter.objectInfo.shaders[Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].mtlIndex].preset
                shaderIndex = ShaderManager.GetShaderIndex(Exporter.shaderManager, preset)

                Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertexFormat = Exporter.shaderManager[shaderIndex].vertexFormat
                Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].types = Exporter.shaderManager[shaderIndex].elementTypes

                if (Exporter.objectInfo.lodGroups[i].meshes[j].skinned):
                    Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertexFormat = SetBit(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertexFormat, 1, 1, 1)
                    Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertexFormat = SetBit(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertexFormat, 2, 1, 1)
                    Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].types = SetBit(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].types, 4, 9, 4)
                    Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].types = SetBit(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].types, 8, 9, 4)
                
                Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertexStride = ShaderManager.GetStride(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].types, Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertexFormat)
                vertexStride = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertexStride
                verticesSize = len(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices)
                indicesSize = len(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].indices)
                Exporter.gpuLayout.Add(verticesSize * vertexStride)
                Exporter.gpuLayout.Add(indicesSize * 0x2)

    Exporter.flags = Exporter.cpuLayout.CreateLayout(144, Exporter.flags, 5)
    Exporter.flags = Exporter.gpuLayout.CreateLayout(0, Exporter.flags, 6)

    ####################################################################
    ###################### Binary writing section ######################
    ####################################################################

    Exporter.drawable._vmt = VirtualTables.gtaDrawable

    cpu = ctypes.create_string_buffer(int(Exporter.flags.GetTotalVSize()))
    ctypes.memset(cpu, 0xcd, Exporter.flags.GetTotalVSize())

    Exporter.drawable.pageMap = Ptr(Exporter.cpuLayout.GetPos(0x210), 5)
    ctypes.memset(cpu[Exporter.drawable.pageMap.GetOffset():], 0, 4)

    gpu = ctypes.create_string_buffer(int(Exporter.flags.GetTotalPSize()))
    ctypes.memset(gpu, 0xcd, Exporter.flags.GetTotalPSize())

    Exporter.shaderGroup._vmt = VirtualTables.grmShaderGroup
    Exporter.drawable.shaderGroup = Ptr(Exporter.cpuLayout.GetPos(Exporter.shaderGroup._structSize), 5)

    # embed textures
    if (len(Exporter.objectInfo.textures) > 0):
        texturesSize = len(Exporter.objectInfo.textures)

        Exporter.shaderGroup.texture = Ptr(Exporter.cpuLayout.GetPos(0x20), 5)
        Exporter.textureDictionary._vmt = np.uint32(VirtualTables.pgDictionary_grcTexturePC)
        Exporter.textureDictionary.usageCount = np.uint32(1)
        Exporter.textureDictionary.hashes.data = Ptr(Exporter.cpuLayout.GetPos(texturesSize * 0x4), 5)
        Exporter.textureDictionary.hashes.count = np.ushort(texturesSize)
        Exporter.textureDictionary.hashes.size = np.ushort(texturesSize)
        Exporter.textureDictionary.data.data = Ptr(Exporter.cpuLayout.GetPos(texturesSize * 0x4), 5)
        Exporter.textureDictionary.data.count = np.ushort(texturesSize)
        Exporter.textureDictionary.data.size = np.ushort(texturesSize)
        for i in range(0, texturesSize):
            Exporter.textureDictionary._hashes.append(GetHash(Exporter.objectInfo.textures[i].fileName, True))
            Exporter.textureDictionary._data.append(Ptr(Exporter.cpuLayout.GetPos(0x50), 5))
            
        grcTextures = []
        for i in range(0, texturesSize):
            texture = grcTexturePC()

            texture._vmt = VirtualTables.grcTexturePC
            texture.usageCount = np.ushort(1)
            texture.depth = np.ubyte(0)
            texture.levels = np.ubyte(Exporter.objectInfo.textures[i].texture.levels)
            texture.textureType = np.ubyte(0)
            texture.stride = np.ushort(Exporter.objectInfo.textures[i].texture.stride)
            texture.height = np.ushort(Exporter.objectInfo.textures[i].texture.height)
            texture.width = np.ushort(Exporter.objectInfo.textures[i].texture.width)
            texture._f28.x = np.float32(1.0)
            texture._f28.y = np.float32(1.0)
            texture._f28.z = np.float32(1.0)
            texture._f34 = Vector3()
            texture.pixelData = Ptr(Exporter.gpuLayout.GetPos(len(Exporter.objectInfo.textures[i].texture.data)), 6)

            if (Exporter.objectInfo.textures[i].texture.format.name == "DXT1"):
                texture.pixelFormat = 827611204
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "DXT3"):
                texture.pixelFormat = 861165636
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "DXT5"):
                texture.pixelFormat = 894720068
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "X8R8G8B8"):
                texture.pixelFormat = 22
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A8R8G8B8"):
                texture.pixelFormat = 21
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "L8"):
                texture.pixelFormat = 50
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "R8G8B8"):
                texture.pixelFormat = 20
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "R5G6B5"):
                texture.pixelFormat = 23
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "X1R5G5B5"):
                texture.pixelFormat = 24
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A1R5G5B5"):
                texture.pixelFormat = 25
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A4R4G4B4"):
                texture.pixelFormat = 26
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "R3G3B2"):
                texture.pixelFormat = 27
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A8"):
                texture.pixelFormat = 28
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A8R3G3B2"):
                texture.pixelFormat = 29
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "X4R4G4B4"):
                texture.pixelFormat = 30
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A2B10G10R10"):
                texture.pixelFormat = 31
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A8B8G8R8"):
                texture.pixelFormat = 32
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "X8B8G8R8"):
                texture.pixelFormat = 33
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "G16R16"):
                texture.pixelFormat = 34
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A2R10G10B10"):
                texture.pixelFormat = 35
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A16B16G16R16"):
                texture.pixelFormat = 36
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A8L8"):
                texture.pixelFormat = 51
            elif (Exporter.objectInfo.textures[i].texture.format.name ==  "A4L4"):
                texture.pixelFormat = 52

            texture.pixelFormat = np.uint32(texture.pixelFormat)

            if (texturesSize > 1):
                # next
                if (i != texturesSize - 1):
                    texture.next = Exporter.textureDictionary._data[i + 1]
                
                # previous
                if (i != 0):
                    texture.prev = Exporter.textureDictionary._data[i - 1]

            texture.name = Ptr(Exporter.cpuLayout.GetPos(np.str_(Exporter.objectInfo.textures[i].fileName)), 5)

            ctypes.memmove(ctypes.addressof(cpu) + texture.name.GetOffset(), Exporter.objectInfo.textures[i].fileName.encode(), len(Exporter.objectInfo.textures[i].fileName) + 1)

            byteTexture = bytes()
            byteTexture += texture._vmt.tobytes()
            byteTexture += texture.pageMap.ptr.tobytes()
            byteTexture += texture._f8.tobytes()
            byteTexture += texture.depth.tobytes()
            byteTexture += texture.usageCount.tobytes()
            byteTexture += texture._fC.tobytes()
            byteTexture += texture._f10.tobytes()
            byteTexture += texture.name.ptr.tobytes()
            byteTexture += texture.texture.ptr.tobytes()
            byteTexture += texture.width.tobytes()
            byteTexture += texture.height.tobytes()
            byteTexture += texture.pixelFormat.tobytes()
            byteTexture += texture.stride.tobytes()
            byteTexture += texture.textureType.tobytes()
            byteTexture += texture.levels.tobytes()
            byteTexture += texture._f28.x.tobytes()
            byteTexture += texture._f28.y.tobytes()
            byteTexture += texture._f28.z.tobytes()
            byteTexture += texture._f34.x.tobytes()
            byteTexture += texture._f34.y.tobytes()
            byteTexture += texture._f34.z.tobytes()
            byteTexture += texture.prev.ptr.tobytes()
            byteTexture += texture.next.ptr.tobytes()
            byteTexture += texture.pixelData.ptr.tobytes()
            byteTexture += texture._f4C.tobytes()
            byteTexture += texture._f4D.tobytes()
            byteTexture += texture._f4E.tobytes()
            byteTexture += texture._f4F.tobytes()
            ctypes.memmove(ctypes.addressof(cpu) + Exporter.textureDictionary._data[i].GetOffset(), byteTexture, texture._structSize)

            ctypes.memmove(ctypes.addressof(gpu) + texture.pixelData.GetOffset(), Exporter.objectInfo.textures[i].texture.data[0:], len(Exporter.objectInfo.textures[i].texture.data))

            grcTextures.append(texture)

        Exporter.textureDictionary.SortData()
        
        byteTextureDictionary = bytes()
        byteTextureDictionary += Exporter.textureDictionary._vmt.tobytes()
        byteTextureDictionary += Exporter.textureDictionary.pageMap.ptr.tobytes()
        byteTextureDictionary += Exporter.textureDictionary.parent.tobytes()
        byteTextureDictionary += Exporter.textureDictionary.usageCount.tobytes()
        byteTextureDictionary += Exporter.textureDictionary.hashes.data.ptr.tobytes()
        byteTextureDictionary += Exporter.textureDictionary.hashes.count.tobytes()
        byteTextureDictionary += Exporter.textureDictionary.hashes.size.tobytes()
        byteTextureDictionary += Exporter.textureDictionary.data.data.ptr.tobytes()
        byteTextureDictionary += Exporter.textureDictionary.data.count.tobytes()
        byteTextureDictionary += Exporter.textureDictionary.data.size.tobytes()
        ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderGroup.texture.GetOffset(), byteTextureDictionary, Exporter.textureDictionary._structSize)

        byteHashes = bytes()
        for j in range(0, len(Exporter.textureDictionary._hashes)):
            byteHashes += Exporter.textureDictionary._hashes[j].tobytes()
        ctypes.memmove(ctypes.addressof(cpu) + Exporter.textureDictionary.hashes.data.GetOffset(), byteHashes, texturesSize * 0x4)

        byteData = bytes()
        for j in range(0, len(Exporter.textureDictionary._data)):
            byteData += Exporter.textureDictionary._data[j].ptr.tobytes()
        ctypes.memmove(ctypes.addressof(cpu) + Exporter.textureDictionary.data.data.GetOffset(), byteData, texturesSize * 0x4)

    # shaders
    shaderSize = len(Exporter.objectInfo.shaders)

    Exporter.shaderGroup.shaders.data = Ptr(Exporter.cpuLayout.GetPos(shaderSize * 0x4), 5)
    Exporter.shaderGroup.shaders.count = np.ushort(shaderSize)
    Exporter.shaderGroup.shaders.size = np.ushort(shaderSize)
    for i in range(0, shaderSize):
        Exporter.shaderGroup._shader.append(Ptr(Exporter.cpuLayout.GetPos(0x5c), 5))
    Exporter.shaderGroup._index = [0] * shaderSize
    Exporter.shaderGroup._vertexFormat = [0] * shaderSize

    byteShader = bytes()
    for i in range(0, shaderSize):
        byteShader += Exporter.shaderGroup._shader[i].ptr.tobytes()
    ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderGroup.shaders.data.GetOffset(), byteShader, shaderSize * 0x4)

    for i in range(0, shaderSize):
        Exporter.shaderFX.append(ShaderFX())

        indexInShaderManager = ShaderManager.GetShaderIndex(Exporter.shaderManager, Exporter.objectInfo.shaders[i].preset)

        Exporter.shaderFX[i]._vmt = VirtualTables.grmShaderFx
        Exporter.shaderFX[i]._name = np.str_(Exporter.shaderManager[indexInShaderManager].name)
        Exporter.shaderFX[i]._sps = np.str_(Exporter.shaderManager[indexInShaderManager].preset)
        Exporter.shaderFX[i].name = Ptr(Exporter.cpuLayout.GetPos(Exporter.shaderFX[i]._name), 5)
        Exporter.shaderFX[i].spsName = Ptr(Exporter.cpuLayout.GetPos(Exporter.shaderFX[i]._sps), 5)

        shaderParamSize = len(Exporter.shaderManager[indexInShaderManager].param)

        Exporter.shaderFX[i].effect.effectSize = np.uint(Exporter.shaderManager[indexInShaderManager].blockSize)
        Exporter.shaderFX[i].effect.parameterCount = np.uint32(shaderParamSize)
        Exporter.shaderFX[i].effect.hash = GetHash(Exporter.shaderFX[i]._name, True)
        Exporter.shaderFX[i].drawBucket = np.ubyte(Exporter.shaderManager[indexInShaderManager].drawBucket)
        Exporter.shaderFX[i].index = np.ushort(Exporter.shaderManager[indexInShaderManager].index)
        Exporter.shaderFX[i].unk_f8 = np.ubyte(2)
        Exporter.shaderFX[i].unk_fa = np.ubyte(1)
        Exporter.shaderFX[i].unk_fc = np.ushort(0)
        Exporter.shaderFX[i].unk_fb = np.ubyte(1)

        Exporter.shaderFX[i].effect.parameters = Ptr(Exporter.cpuLayout.GetPos(Exporter.shaderFX[i].effect.effectSize), 5)
        posInEffectBlock = 0
        for _ in range(0, Exporter.shaderFX[i].effect.parameterCount):
            Exporter.shaderFX[i]._parameter.append(Ptr())
        posInEffectBlock += 0x4 * shaderParamSize
        Exporter.shaderFX[i].effect.parameterTypes = Ptr(Exporter.shaderFX[i].effect.parameters.GetOffset() + posInEffectBlock, 5)
        for _ in range(0, Exporter.shaderFX[i].effect.parameterCount):
            Exporter.shaderFX[i]._type.append(Ptr())
        posInEffectBlock += shaderParamSize
        Exporter.shaderFX[i].effect.paramsHash = Ptr(Exporter.shaderFX[i].effect.parameters.GetOffset() + posInEffectBlock, 5)
        for _ in range(0, Exporter.shaderFX[i].effect.parameterCount):
            Exporter.shaderFX[i]._paramHash.append(Ptr())
        posInEffectBlock += 0x4 * shaderParamSize

        effectBlock = ctypes.create_string_buffer(Exporter.shaderFX[i].effect.effectSize.item())
        ctypes.memset(effectBlock, 0xcd, Exporter.shaderFX[i].effect.effectSize)

        currentCustomParam = 0

        for j in range(0, shaderParamSize):
            if (Exporter.shaderManager[indexInShaderManager].param[j].custom):
                if (str.lower(Exporter.objectInfo.shaders[i].param[currentCustomParam]) == "null"): #TEMP?
                    currentCustomParam += 1
                    continue
            else:
                if (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].staticValue[0]) == "null"):
                    continue
            
            if (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "texture"):
                if (Exporter.shaderManager[indexInShaderManager].param[j].custom):
                    bTextureFileExists = False

                    for textureInfo in Exporter.objectInfo.textures:
                        if (textureInfo.fileName != Exporter.objectInfo.shaders[i].param[currentCustomParam]):
                            continue

                        bTextureFileExists = True

                        break
                    
                    if (bTextureFileExists):
                        for k in range(0, len(Exporter.textureDictionary._hashes)):
                            textureName = str.split(Exporter.objectInfo.shaders[i].param[currentCustomParam], ".")[0]
                            if (GetHash(textureName, True) == Exporter.textureDictionary._hashes[k]):
                                Exporter.shaderFX[i]._parameter[j] = Exporter.textureDictionary._data[k]
                    else:
                        txd = grcTextureReference()
                        txd._vmt = VirtualTables.grcTexture
                        txd._f8 = np.ubyte(2)
                        txd.usageCount = np.ushort(1)
                        txd._name = np.str_(Exporter.objectInfo.shaders[i].param[currentCustomParam])
                        txd.name = Ptr(Exporter.cpuLayout.GetPos(txd._name), 5)
                        Exporter.shaderFX[i]._parameter[j] = Ptr(Exporter.cpuLayout.GetPos(txd._structSize), 5)
                        ctypes.memmove(ctypes.addressof(cpu) + txd.name.GetOffset(), bytes(txd._name.encode()), len(txd._name) + 1)

                        byteTXD = bytes()
                        byteTXD += txd._vmt.tobytes()
                        byteTXD += txd.pageMap.ptr.tobytes()
                        byteTXD += txd._f8.tobytes()
                        byteTXD += txd._f9.tobytes()
                        byteTXD += txd.usageCount.tobytes()
                        byteTXD += txd._fc.tobytes()
                        byteTXD += txd._f10.tobytes()
                        byteTXD += txd.name.ptr.tobytes()
                        byteTXD += txd.texture.tobytes()
                        ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderFX[i]._parameter[j].GetOffset(), byteTXD, txd._structSize)
                    currentCustomParam += 1
                else:
                    txd = grcTextureReference()
                    txd._vmt = VirtualTables.grcTexture
                    txd._f8 = np.ubyte(2)
                    txd.usageCount = np.ushort(1)
                    txd._name = np.str_(Exporter.shaderManager[indexInShaderManager].param[j].staticValue[0])
                    txd.name = Ptr(Exporter.cpuLayout.GetPos(txd._name), 5)
                    Exporter.shaderFX[i]._parameter[j] = Ptr(Exporter.cpuLayout.GetPos(txd._structSize), 5)

                    ctypes.memmove(ctypes.addressof(cpu) + txd.name.GetOffset(), bytes(txd._name.encode()), len(txd._name) + 1)

                    byteTXD = bytes()
                    byteTXD += txd._vmt.tobytes()
                    byteTXD += txd.pageMap.ptr.tobytes()
                    byteTXD += txd._f8.tobytes()
                    byteTXD += txd._f9.tobytes()
                    byteTXD += txd.usageCount.tobytes()
                    byteTXD += txd._fc.tobytes()
                    byteTXD += txd._f10.tobytes()
                    byteTXD += txd.name.ptr.tobytes()
                    byteTXD += txd.texture.tobytes()
                    ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderFX[i]._parameter[j].GetOffset(), byteTXD, txd._structSize)
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "float"):
                value = 0
                if (Exporter.shaderManager[indexInShaderManager].param[j].custom):
                    value = float(Exporter.objectInfo.shaders[i].param[currentCustomParam])
                    currentCustomParam += 1
                else:
                    value = float(Exporter.shaderManager[indexInShaderManager].param[j].staticValue[0])

                Exporter.shaderFX[i]._parameter[j] = Ptr(Exporter.shaderFX[i].effect.parameters.GetOffset() + posInEffectBlock, 5)

                valueSize = 4
                ctypes.memmove(ctypes.addressof(effectBlock) + posInEffectBlock, struct.pack("f", value), valueSize)

                ctypes.memset(ctypes.addressof(effectBlock) + posInEffectBlock + 4, 0, 0xc)
                posInEffectBlock += 0x10
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "vector4"):
                value = [0.0] * 0x4
                if (Exporter.shaderManager[indexInShaderManager].param[j].custom):
                    strValue = Exporter.objectInfo.shaders[i].param[currentCustomParam].split(";")
                    for k in range (0, len(strValue)):
                        value[k] = float(strValue[k])
                    currentCustomParam += 1
                else:
                    for k in range(0, len(Exporter.shaderManager[indexInShaderManager].param[j].staticValue)):
                        value[k] = float(Exporter.shaderManager[indexInShaderManager].param[j].staticValue[k])

                Exporter.shaderFX[i]._parameter[j] = Ptr(Exporter.shaderFX[i].effect.parameters.GetOffset() + posInEffectBlock, 5)

                byteValue = bytes()
                for k in range(0, len(value)):
                    byteValue += struct.pack("f", value[k])

                ctypes.memmove(ctypes.addressof(effectBlock) + posInEffectBlock, byteValue, 0x4 * len(value))
                
                posInEffectBlock += len(value) * 0x4
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "matrix"):
                value = [0.0] * 0x10
                if (Exporter.shaderManager[indexInShaderManager].param[j].custom):
                    strValue = Exporter.objectInfo.shaders[i].param[currentCustomParam].split(";")
                    for k in range (0, len(strValue)):
                        value[k] = float(strValue[k])
                    currentCustomParam += 1
                else:
                    for k in range(0, len(Exporter.shaderManager[indexInShaderManager].param[j].staticValue)):
                        value[k] = float(Exporter.shaderManager[indexInShaderManager].param[j].staticValue[k])

                Exporter.shaderFX[i]._parameter[j] = Ptr(Exporter.shaderFX[i].effect.parameters.GetOffset() + posInEffectBlock, 5)

                byteValue = bytes()
                for k in range(0, len(value)):
                    byteValue += struct.pack("f", value[k])
                
                ctypes.memmove(ctypes.addressof(effectBlock) + posInEffectBlock, byteValue, 0x4 * len(value))
                
                posInEffectBlock += len(value) * 0x4
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "vector4_6"):
                value = [0.0] * (0x4 * 6)
                if (Exporter.shaderManager[indexInShaderManager].param[j].custom):
                    strValue = Exporter.objectInfo.shaders[i].param[currentCustomParam].split(";")
                    for k in range (0, len(strValue)):
                        value[k] = float(strValue[k])
                    currentCustomParam += 1
                else:
                    for k in range(0, len(Exporter.shaderManager[indexInShaderManager].param[j].staticValue)):
                        value[k] = float(Exporter.shaderManager[indexInShaderManager].param[j].staticValue[k])

                Exporter.shaderFX[i]._parameter[j] = Ptr(Exporter.shaderFX[i].effect.parameters.GetOffset() + posInEffectBlock, 5)

                byteValue = bytes()
                for k in range(0, len(value)):
                    byteValue += struct.pack("f", value[k])
                
                ctypes.memmove(ctypes.addressof(effectBlock) + posInEffectBlock, byteValue, 0x4 * len(value))
                
                posInEffectBlock += len(value) * 0x4
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "vector4_14"):
                value = [0.0] * (0x4 * 14)
                if (Exporter.shaderManager[indexInShaderManager].param[j].custom):
                    strValue = Exporter.objectInfo.shaders[i].param[currentCustomParam].split(";")
                    for k in range (0, len(strValue)):
                        value[k] = float(strValue[k])
                    currentCustomParam += 1
                else:
                    for k in range(0, len(Exporter.shaderManager[indexInShaderManager].param[j].staticValue)):
                        value[k] = float(Exporter.shaderManager[indexInShaderManager].param[j].staticValue[k])

                Exporter.shaderFX[i]._parameter[j] = Ptr(Exporter.shaderFX[i].effect.parameters.GetOffset() + posInEffectBlock, 5)

                byteValue = bytes()
                for k in range(0, len(value)):
                    byteValue += struct.pack("f", value[k])
                
                ctypes.memmove(ctypes.addressof(effectBlock) + posInEffectBlock, byteValue, 0x4 * len(value))
                
                posInEffectBlock += len(value) * 0x4
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "vector4_15"):
                value = [0.0] * (0x4 * 15)
                if (Exporter.shaderManager[indexInShaderManager].param[j].custom):
                    strValue = Exporter.objectInfo.shaders[i].param[currentCustomParam].split(";")
                    for k in range (0, len(strValue)):
                        value[k] = float(strValue[k])
                    currentCustomParam += 1
                else:
                    for k in range(0, len(Exporter.shaderManager[indexInShaderManager].param[j].staticValue)):
                        value[k] = float(Exporter.shaderManager[indexInShaderManager].param[j].staticValue[k])

                Exporter.shaderFX[i]._parameter[j] = Ptr(Exporter.shaderFX[i].effect.parameters.GetOffset() + posInEffectBlock, 5)

                byteValue = bytes()
                for k in range(0, len(value)):
                    byteValue += struct.pack("f", value[k])
                
                ctypes.memmove(ctypes.addressof(effectBlock) + posInEffectBlock, byteValue, 0x4 * len(value))
                
                posInEffectBlock += len(value) * 0x4
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "vector4_16"):
                value = [0.0] * (0x4 * 16)
                if (Exporter.shaderManager[indexInShaderManager].param[j].custom):
                    strValue = Exporter.objectInfo.shaders[i].param[currentCustomParam].split(";")
                    for k in range (0, len(strValue)):
                        value[k] = float(strValue[k])
                    currentCustomParam += 1
                else:
                    for k in range(0, len(Exporter.shaderManager[indexInShaderManager].param[j].staticValue)):
                        value[k] = float(Exporter.shaderManager[indexInShaderManager].param[j].staticValue[k])

                Exporter.shaderFX[i]._parameter[j] = Ptr(Exporter.shaderFX[i].effect.parameters.GetOffset() + posInEffectBlock, 5)

                byteValue = bytes()
                for k in range(0, len(value)):
                    byteValue += struct.pack("f", value[k])
                
                ctypes.memmove(ctypes.addressof(effectBlock) + posInEffectBlock, byteValue, 0x4 * len(value))
                
                posInEffectBlock += len(value) * 0x4
            else:
                #TEMP?
                if (Exporter.shaderManager[indexInShaderManager].param[j].custom):
                    currentCustomParam += 1

        for j in range(0, shaderParamSize):
            if (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "texture"):
                Exporter.shaderFX[i]._type[j] = np.ubyte(0)
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "float" or
                  str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "vector4"):
                Exporter.shaderFX[i]._type[j] = np.ubyte(1)
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "matrix"):
                Exporter.shaderFX[i]._type[j] = np.ubyte(4)
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "vector4_6"):
                Exporter.shaderFX[i]._type[j] = np.ubyte(8)
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "vector4_14"):
                Exporter.shaderFX[i]._type[j] = np.ubyte(14)
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "vector4_15"):
                Exporter.shaderFX[i]._type[j] = np.ubyte(15)
            elif (str.lower(Exporter.shaderManager[indexInShaderManager].param[j].type) == "vector4_16"):
                Exporter.shaderFX[i]._type[j] = np.ubyte(16)
            Exporter.shaderFX[i]._paramHash[j] = GetHash(Exporter.shaderManager[indexInShaderManager].param[j].name, True)

            Exporter.shaderGroup._index[i] = Exporter.shaderFX[i].index
            Exporter.shaderGroup._vertexFormat[i] = Exporter.shaderManager[indexInShaderManager].vertexFormat

        ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderFX[i].effect.parameters.GetOffset(), effectBlock, Exporter.shaderFX[i].effect.effectSize)
        effectBlock = 0

        byteParams = bytes()
        for k in range(0, len(Exporter.shaderFX[i]._parameter)):
            byteParams += Exporter.shaderFX[i]._parameter[k].ptr.tobytes()
        ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderFX[i].effect.parameters.GetOffset(), byteParams, Exporter.shaderFX[i].effect.parameterCount * 0x4)
        
        byteParams = bytes()
        for k in range(0, len(Exporter.shaderFX[i]._type)):
            byteParams += Exporter.shaderFX[i]._type[k].tobytes()
        ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderFX[i].effect.parameterTypes.GetOffset(), byteParams, Exporter.shaderFX[i].effect.parameterCount * 0x4)
        
        byteParams = bytes()
        for k in range(0, len(Exporter.shaderFX[i]._paramHash)):
            byteParams += Exporter.shaderFX[i]._paramHash[k].tobytes()
        ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderFX[i].effect.paramsHash.GetOffset(), byteParams, Exporter.shaderFX[i].effect.parameterCount * 0x4)
        
        byteShaderFX = bytes()
        byteShaderFX += Exporter.shaderFX[i]._vmt.tobytes()
        byteShaderFX += Exporter.shaderFX[i].pageMap.ptr.tobytes()
        byteShaderFX += Exporter.shaderFX[i].unk_f8.tobytes()
        byteShaderFX += Exporter.shaderFX[i].drawBucket.tobytes()
        byteShaderFX += Exporter.shaderFX[i].unk_fa.tobytes()
        byteShaderFX += Exporter.shaderFX[i].unk_fb.tobytes()
        byteShaderFX += Exporter.shaderFX[i].unk_fc.tobytes()
        byteShaderFX += Exporter.shaderFX[i].index.tobytes()
        byteShaderFX += Exporter.shaderFX[i].unk_f10.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.parameters.ptr.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.cachedEffect.ptr.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.parameterCount.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.effectSize.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.parameterTypes.ptr.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.hash.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.unkf18.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.unkf1c.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.paramsHash.ptr.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.unkf24.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.unkf28.tobytes()
        byteShaderFX += Exporter.shaderFX[i].effect.unkf2c.tobytes()
        byteShaderFX += Exporter.shaderFX[i].name.ptr.tobytes()
        byteShaderFX += Exporter.shaderFX[i].spsName.ptr.tobytes()
        byteShaderFX += Exporter.shaderFX[i].unk_f4c.tobytes()
        byteShaderFX += Exporter.shaderFX[i].unk_f50.tobytes()
        byteShaderFX += Exporter.shaderFX[i].unk_f54.tobytes()
        byteShaderFX += Exporter.shaderFX[i].unk_f58.tobytes()
        ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderGroup._shader[i].GetOffset(), byteShaderFX, Exporter.shaderFX[i]._structSize)

        ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderFX[i].name.GetOffset(), bytes(Exporter.shaderFX[i]._name.encode()), len(Exporter.shaderFX[i]._name) + 1)
        ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderFX[i].spsName.GetOffset(), bytes(Exporter.shaderFX[i]._sps.encode()), len(Exporter.shaderFX[i]._sps) + 1)

    Exporter.shaderGroup.vertexFormat.data = Ptr(Exporter.cpuLayout.GetPos(shaderSize * 0x4), 5)
    Exporter.shaderGroup.vertexFormat.size = np.ushort(shaderSize)
    Exporter.shaderGroup.vertexFormat.count = np.ushort(shaderSize)
    Exporter.shaderGroup.indexMapping.data = Ptr(Exporter.cpuLayout.GetPos(shaderSize * 0x4), 5)
    Exporter.shaderGroup.indexMapping.size = np.ushort(shaderSize)
    Exporter.shaderGroup.indexMapping.count = np.ushort(shaderSize)

    byteParams = bytes()
    for k in range(0, len(Exporter.shaderGroup._index)):
        byteParams += struct.pack("i", Exporter.shaderGroup._index[k])
    ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderGroup.indexMapping.data.GetOffset(), byteParams, shaderSize * 0x4)

    byteParams = bytes()
    for k in range(0, len(Exporter.shaderGroup._vertexFormat)):
        byteParams += struct.pack("i", Exporter.shaderGroup._vertexFormat[k])
    ctypes.memmove(ctypes.addressof(cpu) + Exporter.shaderGroup.vertexFormat.data.GetOffset(), byteParams, shaderSize * 0x4)
    
    byteGrmShaderGroup = bytes()
    byteGrmShaderGroup += Exporter.shaderGroup._vmt.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.texture.ptr.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.shaders.data.ptr.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.shaders.count.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.shaders.size.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f10.data.ptr.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f10.count.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f10.size.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f18.data.ptr.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f18.count.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f18.size.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f20.data.ptr.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f20.count.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f20.size.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f28.data.ptr.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f28.count.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f28.size.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f30.data.ptr.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f30.count.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f30.size.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f38.data.ptr.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f38.count.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.unk_f38.size.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.vertexFormat.data.ptr.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.vertexFormat.count.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.vertexFormat.size.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.indexMapping.data.ptr.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.indexMapping.count.tobytes()
    byteGrmShaderGroup += Exporter.shaderGroup.indexMapping.size.tobytes()
    ctypes.memmove(ctypes.addressof(cpu) + Exporter.drawable.shaderGroup.GetOffset(), byteGrmShaderGroup, Exporter.shaderGroup._structSize)

    # skel
    boneSize = len(Exporter.objectInfo.skel.bone)
    if (boneSize > 0):
        Exporter.drawable.skeleton = Ptr(Exporter.cpuLayout.GetPos(0x40), 5)
        
        skelData = crSkeletonData()

        bone = []
        for _ in range(0, boneSize):
            bone.append(crBone())

        skelData.bones = Ptr(Exporter.cpuLayout.GetPos(0xe0 * boneSize), 5)

        pos = np.uint(0)

        skelData.usageCount = np.short(1)

        bonesPositionBuffer = [np.ushort(0)] * boneSize
        parentBones = [np.uint(0)] * boneSize

        for i in range(0, boneSize):
            bone[i]._name = np.str_(Exporter.objectInfo.skel.bone[i].name)
            bone[i].name = Ptr(Exporter.cpuLayout.GetPos(bone[i]._name), 5)
            bone[i].boneIndex = np.ushort(Exporter.objectInfo.skel.bone[i].index)
            bone[i].boneId = np.ushort(Exporter.objectInfo.skel.bone[i].id)
            bone[i].mirror = np.ushort(Exporter.objectInfo.skel.bone[i].mirror)
            bone[i].offset.x = np.float32(Exporter.objectInfo.skel.bone[i].localOffset.x)
            bone[i].offset.y = np.float32(Exporter.objectInfo.skel.bone[i].localOffset.y)
            bone[i].offset.z = np.float32(Exporter.objectInfo.skel.bone[i].localOffset.z)

            bonesPositionBuffer[Exporter.objectInfo.skel.bone[i].posInTheHierarchy] = np.ushort(bone[i].boneIndex)
            bone[i]._boneOffset = skelData.bones.GetOffset() + np.uint(pos)

            bone[i].rotationEuler.x = np.float32(Exporter.objectInfo.skel.bone[i].rotationEuler.x)
            bone[i].rotationEuler.y = np.float32(Exporter.objectInfo.skel.bone[i].rotationEuler.y)
            bone[i].rotationEuler.z = np.float32(Exporter.objectInfo.skel.bone[i].rotationEuler.z)

            bone[i].rotationQuaternion.x = np.float32(Exporter.objectInfo.skel.bone[i].rotationQuaternion.x)
            bone[i].rotationQuaternion.y = np.float32(Exporter.objectInfo.skel.bone[i].rotationQuaternion.y)
            bone[i].rotationQuaternion.z = np.float32(Exporter.objectInfo.skel.bone[i].rotationQuaternion.z)
            bone[i].rotationQuaternion.w = np.float32(Exporter.objectInfo.skel.bone[i].rotationQuaternion.w)

            bone[i].scale.x = np.float32(Exporter.objectInfo.skel.bone[i].scale.x)
            bone[i].scale.y = np.float32(Exporter.objectInfo.skel.bone[i].scale.y)
            bone[i].scale.z = np.float32(Exporter.objectInfo.skel.bone[i].scale.z)

            bone[i].parentModelOffset.x = np.float32(Exporter.objectInfo.skel.bone[i].worldOffset.x)
            bone[i].parentModelOffset.y = np.float32(Exporter.objectInfo.skel.bone[i].worldOffset.y)
            bone[i].parentModelOffset.z = np.float32(Exporter.objectInfo.skel.bone[i].worldOffset.z)

            bone[i].orient.x = np.float32(Exporter.objectInfo.skel.bone[i].orient.x)
            bone[i].orient.y = np.float32(Exporter.objectInfo.skel.bone[i].orient.y)
            bone[i].orient.z = np.float32(Exporter.objectInfo.skel.bone[i].orient.z)

            bone[i].sorient.x = np.float32(Exporter.objectInfo.skel.bone[i].sorient.x)
            bone[i].sorient.y = np.float32(Exporter.objectInfo.skel.bone[i].sorient.y)
            bone[i].sorient.z = np.float32(Exporter.objectInfo.skel.bone[i].sorient.z)

            bone[i].transMin.x = np.float32(Exporter.objectInfo.skel.bone[i].transMin.x)
            bone[i].transMin.y = np.float32(Exporter.objectInfo.skel.bone[i].transMin.y)
            bone[i].transMin.z = np.float32(Exporter.objectInfo.skel.bone[i].transMin.z)

            bone[i].transMax.x = np.float32(Exporter.objectInfo.skel.bone[i].transMax.x)
            bone[i].transMax.y = np.float32(Exporter.objectInfo.skel.bone[i].transMax.y)
            bone[i].transMax.z = np.float32(Exporter.objectInfo.skel.bone[i].transMax.z)

            bone[i].rotMin.x = np.float32(Exporter.objectInfo.skel.bone[i].rotMin.x)
            bone[i].rotMin.y = np.float32(Exporter.objectInfo.skel.bone[i].rotMin.y)
            bone[i].rotMin.z = np.float32(Exporter.objectInfo.skel.bone[i].rotMin.z)

            bone[i].rotMax.x = np.float32(Exporter.objectInfo.skel.bone[i].rotMax.x)
            bone[i].rotMax.y = np.float32(Exporter.objectInfo.skel.bone[i].rotMax.y)
            bone[i].rotMax.z = np.float32(Exporter.objectInfo.skel.bone[i].rotMax.z)

            for j in range(0, len(Exporter.objectInfo.skel.bone[i].flags)):
                if (Exporter.objectInfo.skel.bone[i].flags[j] == "LockRotationXYZ"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 0, 1, 1))
                    bone[i].rotFlags += np.ubyte(3)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LockRotationX"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 1, 1, 1))
                    bone[i].rotFlags += np.ubyte(1)
                    skelData.rotLockCount += np.ushort(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LockRotationY"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 2, 1, 1))
                    bone[i].rotFlags += np.ubyte(1)
                    skelData.rotLockCount += np.ushort(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LockRotationZ"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 3, 1, 1))
                    bone[i].rotFlags += np.ubyte(1)
                    skelData.rotLockCount += np.ushort(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LimitRotationX"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 4, 1, 1))
                    bone[i].rotFlags += np.ubyte(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LimitRotationY"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 5, 1, 1))
                    bone[i].rotFlags += np.ubyte(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LimitRotationZ"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 6, 1, 1))
                    bone[i].rotFlags += np.ubyte(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LockTranslationX"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 7, 1, 1))
                    bone[i].transFlags += np.ubyte(1)
                    skelData.transLockCount += np.ushort(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LockTranslationY"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 8, 1, 1))
                    bone[i].transFlags += np.ubyte(1)
                    skelData.transLockCount += np.ushort(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LockTranslationZ"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 9, 1, 1))
                    bone[i].transFlags += np.ubyte(1)
                    skelData.transLockCount += np.ushort(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LimitTranslationX"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 10, 1, 1))
                    bone[i].transFlags += np.ubyte(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LimitTranslationY"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 11, 1, 1))
                    bone[i].transFlags += np.ubyte(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LimitTranslationZ"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 12, 1, 1))
                    bone[i].transFlags += np.ubyte(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LockScaleX"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 13, 1, 1))
                    bone[i].scaleFlags += np.ubyte(1)
                    skelData.scaleLockCount += np.ushort(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LockScaleY"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 14, 1, 1))
                    bone[i].scaleFlags += np.ubyte(1)
                    skelData.scaleLockCount += np.ushort(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LockScaleZ"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 15, 1, 1))
                    bone[i].scaleFlags += np.ubyte(1)
                    skelData.scaleLockCount += np.ushort(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LimitScaleX"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 16, 1, 1))
                    bone[i].scaleFlags += np.ubyte(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LimitScaleY"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 17, 1, 1))
                    bone[i].scaleFlags += np.ubyte(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "LimitScaleZ"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 18, 1, 1))
                    bone[i].scaleFlags += np.ubyte(1)
                elif (Exporter.objectInfo.skel.bone[i].flags[j] == "Invisible"):
                    bone[i].flags = np.uint(SetBit(bone[i].flags, 19, 1, 1))
                    bone[i].scaleFlags += np.ubyte(1)

            if (Exporter.objectInfo.skel.bone[i].posInTheHierarchy != 0):
                boneIndex = bonesPositionBuffer[Exporter.objectInfo.skel.bone[i].posInTheHierarchy - 1]
                bone[i].pastOnHierarchy = Ptr(bone[boneIndex]._boneOffset, 5)
                parentBones[i] = np.uint(bonesPositionBuffer[Exporter.objectInfo.skel.bone[i].posInTheHierarchy - 1])

            pos += np.uint(bone[i]._structSize)
            if (i != boneSize - 1):
                if (Exporter.objectInfo.skel.bone[i].posInTheHierarchy == Exporter.objectInfo.skel.bone[i + 1].posInTheHierarchy):
                    bone[i].parallelOnHierarchy = Ptr(pos + skelData.bones.GetOffset(), 5)
                elif (Exporter.objectInfo.skel.bone[i].posInTheHierarchy + 1 == Exporter.objectInfo.skel.bone[i + 1].posInTheHierarchy):
                    bone[i].nextOnHierarchy = Ptr(pos + skelData.bones.GetOffset(), 5)
                else:
                    boneIndex = bonesPositionBuffer[Exporter.objectInfo.skel.bone[i + 1].posInTheHierarchy]
                    bone[boneIndex].parallelOnHierarchy = Ptr(pos + skelData.bones.GetOffset(), 5)

        pos = np.uint(0)
        for i in range(0, boneSize):
            byteBone = bytes()
            byteBone += bone[i].name.ptr.tobytes()
            byteBone += bone[i].flags.tobytes()
            byteBone += bone[i].parallelOnHierarchy.ptr.tobytes()
            byteBone += bone[i].nextOnHierarchy.ptr.tobytes()
            byteBone += bone[i].pastOnHierarchy.ptr.tobytes()
            byteBone += bone[i].boneIndex.tobytes()
            byteBone += bone[i].boneId.tobytes()
            byteBone += bone[i].mirror.tobytes()
            byteBone += bone[i].transFlags.tobytes()
            byteBone += bone[i].rotFlags.tobytes()
            byteBone += bone[i].scaleFlags.tobytes()
            byteBone += bone[i].unk_f1d.tobytes()
            byteBone += bone[i].unk_f1e.tobytes()
            byteBone += bone[i].unk_f1f.tobytes()
            byteBone += bone[i].offset.x.tobytes()
            byteBone += bone[i].offset.y.tobytes()
            byteBone += bone[i].offset.z.tobytes()
            byteBone += bone[i].hash.tobytes()
            byteBone += bone[i].rotationEuler.x.tobytes()
            byteBone += bone[i].rotationEuler.y.tobytes()
            byteBone += bone[i].rotationEuler.z.tobytes()
            byteBone += bone[i].rotationEuler.w.tobytes()
            byteBone += bone[i].rotationQuaternion.x.tobytes()
            byteBone += bone[i].rotationQuaternion.y.tobytes()
            byteBone += bone[i].rotationQuaternion.z.tobytes()
            byteBone += bone[i].rotationQuaternion.w.tobytes()
            byteBone += bone[i].scale.x.tobytes()
            byteBone += bone[i].scale.y.tobytes()
            byteBone += bone[i].scale.z.tobytes()
            byteBone += bone[i].unk_f5c.tobytes()
            byteBone += bone[i].parentModelOffset.x.tobytes()
            byteBone += bone[i].parentModelOffset.y.tobytes()
            byteBone += bone[i].parentModelOffset.z.tobytes()
            byteBone += bone[i].parentModelOffset.w.tobytes()
            byteBone += bone[i].orient.x.tobytes()
            byteBone += bone[i].orient.y.tobytes()
            byteBone += bone[i].orient.z.tobytes()
            byteBone += bone[i].orient.w.tobytes()
            byteBone += bone[i].sorient.x.tobytes()
            byteBone += bone[i].sorient.y.tobytes()
            byteBone += bone[i].sorient.z.tobytes()
            byteBone += bone[i].sorient.w.tobytes()
            byteBone += bone[i].transMin.x.tobytes()
            byteBone += bone[i].transMin.y.tobytes()
            byteBone += bone[i].transMin.z.tobytes()
            byteBone += bone[i].transMin.w.tobytes()
            byteBone += bone[i].transMax.x.tobytes()
            byteBone += bone[i].transMax.y.tobytes()
            byteBone += bone[i].transMax.z.tobytes()
            byteBone += bone[i].transMax.w.tobytes()
            byteBone += bone[i].rotMin.x.tobytes()
            byteBone += bone[i].rotMin.y.tobytes()
            byteBone += bone[i].rotMin.z.tobytes()
            byteBone += bone[i].rotMin.w.tobytes()
            byteBone += bone[i].rotMax.x.tobytes()
            byteBone += bone[i].rotMax.y.tobytes()
            byteBone += bone[i].rotMax.z.tobytes()
            byteBone += bone[i].rotMax.w.tobytes()
            byteBone += bone[i].jointData.ptr.tobytes()
            byteBone += bone[i].unk_fD4.tobytes()
            byteBone += bone[i].unk_fD8.tobytes()
            byteBone += bone[i].unk_fDC.tobytes()
            ctypes.memmove(ctypes.addressof(cpu) + skelData.bones.GetOffset() + pos.item(), byteBone, bone[i]._structSize)
            
            ctypes.memmove(ctypes.addressof(cpu) + bone[i].name.GetOffset(), bytes(bone[i]._name.encode()), len(bone[i]._name) + 1)

            pos += np.uint(bone[i]._structSize)

        for i in range(0, len(Exporter.objectInfo.skel.flags)):
            if (Exporter.objectInfo.skel.flags[i] == "HaveBoneWorldOrient"):
                skelData.flags = np.uint(SetBit(skelData.flags, 2, 1, 1)) # orient + inverse orient
            elif (Exporter.objectInfo.skel.flags[i] == "HaveBoneMappings"):
                skelData.flags = np.uint(SetBit(skelData.flags, 1, 1, 1)) # bone mapping
            elif (Exporter.objectInfo.skel.flags[i] == "AuthoredOrientation"):
                skelData.flags = np.uint(SetBit(skelData.flags, 3, 1, 1))
            elif (Exporter.objectInfo.skel.flags[i] == "unk0"):
                skelData.flags = np.uint(SetBit(skelData.flags, 0, 1, 1))

        skelData.parentBoneIndices = Ptr(Exporter.cpuLayout.GetPos(0x4 * boneSize), 5)
        byteParentBones = bytes()
        for i in range(0, len(parentBones)):
            byteParentBones += parentBones[i].tobytes()
        ctypes.memmove(ctypes.addressof(cpu) + skelData.parentBoneIndices.GetOffset(), byteParentBones, boneSize * 0x4)

        matrix = Matrix()

        if (GetValueFromBits(skelData.flags, 1, 2) != 0):
            skelData.boneWorldOrient = Ptr(Exporter.cpuLayout.GetPos(0x80 * boneSize), 5)
            skelData.boneWorldOrientInverted = Ptr(skelData.boneWorldOrient.GetOffset() + (0x40 * boneSize), 5)

            pos = np.uint(skelData.boneWorldOrient.GetOffset())
            for i in range(0, boneSize):
                matrix.SetRotation(Vector3(bone[i].orient.x, bone[i].orient.y, bone[i].orient.z), True)
                byteMatrix = bytes()
                byteMatrix += matrix.m10.tobytes()
                byteMatrix += matrix.m11.tobytes()
                byteMatrix += matrix.m12.tobytes()
                byteMatrix += matrix.m13.tobytes()
                byteMatrix += matrix.m20.tobytes()
                byteMatrix += matrix.m21.tobytes()
                byteMatrix += matrix.m22.tobytes()
                byteMatrix += matrix.m23.tobytes()
                byteMatrix += matrix.m30.tobytes()
                byteMatrix += matrix.m31.tobytes()
                byteMatrix += matrix.m32.tobytes()
                byteMatrix += matrix.m33.tobytes()
                byteMatrix += matrix.m40.tobytes()
                byteMatrix += matrix.m41.tobytes()
                byteMatrix += matrix.m42.tobytes()
                byteMatrix += matrix.m43.tobytes()
                ctypes.memmove(ctypes.addressof(cpu) + pos.item(), byteMatrix, 0x40)

                matrix.SetRotation(Vector3(bone[i].orient.x * -1, bone[i].orient.y * -1, bone[i].orient.z * -1), True)
                byteMatrix = bytes()
                byteMatrix += matrix.m10.tobytes()
                byteMatrix += matrix.m11.tobytes()
                byteMatrix += matrix.m12.tobytes()
                byteMatrix += matrix.m13.tobytes()
                byteMatrix += matrix.m20.tobytes()
                byteMatrix += matrix.m21.tobytes()
                byteMatrix += matrix.m22.tobytes()
                byteMatrix += matrix.m23.tobytes()
                byteMatrix += matrix.m30.tobytes()
                byteMatrix += matrix.m31.tobytes()
                byteMatrix += matrix.m32.tobytes()
                byteMatrix += matrix.m33.tobytes()
                byteMatrix += matrix.m40.tobytes()
                byteMatrix += matrix.m41.tobytes()
                byteMatrix += matrix.m42.tobytes()
                byteMatrix += matrix.m43.tobytes()
                ctypes.memmove(ctypes.addressof(cpu) + pos.item() + (0x40 * boneSize), byteMatrix, 0x40)

                pos += 0x40

        skelData.boneLocalTransforms = Ptr(Exporter.cpuLayout.GetPos(0x40 * boneSize), 5)
        pos = np.uint(skelData.boneLocalTransforms.GetOffset())
        for i in range(0, boneSize):
            matrix.SetRotationFromQuaternion(bone[i].rotationQuaternion, True)
            matrix.m40 = np.float32(bone[i].offset.x)
            matrix.m41 = np.float32(bone[i].offset.y)
            matrix.m42 = np.float32(bone[i].offset.z)
            byteMatrix = bytes()
            byteMatrix += matrix.m10.tobytes()
            byteMatrix += matrix.m11.tobytes()
            byteMatrix += matrix.m12.tobytes()
            byteMatrix += matrix.m13.tobytes()
            byteMatrix += matrix.m20.tobytes()
            byteMatrix += matrix.m21.tobytes()
            byteMatrix += matrix.m22.tobytes()
            byteMatrix += matrix.m23.tobytes()
            byteMatrix += matrix.m30.tobytes()
            byteMatrix += matrix.m31.tobytes()
            byteMatrix += matrix.m32.tobytes()
            byteMatrix += matrix.m33.tobytes()
            byteMatrix += matrix.m40.tobytes()
            byteMatrix += matrix.m41.tobytes()
            byteMatrix += matrix.m42.tobytes()
            byteMatrix += matrix.m43.tobytes()
            ctypes.memmove(ctypes.addressof(cpu) + pos.item(), byteMatrix, 0x40)

            pos += 0x40
        
        skelData.boneCount = np.ushort(boneSize)

        if (GetValueFromBits(skelData.flags, 1, 1) != 0):
            skelData.boneIdMappings.data = Ptr(Exporter.cpuLayout.GetPos(0x4 * boneSize), 5)
            skelData.boneIdMappings.count = np.ushort(boneSize)
            skelData.boneIdMappings.size = np.ushort(boneSize)

            boneIdBuffer = []
            for i in range(0, skelData.boneIdMappings.count):
                boneIdBuffer.append(np.ushort(bone[i].boneId))
            boneIdBuffer.sort()

            for i in range(0, skelData.boneIdMappings.count):
                ctypes.memmove(ctypes.addressof(cpu) + skelData.boneIdMappings.data.GetOffset() + (i * 0x4), boneIdBuffer[i].tobytes(), 2)
                for j in range(0, skelData.boneIdMappings.count):
                    if (boneIdBuffer[i] == bone[j].boneId):
                        ctypes.memmove(ctypes.addressof(cpu) + (skelData.boneIdMappings.data.GetOffset() + (i * 0x4)) + 0x2, bone[j].boneIndex.tobytes(), 2)

        skelData.jointDataFile._vmt = VirtualTables.joint
        byteSkelData = bytes()
        byteSkelData += skelData.bones.ptr.tobytes()
        byteSkelData += skelData.parentBoneIndices.ptr.tobytes()
        byteSkelData += skelData.boneWorldOrient.ptr.tobytes()
        byteSkelData += skelData.boneWorldOrientInverted.ptr.tobytes()
        byteSkelData += skelData.boneLocalTransforms.ptr.tobytes()
        byteSkelData += skelData.boneCount.tobytes()
        byteSkelData += skelData.transLockCount.tobytes()
        byteSkelData += skelData.rotLockCount.tobytes()
        byteSkelData += skelData.scaleLockCount.tobytes()
        byteSkelData += skelData.flags.tobytes()
        byteSkelData += skelData.boneIdMappings.data.ptr.tobytes()
        byteSkelData += skelData.boneIdMappings.count.tobytes()
        byteSkelData += skelData.boneIdMappings.size.tobytes()
        byteSkelData += skelData.usageCount.tobytes()
        byteSkelData += skelData.unk_f2a.tobytes()
        byteSkelData += skelData.CRC.tobytes()
        byteSkelData += skelData.jointDataFileName.ptr.tobytes()
        byteSkelData += skelData.jointDataFile._vmt.tobytes()
        byteSkelData += skelData.jointDataFile.jointData.data.ptr.tobytes()
        byteSkelData += skelData.jointDataFile.jointData.count.tobytes()
        byteSkelData += skelData.jointDataFile.jointData.size.tobytes()
        ctypes.memmove(ctypes.addressof(cpu) + Exporter.drawable.skeleton.GetOffset(), byteSkelData, skelData._structSize)

    # model
    for i in range(0, 4):
        if (i > 0): #TEMP!
            Exporter.drawable.lodGroup.models[i] = Ptr()
            Exporter.drawable.lodGroup.shaderUseMask[i] = np.int32(-1)
            continue

        meshSize = len(Exporter.objectInfo.lodGroups[i].meshes)

        if (meshSize == 0):
            Exporter.drawable.lodGroup.models[i] = Ptr()
            Exporter.drawable.lodGroup.shaderUseMask[i] = np.int32(-1)
            continue

        Exporter.drawable.lodGroup.models[i] = Ptr(Exporter.cpuLayout.GetPos(0x8), 5)
        Exporter.drawable.lodGroup.shaderUseMask[i] = np.int32(1)
        Exporter.drawable._model[i].data = Ptr(Exporter.cpuLayout.GetPos(meshSize * 0x4), 5)
        Exporter.drawable._model[i].size = np.ushort(meshSize)
        Exporter.drawable._model[i].count = np.ushort(meshSize)

        byteModel = bytes()
        byteModel += Exporter.drawable._model[i].data.ptr.tobytes()
        byteModel += Exporter.drawable._model[i].count.tobytes()
        byteModel += Exporter.drawable._model[i].size.tobytes()
        ctypes.memmove(ctypes.addressof(cpu) + Exporter.drawable.lodGroup.models[i].GetOffset(), byteModel, 0x8)

        model = []
        for j in range(0, meshSize):
            model.append(GrmModel())

        for j in range(0, meshSize):
            Exporter.drawable._modelPtr[j] = Ptr(Exporter.cpuLayout.GetPos(0x1c), 5)

            model[j]._vmt = VirtualTables.grmModel

            geometrySize = len(Exporter.objectInfo.lodGroups[i].meshes[j].geometry)

            model[j].geometries.data = Ptr(Exporter.cpuLayout.GetPos(geometrySize * 0x4), 5)
            model[j].geometries.size = np.ushort(geometrySize)
            model[j].geometries.count = np.ushort(geometrySize)
            model[j]._geometry = [0] * model[j].geometries.count

            if (not Exporter.objectInfo.lodGroups[i].meshes[j].skinned):
                boundsSize = len(Exporter.objectInfo.lodGroups[i].meshes[j].bounds)
                model[j].bounds = Ptr(Exporter.cpuLayout.GetPos(boundsSize * 0x10), 5)

                byteBounds = bytes()
                for k in range(0, len(Exporter.objectInfo.lodGroups[i].meshes[j].bounds)):
                    byteBounds += struct.pack("f", Exporter.objectInfo.lodGroups[i].meshes[j].bounds[k].x)
                    byteBounds += struct.pack("f", Exporter.objectInfo.lodGroups[i].meshes[j].bounds[k].y)
                    byteBounds += struct.pack("f", Exporter.objectInfo.lodGroups[i].meshes[j].bounds[k].z)
                    byteBounds += struct.pack("f", Exporter.objectInfo.lodGroups[i].meshes[j].bounds[k].w)

                ctypes.memmove(ctypes.addressof(cpu) + model[j].bounds.GetOffset(), byteBounds, boundsSize * 0x10)

            model[j].shaderMappings = Ptr(Exporter.cpuLayout.GetPos(geometrySize * 0x2), 5)
            
            model[j]._mtlIndex = [0] * geometrySize
            for k in range(0, geometrySize):
                model[j]._mtlIndex[k] = np.ushort(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].mtlIndex)

            byteMtlIndices = bytes()
            for k in range(0, len(model[j]._mtlIndex)):
                byteMtlIndices += model[j]._mtlIndex[k].tobytes()

            ctypes.memmove(ctypes.addressof(cpu) + model[j].shaderMappings.GetOffset(), byteMtlIndices, geometrySize * 0x2)

            boneSize = len(Exporter.objectInfo.skel.bone)
            model[j].offsetCount = np.ubyte(boneSize)
            model[j].skinned = np.ubyte(Exporter.objectInfo.lodGroups[i].meshes[j].skinned)
            model[j].unk_f16 = np.ubyte(0xcd)
            model[j].boneIndex = np.ubyte(Exporter.objectInfo.lodGroups[i].meshes[j].boneIndex)
            model[j].unk_f18 = np.ubyte(0)
            model[j].haveOffsetCount = np.ubyte(model[j].skinned) #TEMP?
            model[j].shaderMappingCount = np.ushort(len(model[j]._mtlIndex))

            geometry = []
            for k in range(0, model[j].geometries.count):
                geometry.append(grmGeometry())
            vertexBuffer = []
            for k in range(0, model[j].geometries.count):
                vertexBuffer.append(grcVertexBufferD3D())
            indexBuffer = []
            for k in range(0, model[j].geometries.count):
                indexBuffer.append(grcIndexBufferD3D())
            vertexDeclaration = []
            for k in range(0, model[j].geometries.count):
                vertexDeclaration.append(rageVertexDeclaration())

            for k in range(0, model[j].geometries.count):
                model[j]._geometry[k] = Ptr(Exporter.cpuLayout.GetPos(0x4c), 5)

                bufferIndex = 0

                geometry[k]._vmt = VirtualTables.grmGeometry

                vertices = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices
                indices = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].indices

                geometry[k].vertexCount = np.ushort(len(vertices))
                geometry[k].indexCount = np.uint(len(indices))
                geometry[k].indicesPerFace = np.ushort(3)
                geometry[k].faceCount = np.uint(geometry[k].indexCount / geometry[k].indicesPerFace)
                geometry[k].vertexBuffers[bufferIndex] = Ptr(Exporter.cpuLayout.GetPos(0x40), 5)
                geometry[k].indexBuffers[bufferIndex] = Ptr(Exporter.cpuLayout.GetPos(0x30), 5)
                
                if (Exporter.objectInfo.lodGroups[i].meshes[j].skinned):
                    usedBlendIndexSize = len(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].usedBlendIndex)

                    geometry[k].boneMapping = Ptr(Exporter.cpuLayout.GetPos(usedBlendIndexSize * 0x2), 5)
                    geometry[k].boneCount = np.ushort(usedBlendIndexSize)

                    byteBlendIndices = bytes()
                    for n in range(0, usedBlendIndexSize):
                        byteBlendIndices += Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].usedBlendIndex[n].tobytes()

                    ctypes.memmove(ctypes.addressof(cpu) + geometry[k].boneMapping.GetOffset(), byteBlendIndices, usedBlendIndexSize * 0x2)

                vertexStrides = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertexStride

                geometry[k].vertexStride = np.ushort(vertexStrides)

                vertexBuffer[k]._vmt = VirtualTables.grcVertexBufferD3D
                vertexBuffer[k].vertexCount = np.ushort(len(vertices))
                vertexBuffer[k].lockedData = Ptr(Exporter.gpuLayout.GetPos(len(vertices) * vertexStrides), 6)
                vertexBuffer[k].vertexSize = np.uint(vertexStrides)
                vertexBuffer[k].declarations = Ptr(Exporter.cpuLayout.GetPos(0x10), 5)
                vertexBuffer[k].vertexData = vertexBuffer[k].lockedData
                ctypes.memset(vertexBuffer[k].cacheHandle, 0xcd, 0x20)

                vertexDeclaration[k].usedElements = np.uint(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertexFormat)
                vertexDeclaration[k].elementsCount = np.ubyte(0)
                for n in range(0, 16):
                    if (GetValueFromBits(vertexDeclaration[k].usedElements, 1, n) != 0):
                        vertexDeclaration[k].elementsCount += np.ubyte(1)
                vertexDeclaration[k].totalSize = np.ubyte(vertexBuffer[k].vertexSize)
                vertexDeclaration[k].elementTypes = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].types

                indexBuffer[k]._vmt = VirtualTables.grcIndexBufferD3D
                indexBuffer[k].indexCount = np.uint(len(indices))
                indexBuffer[k].indexData = Ptr(Exporter.gpuLayout.GetPos(len(indices) * 2), 6)

                byteIndices = bytes()
                for n in range(0, len(indices)):
                    byteIndices += np.ushort(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].indices[n]).tobytes()
                ctypes.memmove(ctypes.addressof(gpu) + indexBuffer[k].indexData.GetOffset(), byteIndices, np.uint64(len(indices) * 0x2))

                ctypes.memset(indexBuffer[k].cacheHandle, 0xcd, 0x20)

                for n in range(0, len(vertices)):
                    pos = np.uint64(vertexBuffer[k].vertexData.GetOffset() + (n * vertexBuffer[k].vertexSize))
                    for m in range(0, 16):
                        used = GetValueFromBits(vertexDeclaration[k].usedElements, 1, m)
                        type = GetValueFromBits(vertexDeclaration[k].elementTypes, 4, m * 4)
                        
                        val = Vector4()
                        if (used == 0):
                            continue

                        if (m == 0):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].position.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].position.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].position.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].position.w)
                        elif (m == 1):
                            val.x = np.ubyte(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].blendWeight[0] * 255.5)
                            val.y = np.ubyte(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].blendWeight[1] * 255.5)
                            val.z = np.ubyte(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].blendWeight[2] * 255.5)
                            val.w = np.ubyte(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].blendWeight[3] * 255.5)
                        elif (m == 2):
                            for o in range(0, 4):
                                for p in range(0, len(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].usedBlendIndex)):
                                    if (Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].blendIndex[o] ==
                                        Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].usedBlendIndex[p]):

                                        Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].blendIndex[o] = p
                                        break
                            val.x = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].blendIndex[0]
                            val.y = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].blendIndex[1]
                            val.z = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].blendIndex[2]
                            val.w = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].blendIndex[3]
                        elif (m == 3):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].normal.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].normal.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].normal.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].normal.w)
                        elif (m == 4):
                            val.x = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].color[0]
                            val.y = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].color[1]
                            val.z = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].color[2]
                            val.w = Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].color[3]
                        elif (m == 5):
                            val.x = np.ubyte(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].specular[0]).tobytes()
                            val.y = np.ubyte(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].specular[1]).tobytes()
                            val.z = np.ubyte(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].specular[2]).tobytes()
                            val.w = np.ubyte(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].specular[3]).tobytes()
                        elif (m == 6):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv0.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv0.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv0.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv0.w)
                        elif (m == 7):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv1.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv1.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv1.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv1.w)
                        elif (m == 8):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv2.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv2.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv2.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv2.w)
                        elif (m == 9):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv3.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv3.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv3.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv3.w)
                        elif (m == 10):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv4.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv4.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv4.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv4.w)
                        elif (m == 11):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv5.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv5.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv5.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv5.w)
                        elif (m == 12):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv6.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv6.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv6.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv6.w)
                        elif (m == 13):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv7.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv7.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv7.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].uv7.w)
                        elif (m == 14):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].tangent.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].tangent.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].tangent.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].tangent.w)
                        elif (m == 15):
                            val.x = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].binormal.x)
                            val.y = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].binormal.y)
                            val.z = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].binormal.z)
                            val.w = np.float32(Exporter.objectInfo.lodGroups[i].meshes[j].geometry[k].vertices[n].binormal.w)
                        
                        tmpVal = [0] * 4
                        if (type == 0): # float16
                            tmpVal[0] = float(val.x)
                            byteValue = bytes()
                            for h in range(0, len(tmpVal)):
                                byteValue += struct.pack("f", tmpVal[h])
                            ctypes.memmove(ctypes.addressof(gpu) + pos.item(), byteValue, 0x2)
                            pos += np.uint64(0x2)
                        elif (type == 1): # float16_2
                            tmpVal[0] = float(val.x)
                            tmpVal[1] = float(val.y)
                            byteValue = bytes()
                            for h in range(0, len(tmpVal)):
                                byteValue += struct.pack("f", tmpVal[h])
                            ctypes.memmove(ctypes.addressof(gpu) + pos.item(), byteValue, 0x4)
                            pos += np.uint64(0x4)
                        elif (type == 2): # float16_3
                            tmpVal[0] = float(val.x)
                            tmpVal[1] = float(val.y)
                            tmpVal[2] = float(val.z)
                            byteValue = bytes()
                            for h in range(0, len(tmpVal)):
                                byteValue += struct.pack("f", tmpVal[h])
                            ctypes.memmove(ctypes.addressof(gpu) + pos.item(), byteValue, 0x6)
                            pos += np.uint64(0x6)
                        elif (type == 3): # float16_4
                            tmpVal[0] = float(val.x)
                            tmpVal[1] = float(val.y)
                            tmpVal[2] = float(val.z)
                            tmpVal[3] = float(val.w)
                            byteValue = bytes()
                            for h in range(0, len(tmpVal)):
                                byteValue += struct.pack("f", tmpVal[h])
                            ctypes.memmove(ctypes.addressof(gpu) + pos.item(), byteValue, 0x8)
                            pos += np.uint64(0x8)
                        elif (type == 4): # float
                            ctypes.memmove(ctypes.addressof(gpu) + pos.item(), val.x.tobytes(), 0x4)
                            pos += np.uint64(0x4)
                        elif (type == 5): # float2
                            byteValue = bytes()
                            byteValue += val.x.tobytes()
                            byteValue += val.y.tobytes()
                            ctypes.memmove(ctypes.addressof(gpu) + pos.item(), byteValue, 0x8)
                            pos += np.uint64(0x8)
                        elif (type == 6): # float3
                            byteValue = bytes()
                            byteValue += val.x.tobytes()
                            byteValue += val.y.tobytes()
                            byteValue += val.z.tobytes()
                            ctypes.memmove(ctypes.addressof(gpu) + pos.item(), byteValue, 0xc)
                            pos += np.uint64(0xc)
                        elif (type == 7): # float4
                            byteValue = bytes()
                            byteValue += val.x.tobytes()
                            byteValue += val.y.tobytes()
                            byteValue += val.z.tobytes()
                            byteValue += val.w.tobytes()
                            ctypes.memmove(ctypes.addressof(gpu) + pos.item(), byteValue, 0x10)
                            pos += np.uint64(0x10)
                        elif (type == 9): # d3dcolor, blendWeight
                            tmpVal = np.ubyte(val.x) | np.ubyte(val.y) << 8 | np.ubyte(val.z) << 16 | np.ubyte(val.w) << 24
                            ctypes.memmove(ctypes.addressof(gpu) + pos.item(), tmpVal.tobytes(), 0x4)
                                
                            pos += np.uint64(0x4)

                byteGeometry = bytes()
                byteGeometry += geometry[k]._vmt.tobytes()
                byteGeometry += geometry[k].vertexDeclaration.ptr.tobytes()
                byteGeometry += geometry[k].unk_f8.tobytes()
                byteGeometry += geometry[k].vertexBuffers[0].ptr.tobytes()
                byteGeometry += geometry[k].vertexBuffers[1].ptr.tobytes()
                byteGeometry += geometry[k].vertexBuffers[2].ptr.tobytes()
                byteGeometry += geometry[k].vertexBuffers[3].ptr.tobytes()
                byteGeometry += geometry[k].indexBuffers[0].ptr.tobytes()
                byteGeometry += geometry[k].indexBuffers[1].ptr.tobytes()
                byteGeometry += geometry[k].indexBuffers[2].ptr.tobytes()
                byteGeometry += geometry[k].indexBuffers[3].ptr.tobytes()
                byteGeometry += geometry[k].indexCount.tobytes()
                byteGeometry += geometry[k].faceCount.tobytes()
                byteGeometry += geometry[k].vertexCount.tobytes()
                byteGeometry += geometry[k].indicesPerFace.tobytes()
                byteGeometry += geometry[k].boneMapping.ptr.tobytes()
                byteGeometry += geometry[k].vertexStride.tobytes()
                byteGeometry += geometry[k].boneCount.tobytes()
                byteGeometry += geometry[k]._InstanceVertexDeclarationD3D.ptr.tobytes()
                byteGeometry += geometry[k]._InstanceVertexBufferD3D.ptr.tobytes()
                byteGeometry += geometry[k]._UseGlobalStreamIndex.tobytes()
                ctypes.memmove(ctypes.addressof(cpu) + model[j]._geometry[k].GetOffset(), byteGeometry, geometry[k]._structSize)

                byteVertexBuffer = bytes()
                byteVertexBuffer += vertexBuffer[k]._vmt.tobytes()
                byteVertexBuffer += vertexBuffer[k].vertexCount.tobytes()
                byteVertexBuffer += vertexBuffer[k].locked.tobytes()
                byteVertexBuffer += vertexBuffer[k].unk_f7.tobytes()
                byteVertexBuffer += vertexBuffer[k].lockedData.ptr.tobytes()
                byteVertexBuffer += vertexBuffer[k].vertexSize.tobytes()
                byteVertexBuffer += vertexBuffer[k].declarations.ptr.tobytes()
                byteVertexBuffer += vertexBuffer[k].lockThreadId.tobytes()
                byteVertexBuffer += vertexBuffer[k].vertexData.ptr.tobytes()
                byteVertexBuffer += vertexBuffer[k].vertexBuffer.ptr.tobytes()
                byteVertexBuffer += vertexBuffer[k].cacheHandle
                ctypes.memmove(ctypes.addressof(cpu) + geometry[k].vertexBuffers[bufferIndex].GetOffset(), byteVertexBuffer, vertexBuffer[k]._structSize)

                byteIndexBuffer = bytes()
                byteIndexBuffer += indexBuffer[k]._vmt.tobytes()
                byteIndexBuffer += indexBuffer[k].indexCount.tobytes()
                byteIndexBuffer += indexBuffer[k].indexData.ptr.tobytes()
                byteIndexBuffer += indexBuffer[k].indexBufferBuffer.ptr.tobytes()
                byteIndexBuffer += indexBuffer[k].cacheHandle
                ctypes.memmove(ctypes.addressof(cpu) + geometry[k].indexBuffers[bufferIndex].GetOffset(), byteIndexBuffer, indexBuffer[k]._structSize)

                byteVertexDeclaration = bytes()
                byteVertexDeclaration += vertexDeclaration[k].usedElements.tobytes()
                byteVertexDeclaration += vertexDeclaration[k].totalSize.tobytes()
                byteVertexDeclaration += vertexDeclaration[k].unk_f6.tobytes()
                byteVertexDeclaration += vertexDeclaration[k].storeNormalsDataFirst.tobytes()
                byteVertexDeclaration += vertexDeclaration[k].elementsCount.tobytes()
                byteVertexDeclaration += vertexDeclaration[k].elementTypes.tobytes()
                ctypes.memmove(ctypes.addressof(cpu) + vertexBuffer[k].declarations.GetOffset(), byteVertexDeclaration, 0x10)

            byteModel = bytes()
            byteModel += model[j]._vmt.tobytes()
            byteModel += model[j].geometries.data.ptr.tobytes()
            byteModel += model[j].geometries.count.tobytes()
            byteModel += model[j].geometries.size.tobytes()
            byteModel += model[j].bounds.ptr.tobytes()
            byteModel += model[j].shaderMappings.ptr.tobytes()
            byteModel += model[j].offsetCount.tobytes()
            byteModel += model[j].skinned.tobytes()
            byteModel += model[j].unk_f16.tobytes()
            byteModel += model[j].boneIndex.tobytes()
            byteModel += model[j].unk_f18.tobytes()
            byteModel += model[j].haveOffsetCount.tobytes()
            byteModel += model[j].shaderMappingCount.tobytes()
            ctypes.memmove(ctypes.addressof(cpu) + Exporter.drawable._modelPtr[i].GetOffset(), byteModel, model[j]._structSize)

            byteModelGeometry = bytes()
            for k in range(0, len(model[j]._geometry)):
                byteModelGeometry += model[j]._geometry[k].ptr.tobytes()
            ctypes.memmove(ctypes.addressof(cpu) + model[j].geometries.data.GetOffset(), byteModelGeometry, model[j].geometries.count * 0x4)

        ctypes.memmove(ctypes.addressof(cpu) + Exporter.drawable._model[i].data.GetOffset(), Exporter.drawable._modelPtr[i].ptr.tobytes(), meshSize * 0x4)

    __pad = np.uint(0x7f800001)

    Exporter.drawable.lodGroup.aabbMin.w = __pad.tobytes()

    Exporter.drawable.lodGroup.aabbMax.w = __pad.tobytes()

    Exporter.drawable.lodGroup.center.w = __pad.tobytes()

    for i in range(0, 4):
        Exporter.drawable.lodGroup.lodDist[i] = 9999.0 #TEMP?

    byteGtaDrawable = bytes()
    byteGtaDrawable += Exporter.drawable._vmt.tobytes()
    byteGtaDrawable += Exporter.drawable.pageMap.ptr.tobytes()
    byteGtaDrawable += Exporter.drawable.shaderGroup.ptr.tobytes()
    byteGtaDrawable += Exporter.drawable.skeleton.ptr.tobytes()
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.center.x).tobytes()
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.center.y).tobytes()
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.center.z).tobytes()
    byteGtaDrawable += Exporter.drawable.lodGroup.center.w
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.aabbMin.x).tobytes()
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.aabbMin.y).tobytes()
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.aabbMin.z).tobytes()
    byteGtaDrawable += Exporter.drawable.lodGroup.aabbMin.w
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.aabbMax.x).tobytes()
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.aabbMax.y).tobytes()
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.aabbMax.z).tobytes()
    byteGtaDrawable += Exporter.drawable.lodGroup.aabbMax.w
    for i in range(0, len(Exporter.drawable.lodGroup.models)):
        byteGtaDrawable += Exporter.drawable.lodGroup.models[i].ptr.tobytes()
    for i in range(0, len(Exporter.drawable.lodGroup.lodDist)):
        byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.lodDist[i])
    for i in range(0, len(Exporter.drawable.lodGroup.shaderUseMask)):
        byteGtaDrawable += Exporter.drawable.lodGroup.shaderUseMask[i].tobytes()
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.radius)
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.unk_f64_1)
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.unk_f64_2)
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.unk_f64_3)
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.unk_f68)
    byteGtaDrawable += np.float32(Exporter.drawable.lodGroup.unk_f6c)
    ctypes.memmove(ctypes.addressof(cpu), byteGtaDrawable, Exporter.drawable._structSize)

    ##################################################################
    ###################### File writing section ######################
    ##################################################################

    Exporter.file = open(options['filePath'], "wb")

    magic = np.uint(88298322)
    version = np.uint(110)
    Exporter.flags.SetIsRes(1)
    Exporter.flags.SetCompressed(1)
    Exporter.file.write(magic.tobytes())
    Exporter.file.write(version.tobytes())
    Exporter.file.write(Exporter.flags.flag.tobytes())

    uncompressedData = bytes()
    uncompressedData += cpu
    uncompressedData += gpu

    #compressedData = zlib.compress(uncompressedData, -1, zlib.MAX_WBITS)
    compressedData = zlib.compress(uncompressedData, -1)

    Exporter.file.write(compressedData)

    Exporter.file.close()

    cpu = 0
    gpu = 0
    uncompressedData = 0
    compressedData = 0

    return "SUCCESS"
