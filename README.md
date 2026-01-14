# 3DOM LOD2 Generator

This repository contains an automated pipeline for generating 3D models in **LOD2** (Level of Detail 2) format from building footprints in **Shapefile** format and point clouds in **LAS** format.

The pipeline uses **Blender** as a procedural 3D modeling engine, integrating geometric and spatial analysis to accurately reconstruct various roof typologies.

---

## 🚀 Pipeline Logic

The pipeline follows a workflow structured into several phases:

1.  **Input Data Loading**:
    *   Extraction of 2D geometries (polygons) from the shapefile.
    *   Parsing of associated attributes (e.g., roof type, building ID).
    *   Loading of the corresponding LAS point cloud for altimetric analysis.

2.  **Preprocessing and Spatial Analysis**:
    *   Bounding Box calculation for each building.
    *   Analysis of the LAS point cloud to determine the terrain elevation ($Z_{min}$) and the eave/ridge height ($Z_{max}$).
    *   Coordinate normalization for processing in Blender (applying a global offset).

3.  **Procedural 3D Generation**:
    *   Creation of the building's base volume (extrusion).
    *   Generation of the roof based on the specified typology (Flat, Gabled, Hip, etc.).
    *   Beveling and mesh cleanup.

4.  **Export and Georeferencing**:
    *   Exporting the mesh in PLY or OBJ format.
    *   Restoration of the original coordinates via inverse translation (Global Shift) to ensure correct spatial alignment in GIS environments.

---

## 📂 Project Structure (`tool/`)

The core logic is contained within the `tool/` directory:

*   `main.py`: Main entry-point that orchestrates Blender execution in headless mode.
*   `blender_main.py`: Python script executed inside Blender that manages the modeling lifecycle.
*   **`modeling/`**:
    *   `blender_ops.py`: Low-level mesh operations (cleanup, transformations, bevel).
    *   `pointcloud_ops.py`: LAS point cloud management and filtering for height extraction.
    *   **`roofs/`**: Specific scripts for each roof typology (`flat`, `gabled`, `hip`, `pyramid`, `gabled_L`).
*   **`shapefile/`**: Modules for reading `.shp` files and converting them into polygons ready for Blender.
*   **`io_utils/`**: Utilities for importing, exporting, and geographic positioning management.
*   **`cpp/`**: C++ modules (e.g., `skeleton.cpp`) for advanced geometric calculations like the Straight Skeleton.

---

## 🛠️ Usage

You can start the pipeline using the following command:

```bash
python tool/main.py -i <shapefile_path> -o <output_folder> --las <las_path> [options]
```

### Arguments:
- `-i, --input_shapefile`: Path to the .shp file containing building polygons.
- `-o, --output_folder`: Folder where the generated models will be saved.
- `--las`: Path to the .las file for height calculation.
- `-r, --round_edges`: (Optional) Applies beveling to the roof edges.
- `--export_format`: Output format (`ply` or `obj`, default: `ply`).

---

## 🏠 Supported Roof Typologies

The generator currently supports the following roof shapes:
- **Flat**: Flat roof.
- **Gabled**: Gabled roof (two slopes).
- **Gabled-L**: Gabled roof for L-shaped buildings.
- **Hip**: Hip roof (four slopes).
- **Pyramid**: Pyramid roof.

*In case of failure during the generation of a complex roof, the pipeline includes an automatic fallback to the **Flat** version to ensure process continuity.*
