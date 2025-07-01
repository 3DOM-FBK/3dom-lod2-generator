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

    print_to_terminal(f"--> Saved mesh to: {out_path}")


if __name__ == "__main__":
    args = parse_args()

    # Read Shapefile Polygons
    print_to_terminal("Read Shapefile...")
    polygons, (x_offset, y_offset) = read_shapefile_polygons(args.input_shapefile)

    # Get start Time
    start = time.perf_counter()

    # Process Roof
    for i, poly in enumerate(polygons):
        obj_name = f"Building_{i}"
        print_to_terminal(f"--> Process {obj_name}...")
        obj = create_mesh_from_polygon(obj_name, poly['exterior'], poly['holes'])

        roof_dispatch = {
            'flat': lambda: create_flat_roof(obj, poly['height'], poly['exterior'], round_edges=args.round_edges),
            'gabled': lambda: create_gabled_roof(obj, poly['height'], poly['exterior'], round_edges=args.round_edges),
            'gabled-L': lambda: create_gabled_L_roof(obj, poly['height'], i, poly['exterior'], round_edges=args.round_edges),
            'hip': lambda: create_hip_roof(obj, poly['height'], i, poly['exterior'], round_edges=args.round_edges),
            'pyramid': lambda: create_pyramid_roof(obj, poly['height'], i, poly['exterior'], round_edges=args.round_edges),
        }

        roof_type = poly.get('roof')
        if roof_type in roof_dispatch:
            roof_dispatch[roof_type]()

        export_and_shift_mesh(obj, i, x_offset, y_offset, args.output_folder, args.export_format)
    
    # Get end Time and print execution time
    end = time.perf_counter()
    print_to_terminal(f"Execution time: {end - start:.4f} seconds")