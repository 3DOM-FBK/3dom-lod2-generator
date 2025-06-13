import bpy


### function: export_mesh_ply ###
def export_mesh_ply(filepath, obj=None, use_ascii=False):
    """
    Exports a mesh to PLY format (binary or ASCII) using Blender 4.4's wm.ply_export operator.

    Args:
        filepath (str): Full path to the .ply file to be created.
        obj (bpy.types.Object, optional): If provided, only this object will be exported;
                                          otherwise, the entire scene is exported.
        use_ascii (bool): True for ASCII format, False for binary format.
    """
    if obj:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        use_selection = True
    else:
        use_selection = False

    bpy.ops.wm.ply_export(
        filepath=filepath,
        export_selected_objects=use_selection,
        ascii_format=use_ascii
    )