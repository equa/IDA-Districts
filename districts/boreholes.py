"""
generate_boreholes.py

Reads boreholes from PostGIS and generates symmetric/mirrored/rotated points
based on mir=True reference points.

Output:
    List of dicts:
    [
        {"id": ..., "x": ..., "y": ..., "z": ..., "group": ..., "mir": ...},
        ...
    ]
"""

import math
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2.extras
import numpy as np
from .utility_functions.db import *


# ---------------------------
# Geometry helpers
# ---------------------------

def translate_point(point, center):        
    return float(point[0] - center[0]), float(point[1] - center[1])


def rotate(point, center, theta):
    p = np.array(point, dtype=float)
    c = np.array(center, dtype=float)

    R = np.array([
        [math.cos(theta), -math.sin(theta)],
        [math.sin(theta),  math.cos(theta)]
    ])

    return c + R @ (p - c)


# ---------------------------
# DB read
# ---------------------------

def fetch_points(cur, plant_id,config):
    sql="""SELECT id,
               ST_X(geom) AS x,
               ST_Y(geom) AS y,
               ST_Z(geom) AS z,
               "group",
               mir
    FROM "{}".boreholes
    WHERE plant_id = {}
    ORDER BY id;""".format(config['versionName'],plant_id) # nosec B608
    cur.execute(sql)
    rows = cur.fetchall()
    return rows


# ---------------------------
# Core logic
# ---------------------------

def getTransformedBoreholeInfo(cur,plant_id,config):
    result = []

    points = fetch_points(cur, plant_id,config)

    mir_points = [p for p in points if p['mir']]
    base_points = [p for p in points if not p['mir']]  # keep ALL original points
    #print("BASE POINTS:", base_points)
    #print("MIRROR POINTS:", mir_points)

    # -------------------
    # CASE 0 MIR POINTS (Gravity Center Translation)
    # -------------------
    if len(mir_points) == 0:
        #print('CASE 0 MIR POINTS')
        if not base_points:
            return result

        # Calculate the geometric centroid (mean of all X and Y coordinates)
        avg_x = sum(p['x'] for p in base_points) / len(base_points)
        avg_y = sum(p['y'] for p in base_points) / len(base_points)
        gravity_center = (avg_x, avg_y)
        #print("Gravity Center:", gravity_center)

        # Shift all points relative to the gravity center
        for p in base_points:
            tp = translate_point((p['x'], p['y']), gravity_center)
            result.append({
                "id": p['id'],
                "x": float(tp[0]),
                "y": float(tp[1]),
                "z": p['z'],
                "group": p['group'],
                "mir": 0  # 0 -> no mirror points available
            })

        return result

    # -------------------
    # CASE 2 MIR POINTS
    # -------------------
    if len(mir_points) == 2:
        #print('CASE 2 MIR POINTS')

        p1, p2 = mir_points
        a = (p1['x'], p1['y'])
        b = (p2['x'], p2['y'])

        # Transformation point is exactly the midpoint between the two mirror points
        center = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

        # Rotation to align the line AB with the X-axis
        theta = math.atan2(b[1] - a[1], b[0] - a[0])
        
        for p in base_points:
            # Rotate the system parallel to the X-axis
            rp = rotate((p['x'], p['y']), center, -theta)

            # Translate the origin to the center point (0, 0)
            tp = translate_point(rp, center)
            
            # The raw tp[1] is the signed local Y distance from the line.
            # Rotiert nach -theta gilt: links der Linie ist tp[1] > 0, rechts ist tp[1] < 0.
            # To neglect points on the left, we only keep points on the right (tp[1] <= 0) or on the line (tp[1] == 0).
            # Including a tiny floating point epsilon tolerance keeps points exactly on the line safe.
            if tp[1] <= 1e-9:
                final_x = float(tp[0])
                final_y = max(0.0, abs(float(tp[1])))  # Mirrored to the positive side as requested

                result.append({
                    "id": p['id'],
                    "x": final_x,
                    "y": final_y,
                    "z": p['z'],
                    "group": p['group'],
                    "mir": 1  # 1 -> 2 mirror points available
                })

        return result


    # -------------------
    # CASE 3 MIR POINTS
    # -------------------
    if len(mir_points) == 3:
        #print('CASE 3 MIR POINTS')
        p1, p2, p3 = mir_points

        # Vectors originating from the shared vertex p2 
        v1 = np.array([p1['x'] - p2['x'], p1['y'] - p2['y']]) # Direction p2 -> p1
        v2 = np.array([p3['x'] - p2['x'], p3['y'] - p2['y']]) # Direction p2 -> p3

        # Determine the absolute angle of both vectors
        ang_v1 = math.atan2(v1[1], v1[0])
        ang_v2 = math.atan2(v2[1], v2[0])

        # Exact angle from v1 to v2 COUNTER-CLOCKWISE
        ang_rad = (ang_v2 - ang_v1) % (2 * math.pi)
        ang = math.degrees(ang_rad)
        #print("Counter-clockwise angle between edges:", ang)

        center = (p2['x'], p2['y'])

        if 40 <= ang <= 50:
            step = math.radians(45)
            mir_status = 3  # 3 -> 3 mirror points with a 45° angle
        elif 85 <= ang <= 95:
            step = math.radians(90)
            mir_status = 2  # 2 -> 3 mirror points with a 90° angle
        else:
            raise ValueError(f"Unsupported angle: {ang}")

        # Epsilon tolerance for floating-point safety on the sector boundaries
        epsilon = 1e-9

        # Using ang_v1 (angle of v1) as our virtual zero-line for counter-clockwise checks
        for p in base_points:
            #print(p)
            
            #check if point is on the center
            dx = p['x'] - center[0]
            dy = p['y'] - center[1]
            dist = math.hypot(dx, dy)
            
            if dist <= epsilon:
                #print('keep (center vertex)')
                result.append({
                    "id": p['id'],
                    "x": 0.0,
                    "y": 0.0,
                    "z": p['z'],
                    "group": p['group'],
                    "mir": mir_status
                })
                continue # Nächsten Punkt verarbeiten, Winkelberechnung überspringen

            # Calculate the global angle of the current borehole relative to the center
            ang_p = math.atan2(p['y'] - center[1], p['x'] - center[0])
            
            # Relative angle of the borehole starting from line v1 (counter-clockwise)
            rel_ang = (ang_p - ang_v1) % (2 * math.pi)

            # Check if the point falls inside the valid sector slice (0 to step)
            # Inclusive bounds with epsilon to keep points exactly on both border lines
            if (0 - epsilon) <= rel_ang <= (step + epsilon):
                #print('keep')
                # Project the point into the first quadrant via polar coordinates
                dx = p['x'] - center[0]
                dy = p['y'] - center[1]
                dist = math.hypot(dx, dy)

                # Compute local coordinates based on the relative sector angle
                # This guarantees that all valid points end up in the first quadrant (X>0, Y>0)
                final_x = max(0.0, dist * math.cos(rel_ang))
                final_y = max(0.0, dist * math.sin(rel_ang))

                result.append({
                    "id": p['id'],
                    "x": float(final_x),
                    "y": float(final_y),
                    "z": p['z'],
                    "group": p['group'],
                    "mir": mir_status
                })

        return result


    return False
