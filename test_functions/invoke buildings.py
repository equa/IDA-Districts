from plugins.utility_functions.db import *


plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'test00013', 'versionName' : 'base1'}

#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

sql="""SELECT 
  (ST_XMax(ST_Extent(geom))-ST_XMin(ST_Extent(geom)))/2 + ST_XMin(ST_Extent(geom)) AS x_center, 
  (ST_YMax(ST_Extent(geom))-ST_YMin(ST_Extent(geom)))/2 + ST_YMin(ST_Extent(geom)) AS y_center
FROM {}.buildings;""".format(dictDB['versionName'])
cur.execute(sql)
center=cur.fetchone()
print(center)

sql="""SELECT id,b_id,z_id,ST_AsText(geom) AS geom,z_vexp_m,z_bh_m FROM {}.buildings;""".format(dictDB['versionName'])
print(sql)
cur.execute(sql)

ida_script=''
for zone in cur.fetchall():
    print(zone)
    wkt_string=zone['geom']
    
    # Regular expression to match coordinates in the format (x y)
    pattern = r"(\d+\.\d+ \d+\.\d+)"

    # Find all the coordinates
    coordinates = re.findall(pattern, wkt_string)
    print(coordinates)

    corners = []
    for coordinate in coordinates:
        # Split each coordinate pair and adjust with the center
        x, y = coordinate.split(' ')
        corners.append((round(float(x) - center['x_center'],2), round(float(y) - center['y_center'],2)))

    # Format the corners with brackets but no commas between coordinates
    corners_str = f"({') ('.join([f'{x} {y}' for x, y in corners[:-1]])})"
    print(corners_str)
    
    ida_script+="""(make-building-from-qgis [@] "Zone_{}_{}" {} {} {} #2A({}))\n""".format(
        zone['b_id'],zone['z_id'],zone['z_bh_m'],zone['z_vexp_m'],str(len(corners)-1),corners_str)

print(ida_script)