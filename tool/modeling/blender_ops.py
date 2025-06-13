import bpy
import bmesh
from mathutils import Vector
import mathutils
import numpy as np


### function: extrude_faces_z ###
def extrude_faces_z(obj, height):
    """
    Seleziona tutte le facce dell'oggetto e le estrude lungo Z di 'height'.
    """
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    # Seleziona tutte le facce
    for f in bm.faces:
        f.select = True

    # Estrusione delle facce selezionate
    ret = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    
    # Prende i vertici dell'estrusione e li sposta lungo Z
    verts = [ele for ele in ret['geom'] if isinstance(ele, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts, vec=Vector((0, 0, height)))

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)


### function: create_optimal_bounding_box ###
def create_optimal_bounding_box(obj, name="OBB_Plane", offset=0.5):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    verts = [eval_obj.matrix_world @ v.co for v in mesh.vertices]
    eval_obj.to_mesh_clear()

    points_2d = np.array([[v.x, v.y] for v in verts])

    mean = np.mean(points_2d, axis=0)
    centered = points_2d - mean
    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eigh(cov)

    rotated = centered @ eigvecs

    min_x, min_y = np.min(rotated, axis=0)
    max_x, max_y = np.max(rotated, axis=0)

    # Applica offset su tutti i lati
    min_x -= offset
    min_y -= offset
    max_x += offset
    max_y += offset

    obb_coords = np.array([
        [min_x, min_y],
        [max_x, min_y],
        [max_x, max_y],
        [min_x, max_y]
    ])

    obb_world = (obb_coords @ eigvecs.T) + mean
    obb_3d = [(x, y, 0) for x, y in obb_world]

    mesh_data = bpy.data.meshes.new(name + "_mesh")
    mesh_data.from_pydata(obb_3d, [], [(0, 1, 2, 3)])
    mesh_data.update()

    obb_obj = bpy.data.objects.new(name, mesh_data)
    bpy.context.collection.objects.link(obb_obj)

    return obb_obj


### function: split_bbox_plane ###
def split_bbox_plane(obj):
    """
    Seleziona e suddivide i due edge più corti della mesh.
    Restituisce:
    - Lista dei nuovi edge centrali creati
    - Lunghezza dei lati corti originali
    """
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Calcolo lunghezze
    edge_lengths = [(e, (e.verts[0].co - e.verts[1].co).length) for e in bm.edges]
    edge_lengths.sort(key=lambda x: x[1])
    
    short_edges = [e for e, _ in edge_lengths[:2]]
    short_edge_length = edge_lengths[0][1]  # tutti e due avranno simile lunghezza

    # Deseleziona tutto, poi seleziona solo i più corti
    for e in bm.edges:
        e.select = False
    for e in short_edges:
        e.select = True

    # Suddivide e raccoglie i nuovi edge
    result = bmesh.ops.subdivide_edges(
        bm,
        edges=short_edges,
        cuts=1,
        use_grid_fill=True
    )

    new_edges = result.get('geom_inner', [])
    new_edges = [e for e in new_edges if isinstance(e, bmesh.types.BMEdge)]
    new_edge_indices = [e.index for e in new_edges]

    # Applica modifiche alla mesh
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    return new_edge_indices, short_edge_length


### function: move_edge_up_object ###
def move_edge_up_object(obj, edge_indices, height):
    """
    Sposta verso l'alto i vertici dell'edge indicato di un oggetto mesh.

    :param obj: oggetto Blender
    :param edge_indices: lista di indici degli edge da spostare (usa solo il primo)
    :param height: valore dello spostamento in Z
    """
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.edges.ensure_lookup_table()

    edge = bm.edges[edge_indices[0]]

    for vert in edge.verts:
        vert.co.z += height

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


### function: align_bbox_to_reference ###
def align_bbox_to_reference(bbox_obj, height):
    """
    Sposta la mesh bbox in modo che il suo vertice più alto (in Z, in spazio mondo)
    sia allineato con il vertice più alto della mesh di riferimento.
    """

    def get_max_world_z(obj):
        return max((obj.matrix_world @ v.co).z for v in obj.data.vertices)

    max_z_bbox = get_max_world_z(bbox_obj)

    delta_z = height - max_z_bbox

    # Sposta l'oggetto intero verso l'alto
    bbox_obj.location.z += delta_z


### function: merge_close_vertices ###
def merge_close_vertices(obj, distance=0.001):
    """
    Unisce tutti i vertici dell'oggetto che sono entro 'distance' tra loro.
    """
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    # Merge dei vertici vicini
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)


### function: apply_boolean_difference ###
def apply_boolean_difference(obj_target, obj_cutter, modifier_name="Boolean_Diff"):
    # Assicurati che entrambi gli oggetti siano mesh
    if obj_target.type != 'MESH' or obj_cutter.type != 'MESH':
        raise TypeError("Entrambi gli oggetti devono essere mesh.")

    # Rendi attivo l'oggetto target
    bpy.context.view_layer.objects.active = obj_target
    obj_target.select_set(True)
    obj_cutter.select_set(False)

    # Crea e configura il modificatore boolean
    mod = obj_target.modifiers.new(name=modifier_name, type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = obj_cutter

    # Applica il modificatore
    bpy.ops.object.modifier_apply(modifier=modifier_name)

    return obj_target