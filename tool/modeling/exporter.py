import bpy


### function: export_mesh_ply ###
def export_mesh_ply(filepath, obj=None, use_ascii=False):
    """
    Esporta in PLY (binario o ASCII) usando il nuovo operatore wm.ply_export di Blender 4.4.
    
    Args:
        filepath (str): percorso completo del .ply da creare
        obj (bpy.types.Object, opzionale): se passato, verrà esportato solo questo oggetto; 
                                           altrimenti tutta la scena
        use_ascii (bool): True per ASCII, False per binario
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