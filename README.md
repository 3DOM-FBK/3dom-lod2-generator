# 3dom-lod2-generator

A tool for generating Level of Detail 2 (LOD2) 3D building models from shapefile data and point clouds. The tool combines computational geometry algorithms with 3D modeling to reconstruct buildings with detailed roof structures.

## Mathematical Methods Used for Reconstruction

This section describes the core mathematical algorithms and methods used in the 3D building reconstruction pipeline.

### 1. Straight Skeleton Algorithm

**Purpose**: Generates hip roofs and complex roof structures from 2D building footprints.

**Method**: The tool uses CGAL's `extrude_skeleton` function, which implements the straight skeleton algorithm:
- For a polygon P, the straight skeleton is the set of points that have more than one closest point on the boundary of P
- Each edge of the polygon moves inward at constant speed, maintaining its orientation
- The skeleton consists of angular bisectors where edges meet
- The algorithm handles polygons with holes for complex building shapes

**Mathematical Foundation**:
```
For polygon vertices V = {v₁, v₂, ..., vₙ} and edges E = {e₁, e₂, ..., eₙ}
Skeleton S = {p ∈ P | |{q ∈ ∂P : d(p,q) = d(p,∂P)}| ≥ 2}
```

**Implementation**: Located in `tool/cpp/skeleton.cpp` using CGAL library.

### 2. Minimum Bounding Box Algorithm

**Purpose**: Determines optimal orientation for gabled roofs by finding the minimum-area oriented bounding box.

**Method**: Rotating calipers algorithm:
- Computes the convex hull of the building footprint
- Tests bounding box orientations at each edge angle of the convex hull  
- Selects orientation that minimizes bounding box area
- Uses this orientation to determine the ridge direction for gabled roofs

**Mathematical Foundation**:
```
For convex hull H with edges at angles θ₁, θ₂, ..., θₖ:
Optimal angle θ* = argmin(Area(BoundingBox(H, θᵢ)))
```

**Implementation**: Located in `tool/modeling/min_bounding_rect.py`.

### 3. Roof Slope Calculations

**Purpose**: Calculates roof heights based on geometric constraints and slope percentages.

**Method**: Simple trigonometric relationship for gabled roofs:
```
height = (slope_percent / 100.0) × base_length
```

**Default Parameters**:
- Standard roof slope: 22% (approximately 12.4° angle)
- Base length: Half the width of the minimum bounding box

**Implementation**: Function `calculate_roof_height()` in `tool/modeling/roofs/gabled.py`.

### 4. Point Cloud Processing

**Purpose**: Extracts height information from LAS point cloud data for accurate building height determination.

**Methods**:
- **Spatial filtering**: Uses axis-aligned bounding boxes for efficient point selection
- **Point-in-polygon tests**: Determines which points fall within building footprints
- **Statistical analysis**: Computes height statistics (mean, percentiles) for roof elevation

**Mathematical Foundation**:
```
For point p = (x, y, z) and polygon footprint F:
p ∈ F ⟺ Point(x, y) intersects Polygon(F)
```

**Implementation**: Located in `tool/modeling/pointcloud_ops.py`.

### 5. Boolean Operations (Constructive Solid Geometry)

**Purpose**: Combines and subtracts 3D meshes to create complex roof geometries.

**Methods**:
- **Difference**: `A - B` removes volume B from mesh A (used for creating roof cuts)
- **Intersection**: `A ∩ B` keeps only overlapping volumes (used for edge rounding)
- **Union**: `A ∪ B` combines volumes (used for joining roof and base)

**Mathematical Foundation**:
```
For meshes A and B with point sets PA and PB:
A - B = {p ∈ PA | p ∉ PB}
A ∩ B = {p | p ∈ PA ∧ p ∈ PB}
A ∪ B = {p | p ∈ PA ∨ p ∈ PB}
```

**Implementation**: Via Blender's boolean modifiers in `tool/modeling/blender_ops.py`.

### 6. Geometric Transformations

**Purpose**: Align, scale, and position 3D geometry components.

**Methods**:
- **Translation**: `T(v) = v + t` where t is translation vector
- **Scaling**: `S(v) = (sx·vx, sy·vy, sz·vz)` for scale factors (sx, sy, sz)  
- **Extrusion**: Extends 2D polygons into 3D by adding height dimension
- **Alignment**: Positions roof geometry to match base building height

**Mathematical Foundation**:
```
Homogeneous transformation matrix:
[x']   [sx  0   0  tx] [x]
[y'] = [0   sy  0  ty] [y]
[z']   [0   0   sz tz] [z]
[1 ]   [0   0   0  1 ] [1]
```

### 7. Polygon Processing

**Purpose**: Simplifies and prepares 2D building footprints for 3D reconstruction.

**Methods**:
- **Vertex merging**: Combines vertices within tolerance distance
- **Edge simplification**: Removes redundant points on straight edges
- **Triangulation**: Converts polygons to triangle meshes for rendering
- **Convex hull**: Computes outer boundary for bounding box calculations

**Mathematical Foundation**:
```
Vertex merge condition: ||vi - vj|| < ε for tolerance ε
Douglas-Peucker simplification: max perpendicular distance to edge < threshold
```

**Implementation**: Various functions in `tool/modeling/blender_ops.py`.

## Roof Type Algorithms

### Flat Roofs
Simple vertical extrusion of the building footprint polygon.

### Gabled Roofs  
1. Compute minimum bounding box orientation
2. Split bounding box along longest dimension to create ridge
3. Apply slope calculation to determine ridge height
4. Use boolean difference to cut sloped volume from extruded base

### Hip Roofs
1. Export building footprint to external C++ process
2. Apply straight skeleton algorithm with maximum height constraint
3. Import generated 3D roof mesh
4. Align and join with extruded building base

### Pyramid Roofs
Specialized case of hip roof where all edges slope to a central apex point.

### L-Shaped Gabled Roofs
Complex roofs for L-shaped building footprints, combining multiple gabled sections with proper intersection handling.

## Implementation Overview

The reconstruction pipeline combines multiple programming languages and libraries:

- **Python**: Main orchestration using Blender's Python API
- **C++**: High-performance geometric algorithms using CGAL
- **Blender**: 3D modeling operations and boolean geometry
- **CGAL**: Computational geometry library for skeleton algorithms
- **Shapely**: 2D geometric operations and spatial analysis

## Key Dependencies

- **CGAL 6.0.1**: Computational Geometry Algorithms Library
- **Blender 4.4**: 3D modeling and mesh operations  
- **Python Libraries**: plyfile, shapely, geopandas, trimesh, scipy, laspy, numpy

## References

1. Aichholzer, O., & Aurenhammer, F. (1996). Straight skeletons for general polygonal figures in the plane. In *Computing and Combinatorics* (pp. 117-126).

2. Felkel, P., & Obdržálek, Š. (1998). Straight skeleton implementation. In *Proceedings of Spring Conference on Computer Graphics* (pp. 210-218).

3. Preparata, F. P., & Shamos, M. I. (1985). *Computational geometry: an introduction*. Springer-Verlag.

4. Freeman, H., & Shapira, R. (1975). Determining the minimum-area encasing rectangle for an arbitrary closed curve. *Communications of the ACM*, 18(7), 409-413.
