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
from modeling.exporter import export_mesh_ply
from modeling.roofs.flat import create_flat_roof
from modeling.roofs.gabled import create_gabled_roof

def main(shapefile_path):
    # Leggi i poligoni dallo shapefile
    polygons, (x_offset, y_offset) = read_shapefile_polygons(shapefile_path)

    # Per ogni footprint crea la mesh in Blender
    for i, poly in enumerate(polygons):

        obj_name = f"Building_{i}"
        obj = create_mesh_from_polygon(obj_name, poly['exterior'], poly['holes'])
        print(f"Creato {obj_name} con {len(poly['holes'])} hole(s)")

        bbox = create_gabled_roof(obj, poly['height'])

        path = f"/app/data/bbox_out_{i}.ply"
        export_mesh_ply(path, bbox, True)

if __name__ == "__main__":
    shapefile_path = "/app/data/input/test_polygon.shp"
    main(shapefile_path)
