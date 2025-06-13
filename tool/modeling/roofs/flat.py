import sys
import os

#######################################################
# Adds the root project in the Python path
#######################################################
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)
#######################################################

import blender_ops as blender_ops


### function: create_flat_roof ###
def create_flat_roof(obj, height):
    """
    Generates a flat roof by merging nearby vertices and extruding the geometry upward.

    Args:
        obj (Object): The input mesh object to modify.
        height (float): The extrusion height for the flat roof.
    """
    blender_ops.merge_close_vertices(obj)
    blender_ops.extrude_faces_z(obj, height)