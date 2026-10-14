import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT 
from .utility_functions.db import *
from .utility_functions.workers import *
from qgis.core import Qgis, QgsMessageLog
import traceback

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
)


def get_overpass_bbox():
    # Current visible map extent
    canvas = iface.mapCanvas()
    extent = canvas.extent()

    # Transform from the map canvas CRS to WGS 84
    source_crs = canvas.mapSettings().destinationCrs()
    target_crs = QgsCoordinateReferenceSystem("EPSG:4326")

    transform = QgsCoordinateTransform(
        source_crs,
        target_crs,
        QgsProject.instance().transformContext(),
    )

    extent_wgs84 = transform.transformBoundingBox(extent)

    # Overpass bbox order: south, west, north, east
    return (
        extent_wgs84.yMinimum(),
        extent_wgs84.xMinimum(),
        extent_wgs84.yMaximum(),
        extent_wgs84.xMaximum(),
    )
        
class WorkerOSMImport(QRunnable):

    def __init__(
        self,
        config,
        clearOldFeatures,
        filePath=None,
        plugin_dir=None,
        importType="both",
        bbox=None,
    ):
        super().__init__()

        self.config = config
        self.clearOldFeatures = clearOldFeatures
        self.filePath = filePath
        self.plugin_dir = plugin_dir

        # "buildings", "streets", or "both"
        self.importType = importType
        self.bbox = bbox

        self.signals = APISignals()

        # Retain your existing project configuration setup.
        self.srid = None
        
        self.OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter")
    
        self.signals.progress.emit(0)

    
    def build_overpass_query(
        self, south, west, north, east, feature_type
    ):
        bbox = f"({south},{west},{north},{east})"

        if feature_type == "buildings":
            selector = f'way["building"]{bbox};'
        elif feature_type == "streets":
            selector = f'way["highway"]{bbox};'
        else:
            raise ValueError(
                f"Unknown OSM feature type: {feature_type}"
            )

        return f"""
        [out:json][timeout:60];
        {selector}
        out body geom;
        """

    def download_osm(
        self, south, west, north, east,
        feature_type, retries=3
    ):
        query = self.build_overpass_query(
            south, west, north, east, feature_type
        )

        last_error = None

        for url in self.OVERPASS_URLS:
            for attempt in range(retries + 1):
                request = urllib.request.Request(
                    url,
                    data=urllib.parse.urlencode(
                        {"data": query}
                    ).encode("utf-8"),
                    headers={
                        "User-Agent": "DistrictsModeler",
                        "Accept": "application/json",
                    },
                    method="POST",
                )

                try:
                    with urllib.request.urlopen(
                        request, timeout=120
                    ) as response:
                        data = json.loads(
                            response.read().decode("utf-8")
                        )

                    elements = data.get("elements", [])

                    return elements

                except:
                    QgsMessageLog.logMessage(
                        traceback.format_exc(),
                        "Districts",
                        MessageInfo
                    )

                if attempt < retries:
                    time.sleep(2 ** (attempt + 1))

        raise RuntimeError(
            f"All Overpass endpoints failed for "
            f"{feature_type}. Last error: {last_error}"
        )

    def download_osm_features(self):
        south, west, north, east = self.bbox

        if self.importType not in (
            "buildings", "streets", "both"
        ):
            raise ValueError(
                "importType must be buildings, streets, or both"
            )

        result = {}

        if self.importType in ("buildings", "both"):
            result["buildings"] = self.download_osm(
                south, west, north, east, "buildings"
            )

        if self.importType in ("streets", "both"):
            result["streets"] = self.download_osm(
                south, west, north, east, "streets"
            )

        return result

    @staticmethod
    def way_to_wkt(element, polygon=False):
        coords = element.get("geometry", [])

        if len(coords) < (4 if polygon else 2):
            return None

        points = [
            (p["lon"], p["lat"])
            for p in coords
        ]

        if polygon and points[0] != points[-1]:
            return None

        coordinates = ",".join(
            f"{lon} {lat}" for lon, lat in points
        )

        if polygon:
            return f"POLYGON(({coordinates}))"

        return f"LINESTRING({coordinates})"

    def run(self):
        try:
            conn = None
            cur = None

            self.signals.progress.emit(1)

            # Use your plugin's existing DB functions.
            conn = dbConnect(self.config, True)
            cur = conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )

            # Use your existing configuration loader.
            # Adjust this unpacking to match your function's
            # actual return structure.
            project_config = loadProjectConfig(
                self.config
            )

            self.srid=project_config['srid']

            osm_data = self.download_osm_features()
            buildings = osm_data.get("buildings", [])
            streets = osm_data.get("streets", [])
            

            # Clear only the tables selected for import.
            if self.clearOldFeatures:
                if self.importType in ("buildings", "both"):
                    cur.execute(
                        f'TRUNCATE TABLE "{self.config['versionName']}".customers, '
                        f'"{self.config['versionName']}".buildings CASCADE'
                    )

                if self.importType in ("streets", "both"):
                    cur.execute(
                        f'TRUNCATE TABLE "{self.config['versionName']}".streets CASCADE'
                    )

            # ------------------------------------------------
            # BUILDINGS
            # ------------------------------------------------
            if self.importType in ("buildings", "both"):
                self.signals.progress.emit(10)
                max_seq=setSeqIdToMax('{}.buildings_id_seq'.format(self.config['versionName']),'{}.buildings'.format(self.config['versionName']),'id',cur)
                max_seq+= 0 if max_seq==1 else 1 
                max_id=1 if self.clearOldFeatures else getMaxTableValue(cur,self.config['versionName'],'buildings','b_id')+1
                sql=''
                
                for counter,element in enumerate(buildings,0):
                    wkt = self.way_to_wkt(
                        element, polygon=True
                    )
                    if not wkt:
                        continue

                    tags = element.get("tags", {})
                    osm_id = element["id"]

                    # Estimate building height from OSM tags.
                    height = tags.get("height")
                    if height is not None:
                        try:
                            height = float(
                                str(height).replace(" m", "")
                            )
                        except (TypeError, ValueError):
                            height = None

                    if height is None:
                        levels = tags.get("building:levels")
                        try:
                            height = (
                                float(levels) * 3.0
                                if levels is not None else 'NULL'
                            )
                        except (TypeError, ValueError):
                            height = 'NULL'


                    sql+='''INSERT INTO "{}".buildings (id, geom, b_id, substation_id, z_id, submodel, z_bh_m, z_height_m)
VALUES (
    {},
    ST_Multi(ST_Transform(
        ST_GeomFromText('{}', 4326),
        {}
    )),
    {}, {}, 1, 1, 0, {}
);\n'''.format(self.config['versionName'],
        counter+max_seq,
        wkt,
        self.srid,
        counter+max_id, counter+max_id,
        height)

                    sql+='''INSERT INTO "{}".customers (id, template, geom)
VALUES (
    {}, 1,
    ST_Transform(
        ST_Force3D(
            ST_Centroid(
                ST_GeomFromText('{}', 4326)
            )
        ),
        {}
    )
);\n'''.format(self.config['versionName'],
        counter+max_id,
        wkt,
        self.srid)
                cur.execute(sql)

            # ------------------------------------------------
            # STREETS
            # ------------------------------------------------
            progress = 55 if self.importType=='both' else 5
            if self.importType in ("streets", "both"):
                self.signals.progress.emit(progress)
                sql=''
                for element in streets:
                    wkt = self.way_to_wkt(
                        element, polygon=False
                    )
                    if not wkt:
                        continue
                    sql+='''INSERT INTO "{}".streets (geom)
                        VALUES (
                            ST_Transform(
                                ST_GeomFromText('{}', 4326),
                                {}
                            )
                        );\n'''.format(self.config['versionName'],wkt, self.srid)
                cur.execute(sql)

            conn.commit()
            self.signals.progress.emit(100)
            self.signals.finished.emit('buildings and streets' if self.importType=='both' else self.importType)
        except:
            QgsMessageLog.logMessage(
                traceback.format_exc(),
                "Districts",
                MessageCritical
            )