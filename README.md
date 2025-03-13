# LibertyToolbox

LibertyToolBox is a Blender add-on for exporting Blender scenes to the WDR file used in GTA IV.

Based on [Liberty Four](https://gtaforums.com/topic/990530-relsrc-liberty-four) and [LibertyFourXYZ](https://github.com/d3g0n-byte/LibertyFourXYZ) by Shvab.

## Installation:
Open Blender, go to Edit -> Preferences -> Add-ons and click 'Install...'. Select LibertyToolbox archive. Find it in the list of add-ons and activate it.

Recommended minimum version of Blender: 2.93.

## Usage:
Go to File -> Export -> GTA IV drawable (.wdr). Active collection will be exported.

Bones and materials are customized in the properties:
- Collection: LibertyToolBox - Skeleton
- Object: LibertyToolBox - Bone
- Bone: LibertyToolBox - Bone
- Material: LibertyToolBox

## Known issues:
- Meshes that were not made in GTA IV may not have textures displayed correctly due to the fact that Blender stores UV information in loops rather than vertices. To fix this at the cost of additional vertices, check the “Modify geometry” checkbox during export. If this helps only partially, split the edges of the mesh completely.

## TODO:
- LOD levels
- Terrain shaders
- Vehicle shaders
- VertexInfo: tangent0-tangent7
- Mass export
- Import
- Export to other game formats
