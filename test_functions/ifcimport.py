import ifcopenshell
import ifcopenshell.geom
import shapely.geometry
from shapely.ops import unary_union
import geopandas as gpd
import math
from shapely.affinity import translate

#file_shp="C:\\EQUA\\Projekte\\Hellerhöfe\\shp\\FZS-SPA-ARC-03-XXX-GE-23-GK-Bauherr Abgabe LPH3plus_abstractBIM.shp"
#file_ifc="C:\\EQUA\\Projekte\\Hellerhöfe\\ifc\\FZS-SPA-ARC-03-XXX-GE-23-GK-Bauherr Abgabe LPH3plus_abstractBIM.ifc"
#file_shp="C:\\EQUA\\Projekte\\Hellerhöfe\\shp\\FZN-KBN-ARC-03-XXX-GE-18-AB-ARC Modell_abstractBIM.shp"
#file_ifc="C:\\EQUA\\Projekte\\Hellerhöfe\\ifc\\FZN-KBN-ARC-03-XXX-GE-18-AB-ARC Modell_abstractBIM.ifc"
file_shp="C:\\EQUA\\Projekte\\Hellerhöfe\\shp\\FSS-SPA-ARC-03-GES-XX-18-AB-Freigabe LPH3 TGA_abstractBIM_v3.shp"
file_ifc="C:\\EQUA\\Projekte\\Hellerhöfe\\ifc\\FSS-SPA-ARC-03-GES-XX-18-AB-Freigabe LPH3 TGA_abstractBIM.ifc"
#file_shp="C:\\EQUA\\Projekte\\Hellerhöfe\\shp\\FSN-03A-ARC-03-GES-16-16-NK-FSN IFC Modell TGA.shp"
#file_ifc="C:\\EQUA\\Projekte\\Hellerhöfe\\ifc\\FSN-03A-ARC-03-GES-16-16-NK-FSN IFC Modell TGA.ifc"


def get_floor_elevation_from_object(obj):
    try:
        rel = next(r for r in obj.Decomposes if r.is_a("IfcRelAggregates"))
        storey = rel.RelatingObject
        return float(getattr(storey, "Elevation", 0.0))
    except Exception:
        return 0.0

def get_height_from_verts(verts):
    if not verts:
        return 0
    zs = [verts[i + 2] for i in range(0, len(verts), 3)]
    return max(zs) - min(zs) if zs else 0

def get_footprint_from_verts(verts):
    coords = [(verts[i], verts[i + 1], verts[i + 2]) for i in range(0, len(verts), 3)]
    if not coords:
        return None
    min_z = min(z for x, y, z in coords)
    floor_coords = [(x, y) for x, y, z in coords if math.isclose(z, min_z, abs_tol=0.01)]
    if len(floor_coords) > 2:
        poly = shapely.geometry.Polygon(floor_coords)
        return poly if poly.is_valid else None
    return None

def get_window_area(window):
    # Sum all IfcQuantityArea areas assigned to the window
    total_area = 0.0
    try:
        for rel in window.HasQuantities or []:
            for q in rel.Quantities or []:
                if q.is_a("IfcQuantityArea") and q.AreaValue:
                    total_area += q.AreaValue
    except Exception:
        pass
    return total_area

# Load IFC
ifc = ifcopenshell.open(file_ifc)
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)

# Filter spaces
exclude_keywords = ["ida ice building body", "dachterrasse", "mietbereich", "balkon","terrasse","loggia"]

def is_excluded_space(space):
    name = (space.Name or "").lower()
    longname = (getattr(space, "LongName", "") or "").lower()
    objtype = (getattr(space, "ObjectType", "") or "").lower()
    return any(keyword in name or keyword in longname or keyword in objtype for keyword in exclude_keywords)

# Filter spaces
exclude_keywords = ["ida ice building body", "dachterrasse", "mietbereich", "balkon","terrasse","loggia"]

def is_excluded_space(space):
    name = (space.Name or "").lower()
    longname = (getattr(space, "LongName", "") or "").lower()
    objtype = (getattr(space, "ObjectType", "") or "").lower()
    return any(keyword in name or keyword in longname or keyword in objtype for keyword in exclude_keywords)

spaces = [
    s for s in ifc.by_type("IfcSpace")
    if not is_excluded_space(s)
]

walls = ifc.by_type("IfcWallStandardCase")

floor_data = {}

# Process spaces: get footprint and group by floor elevation
for space in spaces:
    try:
        shape = ifcopenshell.geom.create_shape(settings, space)
        verts = shape.geometry.verts
        poly = get_footprint_from_verts(verts)
        if poly is None:
            continue
        height = get_height_from_verts(verts)
        floor_elev = get_floor_elevation_from_object(space)
        usage = getattr(space, "LongName", None) or getattr(space, "ObjectType", None) or space.Name or "Unknown"

        if floor_elev not in floor_data:
            floor_data[floor_elev] = {"geometry": [], "heights": [], "usages": []}

        floor_data[floor_elev]["geometry"].append(poly)
        floor_data[floor_elev]["heights"].append(height)
        floor_data[floor_elev]["usages"].append(usage)

    except Exception as e:
        print(f"⚠️ Skipping space {space.GlobalId}: {e}")
        continue

# Prepare floor elevations sorted ascending
floor_elevations = sorted(floor_data.keys())

# Process windows: calculate window areas and assign to floor level
window_areas_by_floor = {}
seen_window_positions = set()

for window in ifc.by_type("IfcWindow"):
    print(window)
    try:
        shape = ifcopenshell.geom.create_shape(settings, window)
        verts = shape.geometry.verts
        coords = [(verts[i], verts[i + 1], verts[i + 2]) for i in range(0, len(verts), 3)]
        if not coords:
            continue

        centroid_x = sum(x for x, y, z in coords) / len(coords)
        centroid_y = sum(y for x, y, z in coords) / len(coords)
        base_z = min(z for x, y, z in coords)

        # Use (X, Y, Z) rounded to 2 decimals to filter duplicates (allow vertical stacking)
        rounded_xyz = (round(centroid_x, 2), round(centroid_y, 2), round(base_z, 2))
        if rounded_xyz in seen_window_positions:
            continue
        seen_window_positions.add(rounded_xyz)

        # Get window area from quantities
        win_area = get_window_area(window)
        print(win_area)
        if win_area <= 0:
            continue

        # Assign window to the nearest floor level >= base_z
        possible_floors = [fe for fe in floor_elevations if fe >= base_z]
        if not possible_floors:
            # If no floor above, assign to highest floor below base_z
            possible_floors = [fe for fe in floor_elevations if fe <= base_z]
            if not possible_floors:
                # no floors at all? skip
                continue
        floor_level = min(possible_floors)

        # Add window area to that floor
        window_areas_by_floor.setdefault(floor_level, 0)
        window_areas_by_floor[floor_level] += win_area

        print(f"🪟 Window {window.GlobalId} (#{window.id()}), area={win_area:.3f}, assigned floor={floor_level}")

    except Exception as e:
        print(f"⚠️ Skipping window {getattr(window, 'GlobalId', 'UNKNOWN')} (#{window.id()}): {e}")
        continue

# Prepare GeoDataFrame records
records = []
geometries = []

# Offsets for Hellerhöfe approx location (50.1044°N, 8.6286°E) UTM zone 32N EPSG:25832
x_offset = 487865.0
y_offset = 5551930.0

for floor_elev, val in floor_data.items():
    if not val["geometry"]:
        continue
    geom_merged = unary_union(val["geometry"])
    if geom_merged.is_empty:
        continue

    avg_height = sum(val["heights"]) / len(val["heights"])
    perimeter = geom_merged.length
    # Surface area = perimeter * avg room height (for facade surface approx)
    surface_area = perimeter * avg_height

    window_area = window_areas_by_floor.get(floor_elev, 0)
    window_ratio = window_area / surface_area if surface_area > 0 else 0

    # Apply translation to Hellerhöfe location
    geom_translated = translate(geom_merged, xoff=x_offset, yoff=y_offset)

    records.append({
        "floor_level": round(floor_elev, 3),
        "room_height": round(avg_height, 3),
        "window_surface_ratio": round(window_ratio, 3),
        "usages": list(set(val["usages"])),
        "surface_area": round(surface_area, 3),
        "window_area": round(window_area, 3)
    })
    geometries.append(geom_translated)

gdf = gpd.GeoDataFrame(records, geometry=geometries, crs="EPSG:25832")
gdf.to_file(file_shp)

print("✅ Export complete: 'FZS-SPA-ARC-03-XXX-GE-23-GK-Bauherr Abgabe LPH3plus_abstractBIM.shp'")
