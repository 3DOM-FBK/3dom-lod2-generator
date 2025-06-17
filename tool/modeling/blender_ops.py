import bpy
import bmesh
from mathutils import Vector
import mathutils
import numpy as np
import os
import shutil
import math


### function: clean_tmp_folder ###
def clean_tmp_folder(path="/tmp") -> bool:
    """
    Cleans a directory by removing all its contents (files and subdirectories).

    Args:
        path (str): Path to the directory to clean. Defaults to '/tmp'.

    Returns:
        bool: True if cleaning succeeded, False otherwise.
    """
    if not os.path.exists(path) or not os.path.isdir(path):
        print(f"Directory does not exist or is not a directory: {path}")
        return False

    try:
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # remove file or link
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # remove directory and its contents
        return True
    except Exception as e:
        print(f"Error cleaning directory {path}: {e}")
        return False


### function: clear_blender_scene ###
def clear_blender_scene():
    bpy.ops.object.select_all(action='DESELECT')

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    data_types = [
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.textures,
        bpy.data.images,
        bpy.data.curves,
        bpy.data.lights,
        bpy.data.cameras,
        bpy.data.armatures,
        bpy.data.objects,
        bpy.data.collections
    ]

    for data_block in data_types:
        for item in data_block:
            if item.users == 0:
                data_block.remove(item)

    # Rimuove tutte le collezioni non usate
    for collection in bpy.data.collections:
        if collection.users == 0:
            bpy.data.collections.remove(collection)

    print("Clean Scene - Done")



### function: extrude_faces_z ###
def extrude_faces_z(obj, height):
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
def align_mesh_to_reference(bbox_obj, height):
    def get_max_world_z(obj):
        return max((obj.matrix_world @ v.co).z for v in obj.data.vertices)

    max_z_bbox = get_max_world_z(bbox_obj)

    delta_z = height - max_z_bbox

    bbox_obj.location.z += delta_z


### function: merge_close_vertices ###
def merge_close_vertices(obj, distance=0.001):
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
    if obj_target.type != 'MESH' or obj_cutter.type != 'MESH':
        raise TypeError("Entrambi gli oggetti devono essere mesh.")

    bpy.context.view_layer.objects.active = obj_target
    obj_target.select_set(True)
    obj_cutter.select_set(False)

    mod = obj_target.modifiers.new(name=modifier_name, type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = obj_cutter

    bpy.ops.object.modifier_apply(modifier=modifier_name)

    return obj_target


def apply_boolean_intersect(obj_a, obj_b, apply=True):
    if obj_a is None or obj_b is None:
        print("Entrambi gli oggetti devono essere specificati.")
        return

    bpy.context.view_layer.objects.active = obj_a
    bpy.ops.object.select_all(action='DESELECT')
    obj_a.select_set(True)

    mod = obj_a.modifiers.new(name="Boolean_Intersect", type='BOOLEAN')
    mod.operation = 'INTERSECT'
    mod.object = obj_b
    mod.solver = 'EXACT'

    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)


### function: get_exterior_and_hole_loops ###
def get_exterior_and_hole_loops(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    boundary_edges = [e for e in bm.edges if len(e.link_faces) == 1]

    vert_to_boundary_edges = {}
    for e in boundary_edges:
        for v in e.verts:
            vert_to_boundary_edges.setdefault(v.index, []).append(e)

    def extract_loop(start_edge):
        loop_verts = []
        current_edge = start_edge
        current_vert = start_edge.verts[0]
        visited = set()

        while True:
            loop_verts.append(current_vert)
            next_vert = current_edge.other_vert(current_vert)

            connected_edges = [
                e for e in vert_to_boundary_edges[next_vert.index]
                if e != current_edge and e.index not in visited
            ]
            visited.add(current_edge.index)

            if not connected_edges:
                break
            next_edge = connected_edges[0]

            current_vert = next_vert
            current_edge = next_edge

            if current_vert == loop_verts[0]:
                break

        return loop_verts

    visited_edges = set()
    loops = []

    for e in boundary_edges:
        if e.index in visited_edges:
            continue

        loop_verts = extract_loop(e)
        for i in range(len(loop_verts)):
            v1 = loop_verts[i]
            v2 = loop_verts[(i + 1) % len(loop_verts)]
            edge = bm.edges.get([v1, v2])
            if edge:
                visited_edges.add(edge.index)

        loops.append(loop_verts)

    def is_clockwise(verts):
        coords = [(v.co.x, v.co.y) for v in verts]
        area = 0
        for i in range(len(coords)):
            x1, y1 = coords[i]
            x2, y2 = coords[(i + 1) % len(coords)]
            area += x1 * y2 - x2 * y1
        return area < 0

    def shoelace_area(verts):
        coords = [(v.co.x, v.co.y) for v in verts]
        area = 0
        for i in range(len(coords)):
            x1, y1 = coords[i]
            x2, y2 = coords[(i + 1) % len(coords)]
            area += x1 * y2 - x2 * y1
        return area / 2

    loops_sorted = sorted(loops, key=lambda lv: abs(shoelace_area(lv)), reverse=True)
    exterior_loop = loops_sorted[0]
    holes = loops_sorted[1:]

    # CGAL: esterno antiorario
    if is_clockwise(exterior_loop):
        exterior_loop.reverse()

    # CGAL: fori orari
    for hole_loop in holes:
        if not is_clockwise(hole_loop):
            hole_loop.reverse()

    exterior_indices = [v.index for v in exterior_loop]
    holes_indices = [[v.index for v in hole] for hole in holes]

    bm.free()
    return exterior_indices, holes_indices


### function: delete_downward_faces ###
def delete_downward_faces(obj=None):
    if obj is None:
        obj = bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        print("No object selected.")
        return

    bpy.ops.object.mode_set(mode='OBJECT')
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    bm.normal_update()

    faces_to_delete = [f for f in bm.faces if f.normal.z < 0]

    bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')

    verts_to_delete = [v for v in bm.verts if len(v.link_faces) == 0]
    bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')

    bm.to_mesh(mesh)
    mesh.update()
    bm.free()


### function: delete_facing_up_faces ###
def delete_facing_up_faces(obj, threshold=0.0):
    if obj.type != 'MESH':
        print("Selected object is not a mesh")
        return

    bpy.ops.object.mode_set(mode='OBJECT')
    mesh = obj.data

    bm = bmesh.new()
    bm.from_mesh(mesh)

    bm.faces.ensure_lookup_table()

    up_faces = [f for f in bm.faces if f.normal.z > threshold]

    bmesh.ops.delete(bm, geom=up_faces, context='FACES')

    bm.to_mesh(mesh)
    bm.free()


### function: get_mesh_height ###
def get_mesh_height(obj=None):
    if obj is None:
        obj = bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        print("No valid mesh selected")
        return None

    bpy.ops.object.mode_set(mode='OBJECT')

    zs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    z_values = [v.z for v in zs]

    z_min = min(z_values)
    z_max = max(z_values)
    height = z_max - z_min

    return height


### function: align_bottom_to_top ###
def align_bottom_to_top(source_obj, reference_obj):
    if not source_obj or not reference_obj:
        print("No valid Objects.")
        return

    source_zs = [source_obj.matrix_world @ v.co for v in source_obj.data.vertices]
    reference_zs = [reference_obj.matrix_world @ v.co for v in reference_obj.data.vertices]

    source_z_min = min(v.z for v in source_zs)
    reference_z_max = max(v.z for v in reference_zs)

    delta_z = reference_z_max - source_z_min

    source_obj.location.z += delta_z


### function: join_meshes ###
def join_meshes(obj1, obj2):
    if obj1.type != 'MESH' or obj2.type != 'MESH':
        print("Both objects must be of type MESH.")
        return

    bpy.ops.object.select_all(action='DESELECT')
    obj1.select_set(True)
    obj2.select_set(True)
    bpy.context.view_layer.objects.active = obj1

    bpy.ops.object.join()


### function: bevel_vertical_edges ###
def bevel_vertical_edges(obj=None, angle_threshold_deg=10, width=0.03, segments=3, profile=0.5):
    if obj is None:
        obj = bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        print("No object selected")
        return False

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    for e in bm.edges:
        e.select = False

    z_axis = Vector((0, 0, 1))
    angle_thresh_rad = math.radians(angle_threshold_deg)

    for e in bm.edges:
        vec = (e.verts[1].co - e.verts[0].co).normalized()
        angle = vec.angle(z_axis)
        if angle < angle_thresh_rad or abs(angle - math.pi) < angle_thresh_rad:
            e.select = True

    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.bevel(offset=width, segments=segments, profile=profile, affect='EDGES')
    bpy.ops.object.mode_set(mode='OBJECT')
    return True


### function: bevel_vertical_edges ###
def limited_dissolve_all_faces(obj=None, angle_limit=0.01):
    if obj is None:
        obj = bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        print("Nessun oggetto mesh attivo o non è una mesh.")
        return

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.dissolve_limited(angle_limit=angle_limit)
    bpy.ops.object.mode_set(mode='OBJECT')


### function: compute_custom_vertex_attribute ###
def compute_custom_vertex_attribute(obj=None, attr_name="bevel_weight_vert", default_value=1.0, target_coords=[]):
    if obj is None:
        obj = bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        print("Oggetto non valido.")
        return

    mesh = obj.data
    target_coords = [Vector(c) for c in target_coords]

    if attr_name in mesh.attributes:
        mesh.attributes.remove(mesh.attributes[attr_name])

    attr = mesh.attributes.new(name=attr_name, type='FLOAT', domain='POINT')

    bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()

    epsilon = 1e-6
    values = [0.0] * len(bm.verts)

    for i, v in enumerate(bm.verts):
        if any((v.co - c).length < epsilon for c in target_coords):
            min_dist = None
            for edge in v.link_edges:
                other = edge.other_vert(v)
                # Calcola distanza solo se anche il vertice collegato è nella lista target
                if any((other.co - c).length < epsilon for c in target_coords):
                    dist = (v.co - other.co).length
                    if min_dist is None or dist < min_dist:
                        min_dist = dist

            if min_dist is None:
                val = 0.0
            elif default_value < (min_dist / 2.0):
                val = 1.0
            else:
                val = ((min_dist / 2.0) / default_value) - 0.05

            values[i] = max(0.0, val)
        else:
            values[i] = 0.0

    bm.free()

    for i, v in enumerate(values):
        attr.data[i].value = v

    mesh.update()


### function: apply_bevel_modifier ###
def apply_bevel_modifier(obj=None, name="Bevel_Weight", width=1, segments=4):
    if obj is None:
        obj = bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        print("Oggetto non valido.")
        return

    mod = obj.modifiers.new(name=name, type='BEVEL')
    mod.limit_method = 'WEIGHT'
    mod.width = width
    mod.segments = segments
    mod.profile = 0.5
    mod.use_clamp_overlap = True
    mod.affect = 'VERTICES'

    bpy.ops.object.modifier_apply(modifier=mod.name)


def triangulate_mesh(obj=None):
    if obj is None:
        obj = bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        print("No object selected")
        return

    bpy.ops.object.mode_set(mode='OBJECT')
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    bmesh.ops.triangulate(bm, faces=bm.faces[:])

    bm.to_mesh(mesh)
    mesh.update()
    bm.free()