import os
import laspy
import numpy as np
import trimesh
import sys
from shapely.geometry import Point, Polygon
from shapely.strtree import STRtree  # usa pygeos sotto il cofano


def load_las_points(las_path, x_offset, y_offset):
    las = laspy.read(las_path)
    points = np.vstack((las.x, las.y, las.z)).T  # Nx3 array
    return points


def get_mesh_bbox_2d_trimesh(mesh):
    xs = mesh.vertices[:, 0]
    ys = mesh.vertices[:, 1]
    minx, maxx = xs.min(), xs.max()
    miny, maxy = ys.min(), ys.max()
    return minx, miny, maxx, maxy


def filter_points_in_bbox_trimesh(points, mesh):
    minx, miny, maxx, maxy = get_mesh_bbox_2d_trimesh(mesh)
    mask = (
        (points[:, 0] >= minx) & (points[:, 0] <= maxx) &
        (points[:, 1] >= miny) & (points[:, 1] <= maxy)
    )
    return points[mask]


# def filter_points_in_polygon(points, polygon: Polygon, buffer_dist=1):
#     if buffer_dist != 0:
#         polygon = polygon.buffer(buffer_dist)
    
#     point_geoms = [Point(xy) for xy in points[:, :2]]
#     tree = STRtree(point_geoms)
#     candidate_idxs = tree.query(polygon)
#     filtered = np.array([
#         points[i] for i in candidate_idxs if polygon.contains(point_geoms[i])
#     ])
#     return filtered


# def get_2d_polygon_from_trimesh(mesh: trimesh.Trimesh) -> Polygon:
#     # Proietta i vertici sul piano XY
#     verts_2d = mesh.vertices[:, :2]
#     # Ottieni le facce come insiemi di coordinate 2D
#     polygons = []
#     for face in mesh.faces:
#         poly = verts_2d[face]
#         polygons.append(poly)
    
#     # Unisci tutto in un unico poligono esterno
#     # (assumiamo che la mesh sia un solo "pezzo" planare)
#     # Prendiamo il contorno del bounding shape (convex hull)
#     boundary = trimesh.path.polygons.projected(mesh, normal=[0, 0, 1])
#     if isinstance(boundary, list):
#         boundary = boundary[0]  # Prendi il primo poligono
    
#     return boundary  # È già un shapely.Polygon


def get_min_max_height(points):
    if points.size == 0:
        return None, None
    z_values = points[:, 2]
    return np.min(z_values), np.max(z_values)


def get_min_max_z_from_filtered_points(filtered):
    if filtered.shape[0] == 0:
        return 10, 0  # Default value

    z_min = filtered[:, 2].min()
    z_max = filtered[:, 2].max()

    # Se l'altezza è troppo bassa, impostala a z_min + 2
    if (z_max - z_min) < 2:
        z_max = z_min + 2

    return z_min, z_max


def get_min_max_las(las_points, tmp_path_bbox, x_offset, y_offset, i):
    mesh = trimesh.load(tmp_path_bbox)
    mesh.apply_translation([x_offset, y_offset, 0])

    # polygon = get_2d_polygon_from_trimesh(mesh)
    # filtered = filter_points_in_polygon(las_points, polygon)

    filtered = filter_points_in_bbox_trimesh(las_points, mesh)

    z_min, z_max = get_min_max_z_from_filtered_points(filtered)

    return z_min, z_max