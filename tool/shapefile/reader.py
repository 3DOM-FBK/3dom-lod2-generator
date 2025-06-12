import geopandas as gpd


### function: read_shapefile_polygons ###
def read_shapefile_polygons(shapefile_path):
    """
    Legge shapefile e restituisce:
    - lista di tuple (exterior, holes)
    - offset (x_offset, y_offset)
    
    Le coordinate vengono normalizzate sottraendo l'offset.
    """
    gdf = gpd.read_file(shapefile_path)
    polygons = []
    
    # Calcolo bounding box globale del dataset per offset
    total_bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    x_offset, y_offset = total_bounds[0], total_bounds[1]
    
    for geom in gdf.geometry:
        if geom.geom_type == 'Polygon':
            exterior = [(x - x_offset, y - y_offset) for x, y in geom.exterior.coords]
            holes = [[(x - x_offset, y - y_offset) for x, y in interior.coords] for interior in geom.interiors]
            polygons.append((exterior, holes))
        elif geom.geom_type == 'MultiPolygon':
            for poly in geom.geoms:
                exterior = [(x - x_offset, y - y_offset) for x, y in poly.exterior.coords]
                holes = [[(x - x_offset, y - y_offset) for x, y in interior.coords] for interior in poly.interiors]
                polygons.append((exterior, holes))
    
    return polygons, (x_offset, y_offset)