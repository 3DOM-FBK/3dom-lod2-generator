import bpy
import sys
import os

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
from io_utils.debug import print_to_terminal
import modeling.blender_ops as blender_ops

def main(shapefile_path):
    # Leggi i poligoni dallo shapefile
    print_to_terminal("Read Shapefile...")
    polygons, (x_offset, y_offset) = read_shapefile_polygons(shapefile_path)

    # Per ogni footprint crea la mesh in Blender
    for i, poly in enumerate(polygons):
        obj_name = f"Building_{i}"
        print_to_terminal(f"--> Process {obj_name}...")
        obj = create_mesh_from_polygon(obj_name, poly['exterior'], poly['holes'])

        roof_dispatch = {
            'flat': lambda: create_flat_roof(obj, poly['height'], poly['exterior'], round_edges=True),
            'gabled': lambda: create_gabled_roof(obj, poly['height'], poly['exterior'], round_edges=True),
            'hip': lambda: create_hip_roof(obj, poly['height'], i, poly['exterior'], round_edges=True),
        }

        roof_type = poly.get('roof')
        if roof_type in roof_dispatch:
            roof_dispatch[roof_type]()

        tmp_path = f"/tmp/out_{i}.ply"
        out_path = f"/app/data/out_{i}.obj"
        export_mesh_ply(tmp_path, obj, True)
        apply_global_shift(tmp_path, out_path, x_offset, y_offset)
        blender_ops.clear_blender_scene()
        blender_ops.clean_tmp_folder()

if __name__ == "__main__":
    shapefile_path = "/app/data/input/test_polygon.shp"
    main(shapefile_path)
