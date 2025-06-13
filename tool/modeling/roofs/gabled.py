import sys
import os


#######################################################
# Adds the root project in the Python path
#######################################################
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)
#######################################################

import blender_ops as blender_ops


### function: calculate_roof_height ###
def calculate_roof_height(base_length, slope_percent=22):
    """
    Calculates the height to apply to an edge based on a given slope percentage.

    Args:
        base_length (float): The length of the base to which the slope is applied.
        slope_percent (float): Desired slope expressed as a percentage (default is 22%).

    Returns:
        float: The height needed to achieve the desired slope.
    """
    return (slope_percent / 100.0) * base_length


### function: create_gabled_roof ###
def create_gabled_roof(obj, height):
    """
    Creates a basic gabled roof on a mesh object.

    Steps:
    - Merges close vertices on the object to clean the mesh.
    - Creates an optimal bounding box (minimum area) around the object.
    - Splits the bounding box in half along the longest side.
    - Calculates roof height based on the length of the shorter edge.
    - Moves the central edge upward to form the roof ridge.
    - Aligns the bounding box vertically with the reference object.
    - Extrudes the entire mesh of the object along the Z axis.
    - Applies a Boolean Difference modifier to trim the mesh with the bounding box.

    Args:
        obj (bpy.types.Object): The mesh object to add the roof to.
        height (float): The extrusion height.

    Returns:
        bpy.types.Object: The modified object with the gabled roof.
    """
    
    # Merge vertices that are close to each other for a cleaner mesh
    blender_ops.merge_close_vertices(obj)
    
    # Create the optimal bounding box as a plane
    bbox = blender_ops.create_optimal_bounding_box(obj)
    
    # Split the bounding box along its longest edge, returning new edge indices and short edge length
    new_edge_indices, short_edge_length = blender_ops.split_bbox_plane(bbox)
    
    # Calculate the height to move the central edge based on the short edge length
    height_t = calculate_roof_height(short_edge_length)
    
    # Move the central edge upward to form the roof ridge
    blender_ops.move_edge_up_object(bbox, new_edge_indices, height_t)
    
    # Align the bounding box vertically with the highest point of the reference object
    blender_ops.align_bbox_to_reference(bbox, obj)
    
    # Extrude the original mesh along Z by the specified height
    blender_ops.extrude_faces_z(obj, height)
    
    # Apply Boolean Difference modifier to cut the mesh using the bounding box
    blender_ops.apply_boolean_difference(obj, bbox, modifier_name="Boolean_Diff")
    
    return obj