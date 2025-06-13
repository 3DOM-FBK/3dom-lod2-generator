import geopandas as gpd


### function: read_shapefile_polygons ###
def read_shapefile_polygons(shapefile_path):
    """
    Legge shapefile e restituisce:
    - lista di dict con: { 'exterior': [...], 'holes': [...], 'roof': ..., 'height': ... }
    - offset (x_offset, y_offset)

    Le coordinate vengono normalizzate e viene gestita l'assenza della quota Z.
    """
    gdf = gpd.read_file(shapefile_path)
    polygons = []

    # Calcolo offset
    total_bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    x_offset, y_offset = total_bounds[0], total_bounds[1]

    for _, row in gdf.iterrows():
        geom = row.geometry

        def process_coords(coords):
            return [(x - x_offset, y - y_offset, z if len(coord) == 3 else 0)
                    for coord in coords
                    for x, y, *z_list in [coord]
                    for z in [(z_list[0] if z_list else 0)]]

        if geom.geom_type == 'Polygon':
            exterior = process_coords(geom.exterior.coords)
            holes = [process_coords(interior.coords) for interior in geom.interiors]
            polygons.append({
                'exterior': exterior,
                'holes': holes,
                'roof': row.get('roof', None),
                'height': row.get('height', None)
            })

        elif geom.geom_type == 'MultiPolygon':
            for poly in geom.geoms:
                exterior = process_coords(poly.exterior.coords)
                holes = [process_coords(interior.coords) for interior in poly.interiors]
                polygons.append({
                    'exterior': exterior,
                    'holes': holes,
                    'roof': row.get('roof', None),
                    'height': row.get('height', None)
                })

    return polygons, (x_offset, y_offset)