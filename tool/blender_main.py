import bpy
import sys
import os
import argparse
import time


# ---------------------------------------------------
#
# blender -b --python blender_main.py > /dev/null 2>&1 -- ...
#
# ---------------------------------------------------


#######################################################
# Adds the root project in the Python path
#######################################################
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
#######################################################

from shapefile.reader import read_shapefile_polygons
from shapefile.converter import create_mesh_from_polygon
from io_utils.exporter import export_mesh_ply
from io_utils.exporter import apply_global_shift
from modeling.roofs.flat import create_flat_roof
from modeling.roofs.gabled import create_gabled_roof
from modeling.roofs.hip import create_hip_roof
from modeling.roofs.pyramid import create_pyramid_roof
from modeling.roofs.gabled_L import create_gabled_L_roof
from io_utils.debug import print_to_terminal
import modeling.blender_ops as blender_ops
import modeling.pointcloud_ops as pointcloud_ops


### function: parse_args ###
def parse_args():
    """
    Parses command line arguments passed to the Blender script after "--".
    
    Returns:
        Namespace: Parsed arguments.
    """
    # Only get args after "--"
    argv = sys.argv
    if "--" not in argv:
        argv = []
    else:
        argv = argv[argv.index("--") + 1:]

    parser = argparse.ArgumentParser(description="Process 3D buildings from shapefile in Blender.")
    
    parser.add_argument("-i", "--input_shapefile", type=str, required=True,
                        help="Path to the input shapefile.")
    
    parser.add_argument("-o", "--output_folder", type=str, required=True,
                        help="Folder where the generated meshes will be saved.")
    
    parser.add_argument("-r", "--round_edges", action="store_true",
                        help="Apply rounding (bevel) to roof edges.")
    
    parser.add_argument("--export_format", type=str, default="ply", choices=["ply", "obj"],
                        help="File format to export the resulting mesh (default: ply).")
    
    parser.add_argument("--las", type=str,
                        help="Las file")

    return parser.parse_args(argv)


def export_and_shift_mesh(obj, i, x_offset, y_offset, output_folder, export_format="ply"):
    """
    Exports a mesh to a temporary PLY, applies a global shift, and re-exports
    in the desired format.

    Args:
        obj (trimesh.Trimesh): The mesh object to export.
        i (int): Index for output file naming.
        x_offset (float): Offset along X axis.
        y_offset (float): Offset along Y axis.
        output_folder (str): Directory where the final mesh will be saved.
        export_format (str): Final export format ("ply" or "obj").
    """
    assert export_format in ["ply", "obj"], "Unsupported export format"

    tmp_path = f"/tmp/out_{i}.ply"
    out_path = os.path.join(output_folder, f"out_{i}.{export_format}")

    export_mesh_ply(tmp_path, obj, True)

    apply_global_shift(tmp_path, out_path, x_offset, y_offset)

    blender_ops.clear_blender_scene()
    blender_ops.clean_tmp_folder()

    print_to_terminal(f"----> Saved mesh to: {out_path}")


def process_roofs(polygons_to_process, x_offset, y_offset, las_points, args, force_roof_type=None):
    """
    Processes a list of building footprints and generates corresponding 3D roof meshes.

    Args:
        polygons_to_process (list): List of polygon dictionaries, each containing 'exterior', 'holes', and optionally 'roof' and 'index'.
        x_offset (float): Offset in the X direction to apply during export.
        y_offset (float): Offset in the Y direction to apply during export.
        las_points: Point cloud data already loaded in memory.
        args: Parsed command-line arguments (must contain output_folder, export_format, round_edges).
        force_roof_type (str, optional): If provided, overrides the 'roof' attribute in the polygon and applies this roof type to all buildings.

    Returns:
        list: List of indices corresponding to buildings that failed the process (e.g. due to empty meshes or unsupported roof types).
    """
    failed_indices = []

    for i, poly in enumerate(polygons_to_process):
        idx = poly['index'] if 'index' in poly else i  # useful for second pass
        obj_name = f"Building_{idx}"
        print_to_terminal(f"--> Processing {obj_name}...")

        obj = create_mesh_from_polygon(obj_name, poly['exterior'], poly['holes'])

        tmp_path_bbox = f"/tmp/bbox_mask_{idx}.ply"
        export_mesh_ply(tmp_path_bbox, obj, True)

        z_min, z_max = pointcloud_ops.get_min_max_las(las_points, tmp_path_bbox, x_offset, y_offset, idx)

        if z_max is not None:
            print(f"Highest point: {z_max}")
            print(f"Lowest point: {z_min}")
        else:
            print("⚠ No points found in the bounding box.")

        blender_ops.flatten_mesh_to_z(obj, z_min)
        poly['height'] = z_max - z_min

        roof_dispatch = {
            'flat': lambda: create_flat_roof(obj, poly['height'], poly['exterior'], round_edges=args.round_edges),
            'gabled': lambda: create_gabled_roof(obj, poly['height'], poly['exterior'], round_edges=args.round_edges),
            'gabled-L': lambda: create_gabled_L_roof(obj, poly['height'], idx, poly['exterior'], round_edges=args.round_edges),
            'hip': lambda: create_hip_roof(obj, poly['height'], idx, poly['exterior'], round_edges=args.round_edges),
            'pyramid': lambda: create_pyramid_roof(obj, poly['height'], idx, poly['exterior'], round_edges=args.round_edges),
        }

        roof_type = force_roof_type if force_roof_type else poly.get('roof')
        if roof_type in roof_dispatch:
            roof_dispatch[roof_type]()
        else:
            print(f"⚠ Unsupported roof type '{roof_type}' for building {idx}")
            failed_indices.append(idx)
            bpy.data.objects.remove(obj, do_unlink=True)
            continue

        if blender_ops.count_mesh_points(obj) == 0:
            print(f"⚠ Empty mesh generated for building {idx}, it will be reprocessed.")
            failed_indices.append(idx)
            bpy.data.objects.remove(obj, do_unlink=True)
            continue

        export_and_shift_mesh(obj, idx, x_offset, y_offset, args.output_folder, args.export_format)

    return failed_indices


##### Temporary function
# def export_meshes_to_ply(mesh_objects, export_format="obj", x_offset=0, y_offset=0, output_folder="/root"):
#     """
#     Exports the given list of mesh objects to a single OBJ file.

#     Args:
#         mesh_objects (list of bpy.types.Object): List of mesh objects to export.
#         output_path (str): Path to save the OBJ file.
#     """
#     # Deselect all objects first
#     bpy.ops.object.select_all(action='DESELECT')

#     # Select only the desired mesh objects
#     for obj in mesh_objects:
#         obj.select_set(True)

#     # Set one of them as the active object (required by some export ops)
#     bpy.context.view_layer.objects.active = mesh_objects[0]

#     # tmp_path = f"/tmp/all_buildings.ply"
#     tmp_path = os.path.join(output_folder, f"all_buildings.ply")
#     out_path = os.path.join(output_folder, f"all_buildings.{export_format}")

#     bpy.ops.wm.ply_export(
#         filepath=tmp_path,
#         export_selected_objects=True,
#         ascii_format=False
#     )

#     apply_global_shift(tmp_path, out_path, x_offset, y_offset)


if __name__ == "__main__":
    args = parse_args()

    # Get start Time
    start = time.perf_counter()

    # Read Shapefile Polygons
    print_to_terminal("Read Shapefile...")
    polygons, (x_offset, y_offset) = read_shapefile_polygons(args.input_shapefile)

    print ("--> Read LAS...")
    las_points = pointcloud_ops.load_las_points(args.las, x_offset, y_offset)

    for i, poly in enumerate(polygons):
        poly['index'] = i  # Save global indices

    failed_idxs = process_roofs(polygons, x_offset, y_offset, las_points, args)

    if failed_idxs:
        print_to_terminal(f"\n---> Retry su {len(failed_idxs)} edifici con tetto flat")
        retry_polygons = [polygons[i] for i in failed_idxs]
        process_roofs(retry_polygons, x_offset, y_offset, las_points, args, force_roof_type='flat')
    
    # Get end Time and print execution time
    end = time.perf_counter()
    print_to_terminal(f"Execution time: {end - start:.4f} seconds")