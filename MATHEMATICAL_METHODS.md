# Mathematical Methods - Detailed Technical Documentation

This document provides in-depth technical details about the mathematical algorithms used in the 3DOM-LOD2-Generator for 3D building reconstruction.

## 1. Straight Skeleton Algorithm - Technical Details

### Algorithm Description
The straight skeleton of a polygon is computed by continuously shrinking the polygon, moving each edge inward at constant speed while maintaining edge orientation.

### Mathematical Formulation

For a simple polygon P with vertices V = {v₀, v₁, ..., vₙ₋₁}:

1. **Edge Representation**: Each edge eᵢ is represented by a ray with:
   - Origin: vertex vᵢ  
   - Direction: unit vector perpendicular to edge, pointing inward

2. **Shrinking Process**: At time t, each vertex moves along its angular bisector:
   ```
   vᵢ(t) = vᵢ + t · bisector(eᵢ₋₁, eᵢ)
   ```

3. **Event Detection**: The algorithm tracks two types of events:
   - **Edge events**: When an edge shrinks to zero length
   - **Split events**: When a reflex vertex hits an edge

4. **Skeleton Construction**: The skeleton consists of:
   - Line segments connecting event points
   - Portions of angular bisectors between events

### CGAL Implementation Details

The CGAL implementation uses exact arithmetic to avoid numerical instability:

```cpp
// Key function call in skeleton.cpp
CGAL::extrude_skeleton(poly, sm, CGAL::parameters::maximum_height(height));
```

**Parameters**:
- `poly`: Input polygon with holes (Polygon_with_holes_2)
- `sm`: Output surface mesh (Surface_mesh)  
- `maximum_height`: Height constraint for extrusion

### Complexity Analysis
- **Time Complexity**: O(n log n) for simple polygons, O(n² log n) for polygons with holes
- **Space Complexity**: O(n) for skeleton storage

## 2. Minimum Bounding Box Algorithm - Technical Details

### Rotating Calipers Method

The algorithm finds the minimum-area oriented bounding rectangle using the rotating calipers technique.

### Mathematical Foundation

For a convex hull H with vertices {h₀, h₁, ..., hₖ₋₁}:

1. **Edge Angles**: Compute angle θᵢ for each edge:
   ```
   θᵢ = atan2(hᵢ₊₁.y - hᵢ.y, hᵢ₊₁.x - hᵢ.x)
   ```

2. **Rotation Matrix**: For angle θ, the rotation matrix is:
   ```
   R(θ) = [cos(θ)  -sin(θ)]
          [sin(θ)   cos(θ)]
   ```

3. **Bounding Box Calculation**: For each angle θᵢ:
   - Rotate all points: h'ⱼ = R(-θᵢ) · hⱼ
   - Compute axis-aligned bounding box of rotated points
   - Calculate area = (max_x - min_x) × (max_y - min_y)

4. **Optimization**: Select θ* that minimizes bounding box area

### Implementation Pseudocode

```python
def minBoundingRect(hull_points):
    # Compute edge angles
    edges = compute_edges(hull_points)
    angles = [atan2(edge.y, edge.x) for edge in edges]
    
    min_area = float('inf')
    best_angle = 0
    
    for angle in unique_angles(angles):
        # Rotate points
        rotated = rotate_points(hull_points, -angle)
        
        # Compute AABB
        bbox = axis_aligned_bbox(rotated)
        area = bbox.width * bbox.height
        
        if area < min_area:
            min_area = area
            best_angle = angle
    
    return best_angle, min_area
```

## 3. Point Cloud Processing - Statistical Methods

### Height Determination Algorithm

The tool extracts building heights from LAS point cloud data using statistical analysis.

### Spatial Filtering

1. **Bounding Box Test**: Fast prefiltering using axis-aligned bounding boxes:
   ```
   point_in_bbox(p, bbox) ⟺ 
       bbox.min_x ≤ p.x ≤ bbox.max_x ∧
       bbox.min_y ≤ p.y ≤ bbox.max_y
   ```

2. **Point-in-Polygon Test**: Precise filtering using ray casting algorithm:
   ```python
   def point_in_polygon(point, polygon):
       x, y = point.x, point.y
       n = len(polygon.vertices)
       inside = False
       
       j = n - 1
       for i in range(n):
           xi, yi = polygon.vertices[i]
           xj, yj = polygon.vertices[j]
           
           if ((yi > y) != (yj > y)) and \
              (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
               inside = not inside
           j = i
       
       return inside
   ```

### Statistical Analysis

For height extraction from filtered points:

1. **Outlier Removal**: Remove points beyond μ ± 2σ where:
   - μ = mean height
   - σ = standard deviation

2. **Robust Statistics**: Use percentiles for height estimation:
   - Ground level: 5th percentile
   - Roof level: 95th percentile
   - Building height: 95th percentile - 5th percentile

3. **Density Analysis**: Filter points by return intensity and classification codes

## 4. Boolean Operations - Computational Geometry

### Mesh Boolean Operations

The tool uses Blender's boolean modifiers for Constructive Solid Geometry (CSG).

### Mathematical Foundation

For meshes represented as boundary representations (B-rep):

1. **Intersection Calculation**: Find intersection curves between mesh boundaries
2. **Classification**: Classify mesh regions as inside/outside/on-boundary
3. **Construction**: Build result mesh from classified regions

### Boolean Operation Types

1. **Difference (A - B)**:
   ```
   Result = {faces ∈ A | faces ∉ interior(B)}
   ```

2. **Intersection (A ∩ B)**:
   ```
   Result = {faces | faces ∈ interior(A) ∧ faces ∈ interior(B)}
   ```

3. **Union (A ∪ B)**:
   ```
   Result = {faces | faces ∈ A ∨ faces ∈ B} - intersection_edges
   ```

### Robustness Considerations

- Use exact arithmetic for intersection calculations
- Handle degenerate cases (coincident faces, edges)
- Apply mesh repair operations before boolean operations

## 5. Geometric Transformations - Linear Algebra

### Transformation Matrices

All geometric transformations use homogeneous coordinates for consistency.

### Translation Matrix
```
T(tx, ty, tz) = [1  0  0  tx]
                [0  1  0  ty]
                [0  0  1  tz]
                [0  0  0  1 ]
```

### Scaling Matrix
```
S(sx, sy, sz) = [sx 0  0  0]
                [0  sy 0  0]
                [0  0  sz 0]
                [0  0  0  1]
```

### Rotation Matrix (around Z-axis)
```
Rz(θ) = [cos(θ) -sin(θ) 0 0]
        [sin(θ)  cos(θ) 0 0]
        [0       0      1 0]
        [0       0      0 1]
```

### Composite Transformations
```
M = T · R · S  (applied right to left)
```

## 6. Roof Slope Calculations - Trigonometry

### Slope-Height Relationship

For gabled roofs, the relationship between slope percentage and height:

```
height = base_length × tan(θ)
where θ = atan(slope_percent / 100)
```

### Default Parameters

- **Standard slope**: 22% ≈ 12.4° angle
- **Base length**: Half the width of minimum bounding box
- **Ridge height calculation**:
  ```python
  def calculate_roof_height(base_length, slope_percent=22):
      return (slope_percent / 100.0) * base_length
  ```

### Geometric Constraints

1. **Ridge positioning**: Ridge line positioned at centroid of minimum bounding box
2. **Edge alignment**: Roof edges aligned with building footprint
3. **Height validation**: Ensure roof height is physically reasonable

## References and Further Reading

1. **Straight Skeletons**:
   - Aichholzer, O., et al. (2011). A novel type of skeleton for polygons. *Journal of Universal Computer Science*, 1(12), 752-761.

2. **Computational Geometry**:
   - de Berg, M., et al. (2008). *Computational Geometry: Algorithms and Applications*. Springer.

3. **Boolean Operations**:
   - Hoffmann, C. M. (1989). *Geometric and Solid Modeling*. Morgan Kaufmann.

4. **Point Cloud Processing**:
   - Vosselman, G., & Maas, H. G. (2010). *Airborne and terrestrial laser scanning*. CRC Press.