import ifcopenshell
import ifcopenshell.geom
import geopandas as gpd
from shapely.geometry import Polygon
import shapely
import os

# Initialize IFC geometry settings
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)

output_file = "C:\\Users\\Administrator\\Desktop\\Peter\\Hellerhöfe\\ifc\\FSN-light_v4.ifc"


# Load IFC file
ifc_file = ifcopenshell.open("C:\\Users\\Administrator\\Desktop\\Peter\\Hellerhöfe\\ifc\\FSN-light_v4_abstractBIM.ifc")

# Find all spaces
spaces = ifc_file.by_type("IfcSpace")

# Lists to hold geometries and attributes
polygons = []
floor_levels = []
heights = []

# Set your georeferencing offset
x_offset = 487865.0
y_offset = 5551930.0

# ... [same IFC loading and loop setup] ...

for space in spaces:
    try:
        shape = ifcopenshell.geom.create_shape(settings, space)
        verts = shape.geometry.verts
        faces = shape.geometry.faces

        vertices = [verts[i:i+3] for i in range(0, len(verts), 3)]

        floor_z = min(v[2] for v in vertices)
        ceiling_z = max(v[2] for v in vertices)
        height = ceiling_z - floor_z

        # Apply offset and get floor points
        floor_points = [
            (v[0] + x_offset, v[1] + y_offset)
            for v in vertices if abs(v[2] - floor_z) < 0.01
        ]

        if len(floor_points) < 3:
            continue

        # Create convex hull polygon
        floor_ring = shapely.geometry.MultiPoint(floor_points).convex_hull

        polygons.append(floor_ring)
        floor_levels.append(round(floor_z, 3))
        heights.append(round(height, 3))

    except Exception as e:
        #print(f"Skipping space {space.GlobalId} due to error: {e}")

# Create GeoDataFrame with EPSG:25832
gdf = gpd.GeoDataFrame({
    'floor_level_m': floor_levels,
    'room_height_m': heights,
    'geometry': polygons
}, crs="EPSG:25832")

# Save to Shapefile
output_path = "C:\\Users\\Administrator\\Desktop\\Peter\\Hellerhöfe\\shp\\spaces_floor_polygons_v2.shp"
gdf.to_file(output_path)

#print(f"Shapefile written to: {output_path}")
