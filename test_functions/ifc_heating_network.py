# ifc_waermenetze_with_psets.py
import ifcopenshell
import ifcopenshell.geom
import geopandas as gpd
from shapely.geometry import LineString, Point
import numpy as np
import traceback

# -------------------------------------------------------------------
# Eingabe / Ausgabe anpassen
ifc_path = "C:\\EQUA\\Projekte\\KBP\\Versand Unterlagen\\Übersicht Anergienetz\\1179_00.XX_XXTGA_3D.XX_P.KBP_Infra.ifc"

out_gpkg = "C:\\EQUA\\Projekte\\KBP\\Versand Unterlagen\\Übersicht Anergienetz\\test5.gpkg"  # <-- anpassen
# -------------------------------------------------------------------

# IFC öffnen
ifc = ifcopenshell.open(ifc_path)

# Geometrie-Einstellungen
settings = ifcopenshell.geom.settings()
for key in ("use_world_coords", "use-world-coords"):
    try:
        settings.set(key, True)
    except Exception:
        pass
for key in ("context_identifiers", "context-identifiers"):
    try:
        settings.set(key, ["Axis", "Body"])
        break
    except Exception:
        pass

# -------------------------------------------------------------------
# Hilfsfunktionen
# -------------------------------------------------------------------

def extract_psets(ent):
    """
    Liefert ein dict mit allen PropertySets für ein IFC-Entity.
    Keys = 'PsetName.PropertyName'
    """
    psets = {}
    try:
        if hasattr(ent, "IsDefinedBy"):
            for rel in ent.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    prop_set = rel.RelatingPropertyDefinition
                    if prop_set.is_a("IfcPropertySet"):
                        pname = prop_set.Name
                        for p in prop_set.HasProperties:
                            if p.is_a("IfcPropertySingleValue"):
                                val = getattr(p.NominalValue, "wrappedValue", None)
                                key = f"{pname}.{p.Name}"
                                psets[key] = val
    except Exception:
        pass
    return psets

def verts_to_coords3(verts):
    if not verts:
        return None
    return np.array([(verts[i], verts[i+1], verts[i+2]) for i in range(0, len(verts), 3)], dtype=float)

def mesh_to_centerline(pts3, n_bins=40):
    if pts3.shape[0] < 2:
        return None
    centroid = pts3.mean(axis=0)
    cov = np.cov((pts3 - centroid).T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    main_axis = eigvecs[:, np.argmax(eigvals)]
    proj = (pts3 - centroid) @ main_axis
    if np.isclose(proj.min(), proj.max()):
        return None
    bins = np.linspace(proj.min(), proj.max(), min(n_bins, max(3, pts3.shape[0] // 5)))
    line_pts = []
    for i in range(len(bins)-1):
        mask = (proj >= bins[i]) & (proj < bins[i+1])
        if mask.sum() > 0:
            m = pts3[mask].mean(axis=0)
            line_pts.append((m[0], m[1]))
    if len(line_pts) >= 2:
        return LineString(line_pts)
    return None

def try_create_shape_line(entity):
    try:
        shp = ifcopenshell.geom.create_shape(settings, entity)
        verts = getattr(shp.geometry, "verts", None)
        coords3 = verts_to_coords3(verts)
        if coords3 is not None and coords3.shape[0] >= 2:
            return LineString([(p[0], p[1]) for p in coords3])
    except Exception:
        return None
    return None

# -------------------------------------------------------------------
# Pipes (IfcFlowSegment)
# -------------------------------------------------------------------
pipe_records = []
for seg in ifc.by_type("IfcFlowSegment"):
    try:
        line = try_create_shape_line(seg)
        if line is None:
            # Fallback: Mesh -> PCA
            shp = ifcopenshell.geom.create_shape(settings, seg)
            coords3 = verts_to_coords3(shp.geometry.verts)
            if coords3 is not None:
                line = mesh_to_centerline(coords3)
        if line is None:
            continue

        record = {
            "ifc_id": seg.id(),
            "name": getattr(seg, "Name", None),
            "type": seg.is_a(),
            "objecttype": getattr(seg, "ObjectType", None),
            "tag": getattr(seg, "Tag", None),
            "geometry": line
        }
        record.update(extract_psets(seg))
        pipe_records.append(record)
    except Exception:
        #print("⚠ Fehler bei Segment", seg.id(), getattr(seg, "Name", None))
        #print(traceback.format_exc())

# -------------------------------------------------------------------
# Nodes (Fittings, Controller, MovingDevices etc.)
# -------------------------------------------------------------------
node_records = []
for kind in ("IfcFlowFitting", "IfcFlowController", "IfcFlowMovingDevice"):
    for ent in ifc.by_type(kind):
        try:
            shp = ifcopenshell.geom.create_shape(settings, ent)
            coords3 = verts_to_coords3(shp.geometry.verts)
            if coords3 is None or coords3.shape[0] == 0:
                continue
            c = coords3.mean(axis=0)
            pt = Point(c[0], c[1])
            record = {
                "ifc_id": ent.id(),
                "name": getattr(ent, "Name", None),
                "type": ent.is_a(),
                "objecttype": getattr(ent, "ObjectType", None),
                "tag": getattr(ent, "Tag", None),
                "geometry": pt
            }
            record.update(extract_psets(ent))
            node_records.append(record)
        except Exception:
            #print("⚠ Fehler bei", kind, ent.id(), getattr(ent, "Name", None))

def make_unique_columns(columns):
    """
    Erzwingt eindeutige Spaltennamen, indem Duplikate mit Suffixen _1, _2, ... versehen werden.
    Entfernt zusätzlich führende/trailing Whitespaces.
    """
    seen = {}
    new_cols = []
    for col in columns:
        col = col.strip()   # Leerzeichen entfernen
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    return new_cols
    
# -------------------------------------------------------------------
# Export
# -------------------------------------------------------------------
if pipe_records:
    gdf_pipes = gpd.GeoDataFrame(pipe_records, geometry="geometry", crs=None)
    gdf_pipes.columns = make_unique_columns(gdf_pipes.columns)
    gdf_pipes.to_file(out_gpkg, layer="pipes", driver="GPKG")
    #print("✅ Pipes exportiert:", len(gdf_pipes))
else:
    #print("Keine Pipes exportiert.")

if node_records:
    gdf_nodes = gpd.GeoDataFrame(node_records, geometry="geometry", crs=None)
    gdf_nodes.columns = make_unique_columns(gdf_nodes.columns)
    gdf_nodes.to_file(out_gpkg, layer="nodes", driver="GPKG")
    #print("✅ Nodes exportiert:", len(gdf_nodes))
else:
    #print("Keine Nodes exportiert.")

#print("Fertig. Ergebnis:", out_gpkg)
