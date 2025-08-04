import bpy
import os
import sys
import subprocess


#######################################################
# Adds the root project in the Python path
#######################################################
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)
#######################################################


from io_utils.exporter import export_polygon_to_txt
from io_utils.importer import import_ply
import modeling.blender_ops as blender_ops
from shapefile.converter import create_mesh_from_polygon


TMP_OUT_MESH = "/tmp/hip.ply"
CPP_PATH = "/app/tool/cpp/build/extrude_skeleton"


### function: run_executable ###
def run_executable(exe_path, args=None):
    cmd = [exe_path]
    if args:
        cmd.extend(args)

    proc = subprocess.run(cmd, capture_output=True, text=True)

    return proc.stdout, proc.stderr, proc.returncode


### function: create_hip_roof ###
def create_gabled_L_roof(base_obj, height, idx, exterior_coords, round_edges=False):
    """
    Creates a hip roof on top of a base mesh object using an external C++ process.
    If the external process fails, only the base mesh is extruded.

    Parameters:
    - base_obj (Object): The base Blender mesh object.
    - height (float): Desired total height of the final mesh including the hip roof.
    - idx (int): Index used for temporary file naming.
    - exterior_coords (list of tuple): Coordinates of the outer loop (used for edge rounding).
    - round_edges (bool): Whether to round the external edges of the roof.

    Returns:
    - Object: The final mesh object (either roof + base or just base extruded).
    """
    blender_ops.merge_close_vertices(base_obj)

    # Export base polygon for roof generation
    txt_path = f"/tmp/input_{idx}.txt"
    export_polygon_to_txt(base_obj, txt_path)

    # Attempt to generate hip roof using external process
    stdout, stderr, code = run_executable(CPP_PATH, [txt_path, TMP_OUT_MESH, "2000.0"])

    if code != 0:
        print("⚠️ External C++ process failed. Skipping hip roof generation.")
        blender_ops.extrude_faces_z(base_obj, height)
    else:
        # Import generated hip roof mesh
        try:
            hip_obj = import_ply(TMP_OUT_MESH)
            blender_ops.clean_tmp_folder()
            blender_ops.delete_downward_faces(hip_obj)

            blender_ops.merge_close_vertices(hip_obj)
            blender_ops.limited_dissolve_all_faces(hip_obj)
            blender_ops.align_top_vertex_to_plane(hip_obj)
            blender_ops.triangulate_mesh(hip_obj)

            hip_height = blender_ops.get_mesh_height(hip_obj)
            base_extrude_height = height - hip_height
            if (base_extrude_height < 0):
                base_extrude_height = 1.0

            blender_ops.extrude_faces_z(base_obj, base_extrude_height)
            blender_ops.align_bottom_to_top(hip_obj, base_obj)
            blender_ops.delete_facing_up_faces(base_obj)

            # Join roof with base
            blender_ops.join_meshes(base_obj, hip_obj)
            blender_ops.merge_close_vertices(base_obj)

            blender_ops.limited_dissolve_all_faces(base_obj)
        except:
            print("⚠️ failed importing geometry.")

    if round_edges:
        round_obj = create_mesh_from_polygon("round_edge", exterior_coords, [])
        blender_ops.merge_close_vertices(round_obj)
        blender_ops.limited_dissolve_all_faces(round_obj)
        blender_ops.compute_custom_vertex_attribute(round_obj, target_coords=exterior_coords)
        blender_ops.apply_bevel_modifier(round_obj, width=2)
        blender_ops.extrude_faces_z(round_obj, base_extrude_height + 1)
        blender_ops.apply_boolean_intersect(base_obj, round_obj, apply=True)

        # Clean final mesh
        blender_ops.triangulate_mesh(base_obj)
        blender_ops.merge_close_vertices(base_obj)
        blender_ops.limited_dissolve_all_faces(base_obj)
        blender_ops.triangulate_mesh(base_obj)

    blender_ops.triangulate_mesh(base_obj)