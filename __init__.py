### testing
#if "bpy" in locals():
    #import importlib

    #if "export_wdr" in locals():
        #importlib.reload(export_wdr)

import time

import bpy
from bpy.utils import register_class, unregister_class
from bpy_extras.io_utils import ExportHelper

from . import export_wdr

bl_info = {
    "name": "LibertyToolBox",
    "author": "GTA community",
    "blender": (2, 93, 0),
    "version": (0, 9),
    "description": "GTA IV WDR Exporter",
    "location": "File > Export",
    "category": "Export"
}

class Export_WDR(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.wdr"
    bl_description = 'Export one visible geometry and visible bones/armature from the active collection to WDR format'
    bl_label = "GTA IV drawable (.wdr)"
    filename_ext = ".wdr"

    filter_glob : bpy.props.StringProperty(
        default = "*.wdr",
        options = {'HIDDEN'}
    )
    
    directory : bpy.props.StringProperty(
        maxlen = 1024,
        default = "",
        subtype = 'FILE_PATH',
        options = {'HIDDEN'}
    )
    
    files : bpy.props.CollectionProperty(
        type = bpy.types.OperatorFileListElement,
        options = {'HIDDEN'}
    )

    filepath : bpy.props.StringProperty(
         name = "File path",
         description = "WDR file path",
         maxlen = 1024,
         default = "",
         options = {'HIDDEN'}
     )
    
    modify_geometry : bpy.props.BoolProperty(
        name = "Modify geometry",
        description = "Changing faces and splitting edges. This may help if the model is not displaying correctly",
        default = False
    )

    def execute(self, context):
        startTime = time.time()

        exportStatus = export_wdr.start_export(
                                {
                                    'filePath' : self.filepath,
                                    'modifyGeometry' : self.modify_geometry,
                                }
                                )
        
        if (exportStatus == "SUCCESS"):
            self.report({"INFO"}, f"Export finished ({time.time() - startTime:.1f} sec)")
        elif (exportStatus == "ERROR_NOTHING"):
            self.report({"INFO"}, f"Nothing to export!")
        elif (exportStatus == "ERROR_CODE_1"):
            self.report({"INFO"}, f"Export error! [1]")
        elif (exportStatus == "ERROR_CODE_2"):
            self.report({"INFO"}, f"Export error! [2]")
                
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def export_wdr_link(self, context):
    self.layout.operator(Export_WDR.bl_idname, text="GTA IV drawable (.wdr)")


class DrawableMaterial(bpy.types.Panel):
    bl_idname      = "MATERIAL_PT_DrawableMaterial"
    bl_label       = "LibertyToolBox"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "material"

    def draw_diffuse(self, context):
        drawable = context.material.libertytool_drawable
        box = self.layout.box()
        box.label(text="Diffuse")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")

    def draw_bump(self, context):
        drawable = context.material.libertytool_drawable
        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")
        box.prop(drawable, "bumpiness")

    def draw_bump_reflect(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "bumpiness")

        box = self.layout.box()
        box.label(text="Reflective")
        box.prop(drawable, "embed_environment_texture")
        if (not drawable.embed_environment_texture):
            box.prop(drawable, "environment_texture_name")
        box.prop(drawable, "reflective_power")

    def draw_specular(self, context):
        drawable = context.material.libertytool_drawable
        box = self.layout.box()
        box.label(text="Specular")
        box.prop(drawable, "embed_specular_texture")
        if (not drawable.embed_specular_texture):
            box.prop(drawable, "specular_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")
        box.prop(drawable, "spec_map_int_mask")

    def draw_specular_const(self, context):
        drawable = context.material.libertytool_drawable
        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")

    def draw_bump_spec(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "bumpiness")
        
        box = self.layout.box()
        box.label(text="Specular")
        box.prop(drawable, "embed_specular_texture")
        if (not drawable.embed_specular_texture):
            box.prop(drawable, "specular_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")
        box.prop(drawable, "spec_map_int_mask")

    def draw_reflect(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="Reflective")
        box.prop(drawable, "embed_environment_texture")
        if (not drawable.embed_environment_texture):
            box.prop(drawable, "environment_texture_name")
        box.prop(drawable, "reflective_power")

    def draw_glass_default(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")

        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "bumpiness")

        box = self.layout.box()
        box.label(text="Reflective")
        box.prop(drawable, "embed_environment_texture")
        if (not drawable.embed_environment_texture):
            box.prop(drawable, "environment_texture_name")
        box.prop(drawable, "reflective_power")

    def draw_glass(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")

    def draw_emissive(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="Emissive")
        box.prop(drawable, "z_shift")
        box.prop(drawable, "emissive_multiplier")

    def draw_parallax(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "parallax_scale_bias")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")

        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "bumpiness")

    def draw_parallax_spec(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "parallax_scale_bias")

        box = self.layout.box()
        box.label(text="Specular")
        box.prop(drawable, "embed_specular_texture")
        if (not drawable.embed_specular_texture):
            box.prop(drawable, "specular_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")
        box.prop(drawable, "spec_map_int_mask")

        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "bumpiness")

    def draw_decal_glue(self, context):
        drawable = context.material.libertytool_drawable
        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")

    def draw_decal_dirt(self, context):
        drawable = context.material.libertytool_drawable
        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "dirt_decal_mask")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")

    def draw_ped(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="Specular")
        box.prop(drawable, "embed_specular_texture")
        if (not drawable.embed_specular_texture):
            box.prop(drawable, "specular_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")
        box.prop(drawable, "spec_map_int_mask")

        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "bumpiness")

    def draw_ped_reflect(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="Specular")
        box.prop(drawable, "embed_specular_texture")
        if (not drawable.embed_specular_texture):
            box.prop(drawable, "specular_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")
        box.prop(drawable, "spec_map_int_mask")

        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "bumpiness")

        box = self.layout.box()
        box.label(text="Reflective")
        box.prop(drawable, "embed_environment_texture")
        if (not drawable.embed_environment_texture):
            box.prop(drawable, "environment_texture_name")
        box.prop(drawable, "reflective_power")
    
    def draw_ped_skin(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "sub_color")

        box = self.layout.box()
        box.label(text="Specular")
        box.prop(drawable, "embed_specular_texture")
        if (not drawable.embed_specular_texture):
            box.prop(drawable, "specular_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")
        box.prop(drawable, "spec_map_int_mask")

        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "bumpiness")

    def draw_hair_sorted_alpha_expensive(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "order_number")

        box = self.layout.box()
        box.label(text="Diffuse")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")

        box = self.layout.box()
        box.label(text="Specular")
        box.prop(drawable, "embed_specular_texture")
        if (not drawable.embed_specular_texture):
            box.prop(drawable, "specular_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")
        box.prop(drawable, "spec_map_int_mask")

        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "bumpiness")

    def draw_wire(self, context):
        drawable = context.material.libertytool_drawable
        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "fade_thickness")

    def draw_diffuse_instance(self, context):
        drawable = context.material.libertytool_drawable
        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "world_instance_matrix")
        box.prop(drawable, "world_instance_inverse_transpose")

    def draw_radar(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")

        box = self.layout.box()
        box.label(text="Normal/Bump")
        box.prop(drawable, "embed_bump_texture")
        if (not drawable.embed_bump_texture):
            box.prop(drawable, "bump_texture_name")
        box.prop(drawable, "bumpiness")
    
    def draw_rmptfx_mesh(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")

    def draw_null(self, context):
        drawable = context.material.libertytool_drawable

        box = self.layout.box()
        box.label(text="General")
        box.prop(drawable, "embed_diffuse_texture")
        if (not drawable.embed_diffuse_texture):
            box.prop(drawable, "diffuse_texture_name")
        box.prop(drawable, "specular_factor")
        box.prop(drawable, "specular_color_factor")

    def draw(self, context):
        if not context.material or not context.material.libertytool_drawable:
            return

        drawable = context.material.libertytool_drawable

        shaders_box = self.layout.box()
        shaders_box.prop(drawable, "shader_category")

        if (drawable.shader_category =="general"):
            shaders_box.prop(drawable, "shaders_general")
            if (drawable.shaders_general == "gta_default.sps" or drawable.shaders_general == "gta_alpha.sps" or
                drawable.shaders_general == "gta_decal.sps" or drawable.shaders_general == "gta_cutout.sps" or
                drawable.shaders_general == "gta_cutout_fence.sps" or drawable.shaders_general == "gta_decal_amb_only.sps"):
                self.draw_diffuse(context)
            elif (drawable.shaders_general == "gta_alpha.sps"):
                self.draw_diffuse(context)
            elif (drawable.shaders_general == "gta_decal_glue.sps"):
                self.draw_decal_glue(context)
            elif (drawable.shaders_general == "gta_decal_dirt.sps"):
                self.draw_decal_dirt(context)
            elif (drawable.shaders_general == "gta_normal.sps" or drawable.shaders_general == "gta_normal_alpha.sps" or
                  drawable.shaders_general == "gta_normal_cutout.sps" or drawable.shaders_general == "gta_decal_normal_only.sps" or
                  drawable.shaders_general == "gta_normal_decal.sps"):
                self.draw_diffuse(context)
                self.draw_bump(context)
            elif (drawable.shaders_general == "gta_spec.sps" or drawable.shaders_general == "gta_spec_alpha.sps" or
                  drawable.shaders_general == "gta_spec_decal.sps"):
                self.draw_diffuse(context)
                self.draw_specular(context)
            elif (drawable.shaders_general == "gta_spec_const.sps"):
                self.draw_specular_const(context)
            elif (drawable.shaders_general == "gta_spec_reflect.sps" or drawable.shaders_general == "gta_spec_reflect_alpha.sps" or
                  drawable.shaders_general == "gta_spec_reflect_decal.sps"):
                self.draw_diffuse(context)
                self.draw_specular(context)
                self.draw_reflect(context)
            elif (drawable.shaders_general == "gta_normal_spec.sps" or drawable.shaders_general == "gta_normal_spec_alpha.sps" or
                  drawable.shaders_general == "gta_normal_spec_decal.sps"):
                self.draw_diffuse(context)
                self.draw_bump_spec(context)
            elif (drawable.shaders_general == "gta_normal_spec_reflect.sps" or drawable.shaders_general == "gta_normal_spec_reflect_alpha.sps" or
                  drawable.shaders_general == "gta_normal_spec_cubemap_reflect.sps" or drawable.shaders_general == "gta_normal_spec_reflect_decal.sps"):
                self.draw_diffuse(context)
                self.draw_bump_spec(context)
                self.draw_reflect(context)
            elif (drawable.shaders_general == "gta_normal_spec_reflect_emissive.sps" or drawable.shaders_general == "gta_normal_spec_reflect_emissive_alpha.sps" or
                  drawable.shaders_general == "gta_normal_spec_reflect_emissivenight.sps" or drawable.shaders_general == "gta_normal_spec_reflect_emissivenight_alpha.sps"):
                self.draw_diffuse(context)
                self.draw_bump_spec(context)
                self.draw_reflect(context)
                self.draw_emissive(context)
            elif (drawable.shaders_general == "gta_normal_reflect.sps" or drawable.shaders_general == "gta_normal_reflect_alpha.sps" or
                  drawable.shaders_general == "gta_normal_reflect_decal.sps" or drawable.shaders_general == "gta_normal_cubemap_reflect.sps"):
                self.draw_diffuse(context)
                self.draw_bump_reflect(context)
            elif (drawable.shaders_general == "gta_reflect.sps" or drawable.shaders_general == "gta_reflect_alpha.sps" or
                  drawable.shaders_general == "gta_reflect_decal.sps"):
                self.draw_diffuse(context)
                self.draw_reflect(context)
            elif (drawable.shaders_general == "gta_cubemap_reflect.sps"):
                self.draw_diffuse(context)
                self.draw_reflect(context)
            elif (drawable.shaders_general == "gta_glass.sps"):
                self.draw_glass_default(context)
            elif (drawable.shaders_general == "gta_glass_spec.sps"):
                self.draw_diffuse(context)
                self.draw_specular(context)
            elif (drawable.shaders_general == "gta_glass_normal_spec_reflect.sps"):
                self.draw_diffuse(context)
                self.draw_bump_spec(context)
                self.draw_reflect(context)
            elif (drawable.shaders_general == "gta_glass_reflect.sps"):
                self.draw_glass(context)
                self.draw_reflect(context)
            elif (drawable.shaders_general == "gta_glass_emissive.sps" or drawable.shaders_general == "gta_glass_emissive_alpha.sps" or
                  drawable.shaders_general == "gta_glass_emissivenight.sps" or drawable.shaders_general == "gta_glass_emissivenight_alpha.sps"):
                self.draw_glass_default(context)
                self.draw_emissive(context)
            elif (drawable.shaders_general == "gta_emissive.sps" or drawable.shaders_general == "gta_emissive_alpha.sps" or
                  drawable.shaders_general == "gta_emissivestrong.sps" or drawable.shaders_general == "gta_emissivestrong_alpha.sps" or
                  drawable.shaders_general == "gta_emissivenight.sps" or drawable.shaders_general == "gta_emissivenight_alpha.sps"):
                self.draw_diffuse(context)
                self.draw_emissive(context)
            elif (drawable.shaders_general == "gta_parallax.sps" or drawable.shaders_general == "gta_parallax_steep.sps"):
                self.draw_parallax(context)
            elif (drawable.shaders_general == "gta_parallax_specmap.sps"):
                self.draw_parallax_spec(context)
        elif (drawable.shader_category =="ped"):
            shaders_box.prop(drawable, "shaders_ped")
            if (drawable.shaders_ped == "gta_ped.sps"):
                self.draw_diffuse(context)
                self.draw_ped(context)
            elif (drawable.shaders_ped == "gta_ped_reflect.sps"):
                self.draw_diffuse(context)
                self.draw_ped_reflect(context)
            elif (drawable.shaders_ped == "gta_ped_skin.sps" or drawable.shaders_ped == "gta_ped_skin_blendshape.sps"):
                self.draw_ped_skin(context)
            elif (drawable.shaders_ped == "gta_hair_sorted_alpha.sps"):
                self.draw_diffuse(context)
                self.draw_bump_spec(context)
            elif (drawable.shaders_ped == "gta_hair_sorted_alpha_expensive.sps"):
                self.draw_hair_sorted_alpha_expensive(context)
        elif (drawable.shader_category =="vehicle"):
            shaders_box.prop(drawable, "shaders_vehicle")
            #TODO
        elif (drawable.shader_category =="other"):
            shaders_box.prop(drawable, "shaders_other")
            if (drawable.shaders_other == "gta_mirror.sps"):
                self.draw_diffuse(context)
                self.draw_reflect(context)
            elif (drawable.shaders_other == "gta_trees.sps"):
                self.draw_diffuse(context)
            elif (drawable.shaders_other == "gta_wire.sps"):
                self.draw_wire(context)
            elif (drawable.shaders_other == "gta_diffuse_instance.sps"):
                self.draw_diffuse_instance(context)
            elif (drawable.shaders_other == "gta_radar.sps"):
                self.draw_radar(context)
            elif (drawable.shaders_other == "gta_rmptfx_mesh.sps"):
                self.draw_rmptfx_mesh(context)
            elif (drawable.shaders_other == "null.sps"):
                self.draw_null(context)
            #TODO
        elif (drawable.shader_category == "custom"):
            shaders_box.prop(drawable, "shaders_custom")
            if (drawable.shaders_custom == "gta_custom.sps"):
                pass

shader_category_items = (
    ("general", "General", "General shaders"),
    ("ped", "Ped", "Ped shaders"),
    ("vehicle", "Vehicle [PREVIEW]", "Vehicle shaders"), #TEMP
    ("other", "Other", "Other shaders"),
    #("custom", "Custom", "Custom shaders"),
)

shader_general_items = (
    ("gta_default.sps", "Default", "gta_default"),
    ("gta_alpha.sps", "Alpha", "gta_alpha"),
    ("gta_decal.sps", "Decal", "gta_decal"),
    ("gta_decal_glue.sps", "Decal glue", "gta_decal_glue"),
    ("gta_decal_dirt.sps", "Decal dirt", "gta_decal_dirt"),
    ("gta_decal_amb_only.sps", "Decal, Amb", "gta_decal_amb_only"),
    ("gta_decal_normal_only.sps", "Decal, Normal", "gta_decal_normal_only"),
    ("gta_cutout.sps", "Cutout", "gta_cutout"),
    ("gta_cutout_fence.sps", "Cutout fence", "gta_cutout_fence"),
    ("gta_normal.sps", "Normal", "gta_normal"),
    ("gta_normal_alpha.sps", "Normal, Alpha", "gta_normal_alpha"),
    ("gta_normal_cutout.sps", "Normal, Cutout", "gta_normal_cutout"),
    ("gta_normal_spec.sps", "Normal, Specular", "gta_normal_spec"),
    ("gta_normal_spec_alpha.sps", "Normal, Specular, Alpha", "gta_normal_spec_alpha"),
    ("gta_normal_spec_reflect.sps", "Normal, Specular, Reflect", "gta_normal_spec_reflect"),
    ("gta_normal_spec_reflect_alpha.sps", "Normal, Specular, Reflect, Alpha", "gta_normal_spec_reflect_alpha"),
    ("gta_normal_spec_reflect_emissive.sps", "Normal, Specular, Reflect, Emissive", "gta_normal_spec_reflect_emissive"),
    ("gta_normal_spec_reflect_emissive_alpha.sps", "Normal, Specular, Reflect, Emissive, Alpha", "gta_normal_spec_reflect_emissive_alpha"),
    ("gta_normal_spec_reflect_emissivenight.sps", "Normal, Specular, Reflect, Emissive night", "gta_normal_spec_reflect_emissivenight"),
    ("gta_normal_spec_reflect_emissivenight_alpha.sps", "Normal, Specular, Reflect, Emissive night, Alpha", "gta_normal_spec_reflect_emissivenight_alpha"),
    ("gta_normal_spec_cubemap_reflect.sps", "Normal, Specular, Cubemap, Reflect", "gta_normal_spec_cubemap_reflect"),
    ("gta_normal_reflect.sps", "Normal, Reflect", "gta_normal_reflect"),
    ("gta_normal_reflect_alpha.sps", "Normal, Reflect, Alpha", "gta_normal_reflect_alpha"),
    ("gta_normal_reflect_decal.sps", "Normal, Reflect, Decal", "gta_normal_reflect_decal"),
    ("gta_normal_cubemap_reflect.sps", "Normal, Cubemap, Reflect", "gta_normal_cubemap_reflect"),
    ("gta_normal_decal.sps", "Normal, Decal", "gta_normal_decal"),
    ("gta_normal_spec_decal.sps", "Normal, Specular, Decal", "gta_normal_spec_decal"),
    ("gta_normal_spec_reflect_decal.sps", "Normal, Specular, Reflect, Decal", "gta_normal_spec_reflect_decal"),
    ("gta_spec.sps", "Specular", "gta_spec"),
    ("gta_spec_alpha.sps", "Specular, Alpha", "gta_spec_alpha"),
    ("gta_spec_const.sps", "Specular const", "gta_spec_const"),
    ("gta_spec_decal.sps", "Specular, Decal", "gta_spec_decal"),
    ("gta_spec_reflect.sps", "Specular, Reflect", "gta_spec_reflect"),
    ("gta_spec_reflect_alpha.sps", "Specular, Reflect, Alpha", "gta_spec_reflect_alpha"),
    ("gta_spec_reflect_decal.sps", "Specular, Reflect, Decal", "gta_spec_reflect_decal"),
    ("gta_reflect.sps", "Reflect", "gta_reflect"),
    ("gta_reflect_alpha.sps", "Reflect, Alpha", "gta_reflect_alpha"),
    ("gta_reflect_decal.sps", "Reflect, Decal", "gta_reflect_decal"),
    ("gta_cubemap_reflect.sps", "Cubemap, Reflect", "gta_cubemap_reflect"),
    ("gta_glass.sps", "Glass", "gta_glass"),
    ("gta_glass_spec.sps", "Glass, Specular", "gta_glass_spec"),
    ("gta_glass_normal_spec_reflect.sps", "Glass, Normal, Specular", "gta_glass_normal_spec_reflect"),
    ("gta_glass_reflect.sps", "Glass, Reflect", "gta_glass_reflect"),
    ("gta_glass_emissive.sps", "Glass, Emissive", "gta_glass_emissive"),
    ("gta_glass_emissive_alpha.sps", "Glass, Emissive, Alpha", "gta_glass_emissive_alpha"),
    ("gta_glass_emissivenight.sps", "Glass, Emissive night", "gta_glass_emissivenight"),
    ("gta_glass_emissivenight_alpha.sps", "Glass, Emissive night, Alpha", "gta_glass_emissivenight_alpha"),
    ("gta_emissive.sps", "Emissive", "gta_emissive"),
    ("gta_emissive_alpha.sps", "Emissive, Alpha", "gta_emissive_alpha"),
    ("gta_emissivestrong.sps", "Emissive strong", "gta_emissivestrong"),
    ("gta_emissivestrong_alpha.sps", "Emissive strong, Alpha", "gta_emissivestrong_alpha"),
    ("gta_emissivenight.sps", "Emissive night", "gta_emissivenight"),
    ("gta_emissivenight_alpha.sps", "Emissive night, Alpha", "gta_emissivenight_alpha"),
    ("gta_parallax.sps", "Parallax", "gta_parallax"),
    ("gta_parallax_specmap.sps", "Parallax, Specular", "gta_parallax_specmap"),
    ("gta_parallax_steep.sps", "Parallax steep", "gta_parallax_steep"),
)

shader_ped_items = (
    ("gta_ped.sps", "Ped", "gta_ped"),
    ("gta_ped_reflect.sps", "Ped reflect", "gta_ped_reflect"),
    ("gta_ped_skin.sps", "Ped skin", "gta_ped_skin"),
    ("gta_ped_skin_blendshape.sps", "Ped skin blendshape", "gta_ped_skin_blendshape"),
    ("gta_hair_sorted_alpha.sps", "Hair sorted alpha", "gta_hair_sorted_alpha"),
    ("gta_hair_sorted_alpha_expensive.sps", "Hair sorted alpha expensive", "gta_hair_sorted_alpha_expensive"),
)

shader_vehicle_items = (
    ("gta_vehicle_badges.sps", "Badges", "gta_vehicle_badges"),
    ("gta_vehicle_chrome.sps", "Chrome", "gta_vehicle_chrome"),
    ("gta_vehicle_generic.sps", "Generic", "gta_vehicle_generic"),
    ("gta_vehicle_interior.sps", "Interior", "gta_vehicle_interior"),
    ("gta_vehicle_interior2.sps", "Interior 2", "gta_vehicle_interior2"),
    ("gta_vehicle_lightsemissive.sps", "Lights emissive", "gta_vehicle_lightsemissive"),
    ("gta_vehicle_mesh.sps", "Mesh", "gta_vehicle_mesh"),
    ("gta_vehicle_paint1.sps", "Paint 1", "gta_vehicle_paint1"),
    ("gta_vehicle_paint2.sps", "Paint 2", "gta_vehicle_paint2"),
    ("gta_vehicle_paint3.sps", "Paint 3", "gta_vehicle_paint3"),
    ("gta_vehicle_rims1.sps", "Rims 1", "gta_vehicle_rims1"),
    ("gta_vehicle_rims2.sps", "Rims 2", "gta_vehicle_rims2"),
    ("gta_vehicle_rubber.sps", "Rubber", "gta_vehicle_rubber"),
    ("gta_vehicle_shuts.sps", "Shuts", "gta_vehicle_shuts"),
    ("gta_vehicle_tire.sps", "Tire", "gta_vehicle_tire"),
    ("gta_vehicle_vehglass.sps", "Glass", "gta_vehicle_vehglass"),
)

shader_other_items = (
    ("gta_mirror.sps", "Mirror", "gta_mirror"),
    ("gta_trees.sps", "Trees", "gta_trees"),
    ("gta_wire.sps", "Wire", "gta_wire"),
    ("gta_diffuse_instance.sps", "Diffuse instance", "gta_diffuse_instance"),
    ("gta_radar.sps", "Radar", "gta_radar"),
    ("gta_rmptfx_mesh.sps", "RMPTFX mesh", "gta_rmptfx_mesh"),
    ("null.sps", "Null", "null"),
    #("gta_terrain_va_2lyr.sps", "terrain_va_2lyr", "gta_terrain_va_2lyr"),
    #("gta_terrain_va_3lyr.sps", "terrain_va_3lyr", "gta_terrain_va_3lyr"),
    #("gta_terrain_va_4lyr.sps", "terrain_va_4lyr", "gta_terrain_va_4lyr"),
)

shader_custom_items = (
    ("gta_custom.sps", "Custom", "gta_custom"),
)

class DrawableMaterialProperties(bpy.types.PropertyGroup):
    shader_category : bpy.props.EnumProperty(items=shader_category_items, default="general", name="Category")

    # Shader list
    shaders_general : bpy.props.EnumProperty(items=shader_general_items, default="gta_default.sps", name="Shader")
    shaders_ped : bpy.props.EnumProperty(items=shader_ped_items, default="gta_ped.sps", name="Shader")
    shaders_vehicle : bpy.props.EnumProperty(items=shader_vehicle_items, default="gta_vehicle_badges.sps", name="Shader")
    shaders_other : bpy.props.EnumProperty(items=shader_other_items, default="gta_mirror.sps", name="Shader")
    shaders_custom : bpy.props.EnumProperty(items=shader_custom_items, default="gta_custom.sps", name="Shader")

    # Embed texture
    embed_diffuse_texture : bpy.props.BoolProperty(name="Embed texture", default=False, description="Embed diffuse DDS texture in exported file (Principled BSDF > Base Color)")
    embed_specular_texture : bpy.props.BoolProperty(name="Embed texture", default=False, description="Embed specular DDS texture in exported file (Principled BSDF > Specular > Tint)")
    embed_bump_texture : bpy.props.BoolProperty(name="Embed texture", default=False, description="Embed bump DDS texture in exported file (Principled BSDF > Normal)")
    embed_environment_texture : bpy.props.BoolProperty(name="Embed texture", default=False, description="Embed environment DDS texture in exported file (Principled BSDF > Sheen > Tint)")

    # Diffuse
    diffuse_texture_name : bpy.props.StringProperty(name="Texture", description="Diffuse texture name. If the field is empty, the texture name will be used from Principled BSDF > Base Color")

    # Specular
    specular_texture_name : bpy.props.StringProperty(name="Texture", description="Specular texture name. If the field is empty, the texture name will be used from Principled BSDF > Specular > Tint")
    specular_factor : bpy.props.FloatProperty(name="Specular factor", min=0.001, max=200.0)
    specular_color_factor : bpy.props.FloatProperty(name="Specular color factor", min=0.001, max=2.0)
    spec_map_int_mask : bpy.props.FloatVectorProperty(name="Specular mask", subtype='COLOR', size=3, default=[1.0, 0.0, 0.0], min=0.0, max=1.0)
    
    # Normal/Bump
    bump_texture_name : bpy.props.StringProperty(name="Texture", description="Bump texture name. If the field is empty, the texture name will be used from Principled BSDF > Normal")
    bumpiness : bpy.props.FloatProperty(name="Bumpiness", min=0.001, max=2.0)

    # Reflect
    environment_texture_name : bpy.props.StringProperty(name="Texture", description="Environment texture name. If the field is empty, the texture name will be used from Principled BSDF > Sheen > Tint")
    reflective_power : bpy.props.FloatProperty(name="Reflective power", min=0.001, max=2.0)

    # Emissive
    z_shift : bpy.props.FloatProperty(name="Z-shift", min=0.001, max=2.0)
    emissive_multiplier : bpy.props.FloatProperty(name="Emissive multiplier", min=0.001, max=200.0)

    # Parallax
    parallax_scale_bias : bpy.props.FloatProperty(name="Parallax scale bias", min=0.001, max=2.0)

    # Decal
    dirt_decal_mask : bpy.props.FloatVectorProperty(name="Dirt decal mask", subtype='COLOR', size=4, default=[0.0, 0.0, 0.0, 0.0], min=0.0, max=1.0)

    # Ped skin
    sub_color : bpy.props.FloatVectorProperty(name="Sub color", subtype='COLOR', size=4, default=[0.2, 0.0825, 0.025, 1.0], min=0.0, max=1.0)

    # Ped hair
    order_number : bpy.props.IntProperty(name="Order number", default=1, min=1, max=5, description="The order of the hair layers. The order starts with the lowest hair layer")

    # Diffuse instance
    world_instance_matrix : bpy.props.FloatVectorProperty(name="World instance matrix", subtype='TRANSLATION', size=4, default=[0.0, 0.0, 0.0, 0.0], min=-2.0, max=2.0)
    world_instance_inverse_transpose : bpy.props.FloatVectorProperty(name="World instance inverse transpose", subtype='TRANSLATION', size=4, default=[0.0, 0.0, 0.0, 0.0], min=-2.0, max=2.0)

    # Wire
    fade_thickness : bpy.props.FloatProperty(name="Fade thickness", min=0.001, max=2.0)

    def register():
        bpy.types.Material.libertytool_drawable = bpy.props.PointerProperty(type=DrawableMaterialProperties)


class SkelData(bpy.types.Panel):
    bl_idname      = "OBJECT_PT_SkelData"
    bl_label       = "LibertyToolBox - Bone"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "object"

    def draw(self, context):
        if not context.object or not context.object.libertytool_bone:
            return

        bone = context.object.libertytool_bone

        if context.object.type != 'EMPTY':
            return

        layout = self.layout
        box = layout.box()
        box.label(text="General")
        box.prop(bone, "id")
        box.prop(bone, "index")
        box.prop(bone, "mirror")

        layout = self.layout
        box = layout.box()
        box.label(text="Flags")
        box.prop(bone, "flag_invisible")
        box.prop(bone, "flag_lock_translation_x")
        box.prop(bone, "flag_lock_translation_y")
        box.prop(bone, "flag_lock_translation_z")
        box.prop(bone, "flag_limit_translation_x")
        box.prop(bone, "flag_limit_translation_y")
        box.prop(bone, "flag_limit_translation_z")
        box.prop(bone, "flag_lock_rotation_x")
        box.prop(bone, "flag_lock_rotation_y")
        box.prop(bone, "flag_lock_rotation_z")
        box.prop(bone, "flag_lock_rotation_xyz")
        box.prop(bone, "flag_limit_rotation_x")
        box.prop(bone, "flag_limit_rotation_y")
        box.prop(bone, "flag_limit_rotation_z")
        box.prop(bone, "flag_lock_scale_x")
        box.prop(bone, "flag_lock_scale_y")
        box.prop(bone, "flag_lock_scale_z")
        box.prop(bone, "flag_limit_scale_x")
        box.prop(bone, "flag_limit_scale_y")
        box.prop(bone, "flag_limit_scale_z")

class SkelDataProperties(bpy.types.PropertyGroup):
    id : bpy.props.IntProperty(default=-1, name="ID", description="Identificator. If the value is -1, an identifier based on location in the hierarchy will be used")
    index : bpy.props.IntProperty(default=-1, name="Index")
    mirror : bpy.props.IntProperty(default=-1, name="Mirror")

    flag_invisible : bpy.props.BoolProperty(name="Invisible", default=True)
    flag_lock_rotation_xyz : bpy.props.BoolProperty(name="Lock XYZ rotation")
    flag_lock_rotation_x : bpy.props.BoolProperty(name="Lock X rotation")
    flag_lock_rotation_y : bpy.props.BoolProperty(name="Lock Y rotation")
    flag_lock_rotation_z : bpy.props.BoolProperty(name="Lock Z rotation")
    flag_limit_rotation_x : bpy.props.BoolProperty(name="Limit X rotation")
    flag_limit_rotation_y : bpy.props.BoolProperty(name="Limit Y rotation")
    flag_limit_rotation_z : bpy.props.BoolProperty(name="Limit Z rotation")
    flag_lock_translation_x : bpy.props.BoolProperty(name="Lock X location", description="Lock X translation")
    flag_lock_translation_y : bpy.props.BoolProperty(name="Lock Y location", description="Lock Y translation")
    flag_lock_translation_z : bpy.props.BoolProperty(name="Lock Z location", description="Lock Z translation")
    flag_limit_translation_x : bpy.props.BoolProperty(name="Limit X location", description="Limit X translation")
    flag_limit_translation_y : bpy.props.BoolProperty(name="Limit Y location", description="Limit Y translation")
    flag_limit_translation_z : bpy.props.BoolProperty(name="Limit Z location", description="Limit Z translation")
    flag_lock_scale_x : bpy.props.BoolProperty(name="Lock X scale")
    flag_lock_scale_y : bpy.props.BoolProperty(name="Lock Y scale")
    flag_lock_scale_z : bpy.props.BoolProperty(name="Lock Z scale")
    flag_limit_scale_x : bpy.props.BoolProperty(name="Limit X scale")
    flag_limit_scale_y : bpy.props.BoolProperty(name="Limit Y scale")
    flag_limit_scale_z : bpy.props.BoolProperty(name="Limit Z scale")
    
    def register():
        bpy.types.Object.libertytool_bone = bpy.props.PointerProperty(type=SkelDataProperties)


rotation_mode_items = (
    ("dont_override", "Don't override", "Don't override rotation order"),
    ("XYZ", "XYZ Euler", "XYZ rotation order"),
    ("XZY", "XZY Euler", "XZY rotation order"),
    ("YXZ", "YXZ Euler", "YXZ rotation order"),
    ("YZX", "YZX Euler", "YZX rotation order"),
    ("ZXY", "ZXY Euler", "ZXY rotation order"),
    ("ZYX", "ZYX Euler", "ZYX rotation order"),
)

class SkelCollection(bpy.types.Panel):
    bl_idname      = "COLLECTION_PT_SkelData"
    bl_label       = "LibertyToolBox - Skeleton"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "collection"

    def draw(self, context):
        if not context.collection or not context.collection.libertytool_skel:
            return

        skel = context.collection.libertytool_skel

        layout = self.layout
        box = layout.box()
        box.prop(skel, "override_rotation_mode")
        box.separator()
        box.prop(skel, "flag_have_bone_world_orientation")
        box.prop(skel, "flag_have_bone_mappings")
        box.prop(skel, "flag_authored_orientation")
        box.prop(skel, "flag_unk0")
        box.separator()
        box.prop(skel, "force_lock_location_armature")

class SkelCollectionProperties(bpy.types.PropertyGroup):
    override_rotation_mode : bpy.props.EnumProperty(items=rotation_mode_items, default="dont_override", name="Rotation")

    force_lock_location_armature : bpy.props.BoolProperty(name="Force lock location at first armature bone", default=True, description="Force the Lock Location X, Y, Z flags to true at the first armature bone")
    
    flag_have_bone_world_orientation : bpy.props.BoolProperty(name="Have bone world orientation", default=True)
    flag_have_bone_mappings : bpy.props.BoolProperty(name="Have bone mappings", default=True)
    flag_authored_orientation : bpy.props.BoolProperty(name="Authored orientation", default=True)
    flag_unk0 : bpy.props.BoolProperty(name="Unknown flag", default=False)
    
    def register():
        bpy.types.Collection.libertytool_skel = bpy.props.PointerProperty(type=SkelCollectionProperties)


class SkelArmatureBoneData(bpy.types.Panel):
    bl_idname      = "OBJECT_PT_SkelArmatureBoneData"
    bl_label       = "LibertyToolBox - Bone"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "bone"

    def draw(self, context):
        if not context.bone or not context.bone.libertytool_bone:
            return

        bone = context.bone.libertytool_bone

        layout = self.layout
        box = layout.box()
        box.label(text="General")
        box.prop(bone, "id")
        box.prop(bone, "index")
        box.prop(bone, "mirror")

        layout = self.layout
        box = layout.box()
        box.label(text="Flags")
        box.prop(bone, "flag_invisible")
        box.prop(bone, "flag_lock_translation_x")
        box.prop(bone, "flag_lock_translation_y")
        box.prop(bone, "flag_lock_translation_z")
        box.prop(bone, "flag_limit_translation_x")
        box.prop(bone, "flag_limit_translation_y")
        box.prop(bone, "flag_limit_translation_z")
        box.prop(bone, "flag_lock_rotation_x")
        box.prop(bone, "flag_lock_rotation_y")
        box.prop(bone, "flag_lock_rotation_z")
        box.prop(bone, "flag_lock_rotation_xyz")
        box.prop(bone, "flag_limit_rotation_x")
        box.prop(bone, "flag_limit_rotation_y")
        box.prop(bone, "flag_limit_rotation_z")
        box.prop(bone, "flag_lock_scale_x")
        box.prop(bone, "flag_lock_scale_y")
        box.prop(bone, "flag_lock_scale_z")
        box.prop(bone, "flag_limit_scale_x")
        box.prop(bone, "flag_limit_scale_y")
        box.prop(bone, "flag_limit_scale_z")

class SkelArmatureBoneDataProperties(bpy.types.PropertyGroup):
    id : bpy.props.IntProperty(default=-1, name="ID", description="Identificator. If the value is -1, an identifier based on location in the hierarchy will be used")
    index : bpy.props.IntProperty(default=-1, name="Index")
    mirror : bpy.props.IntProperty(default=-1, name="Mirror")

    flag_invisible : bpy.props.BoolProperty(name="Invisible", default=True)
    flag_lock_rotation_xyz : bpy.props.BoolProperty(name="Lock XYZ rotation", default=True)
    flag_lock_rotation_x : bpy.props.BoolProperty(name="Lock X rotation", default=True)
    flag_lock_rotation_y : bpy.props.BoolProperty(name="Lock Y rotation", default=True)
    flag_lock_rotation_z : bpy.props.BoolProperty(name="Lock Z rotation", default=True)
    flag_limit_rotation_x : bpy.props.BoolProperty(name="Limit X rotation")
    flag_limit_rotation_y : bpy.props.BoolProperty(name="Limit Y rotation")
    flag_limit_rotation_z : bpy.props.BoolProperty(name="Limit Z rotation")
    flag_lock_translation_x : bpy.props.BoolProperty(name="Lock X location", description="Lock X translation")
    flag_lock_translation_y : bpy.props.BoolProperty(name="Lock Y location", description="Lock Y translation")
    flag_lock_translation_z : bpy.props.BoolProperty(name="Lock Z location", description="Lock Z translation")
    flag_limit_translation_x : bpy.props.BoolProperty(name="Limit X location", description="Limit X translation")
    flag_limit_translation_y : bpy.props.BoolProperty(name="Limit Y location", description="Limit Y translation")
    flag_limit_translation_z : bpy.props.BoolProperty(name="Limit Z location", description="Limit Z translation")
    flag_lock_scale_x : bpy.props.BoolProperty(name="Lock X scale")
    flag_lock_scale_y : bpy.props.BoolProperty(name="Lock Y scale")
    flag_lock_scale_z : bpy.props.BoolProperty(name="Lock Z scale")
    flag_limit_scale_x : bpy.props.BoolProperty(name="Limit X scale")
    flag_limit_scale_y : bpy.props.BoolProperty(name="Limit Y scale")
    flag_limit_scale_z : bpy.props.BoolProperty(name="Limit Z scale")
    
    def register():
        bpy.types.Bone.libertytool_bone = bpy.props.PointerProperty(type=SkelArmatureBoneDataProperties)


def register():
    register_class(Export_WDR)

    register_class(DrawableMaterial)
    register_class(DrawableMaterialProperties)
    register_class(SkelData)
    register_class(SkelDataProperties)
    register_class(SkelCollection)
    register_class(SkelCollectionProperties)
    register_class(SkelArmatureBoneData)
    register_class(SkelArmatureBoneDataProperties)

    bpy.types.TOPBAR_MT_file_export.append(export_wdr_link)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(export_wdr_link)

    unregister_class(Export_WDR)

    unregister_class(DrawableMaterial)
    unregister_class(DrawableMaterialProperties)
    unregister_class(SkelData)
    unregister_class(SkelDataProperties)
    unregister_class(SkelCollection)
    unregister_class(SkelCollectionProperties)
    unregister_class(SkelArmatureBoneData)
    unregister_class(SkelArmatureBoneDataProperties)
