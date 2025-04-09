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


"""(defun make-building-from-qgis (building name floor_height_from_ground ceiling-height ncorn corners win-facade-ratio win-template &aux zone)
   (setf zone (make-component building `(ce-zone :n ,name :t zone)))
   (set-value building  `(,name geometry floor_height_from_ground) 200) ; in order not to insect with other zones
   (set-value building  `(,name geometry origin) #(0 0))
   (set-value building  `(,name geometry ncorn) ncorn)
   (enclose_zone zone)
   (set-value building  `(,name geometry corners) corners)
   (set-value building  `(,name geometry ceiling-height) ceiling-height)
   (set-value building  `(,name geometry floor_height_from_ground) floor_height_from_ground)
   (zone-to-bsection zone)
   (insert-win-by-ratio building win-facade-ratio :zones (list zone) :sia_380_1 T :win-template win-template)
   
   )


(defun apply-zone-template (building zone-name template-name modes &aux (zone (component building zone-name)) name template)
   (set-value zone 'zone-usage template-name)
   (setf template (pointed-resource (component zone 'zone-usage)))
   (ice-reset-to-zone-template zone template modes)
)
     

(defun merge-sections (building &key section-names &aux bsects)
   (setf bsects 
         (if section-names
            (print (for section in (:sections building) when (member (name section) section-names :test #'equal) collect section))
            (:sections building)))
   (let (poly newsect)
      (if (setf poly (merge-many-sections-g bsects))
         (with-logbook (act building `(:merge-sections ,@bsects))
           (if (Setf newsect (pset-to-section-in-building poly building :name (format nil "~a-merged" (name (car bsects)))))
              (progn
                (loop for sect in bsects do
                  (Del-Component building sect))
                (Log-message building :bb-merged (length bsects))
                (refresh-pane-and-others nil)
                )
              (Error-Message NIL :bb-merge-failed)))
         (Error-Message NIL :bb-merge-failed))))
         
(defun insert-win-by-ratio (system setpoint &key zones sia_380_1 intshad-model glass-res area-fraction u-value-frame slat-angle intshad-ctrl win-template 
                             &aux x-min x-max y-min y-max sides name-counter win (counter 0) f f-old offset dx offset-old (tolerance 0.0001) (max-steps 20) offset-points setpoint-decimal)
   "delete all windows and insert new windows on facade according to a window to facade ratio"
   (print zones)
   (unless zones
      (setf zones (:zones system)))
   
   ;;delete old windows
   (for win in (:windows system) when (member (:zone win) zones) do
     (delete-components win))
   
   ;;recalculate ambient surfaces areas without windows according to SIA 380-1
   (if sia_380_1
      (local-ch-sia380-1-set-area-values (:zones system) system))
   
   ;;insert scaled windows
   (for zone in (:zones system) when (member zone zones) do
     (print zone)
     (setf name-counter 0)
     (if (typep setpoint 'list)
        (setf setpoint-decimal (/ (cdr (assoc (name zone) setpoint :test #'equal)) 100))
        (setf setpoint-decimal (/ setpoint 100)))

     (when (and (> setpoint-decimal 0) (<= setpoint-decimal 1))
        (for cell in (apply 'append (slot-value zone 'ice-wall-sources)) when (and (equal (model-type (cnet-out cell)) 'wall-face)
                                                                                   (not (cnet-subcells cell))
                                                                                   (not (typep (cnet-in cell) 'wall-part)))
          do 
          (print cell)
          (setf counter 0)
          (setf offset 0.05)
          (setf offset-old 0)
          (setf offset-points '((0.0 0.0) (1.0 0.0) (1.0 1.0) (0.0 1.0)))
          (setf f (win-surface-ratio-error cell offset setpoint-decimal :sia_380_1 sia_380_1))
          (setf f-old (win-surface-ratio-error cell offset-old setpoint-decimal :sia_380_1 sia_380_1))
          (loop while (or (/= f f-old) 
                          (and
                               (< counter max-steps)
                               (> 0.000001 (xy-area offset-points)))) do 
            (setf dx (* f (/ (- offset offset-old) (- f f-old))))
            (if (< (abs dx) tolerance)
               (return))
            (setf offset-old offset)
            (setf offset (- offset dx))
            (multiple-value-setq (f offset-points) (win-surface-ratio-error cell offset setpoint-decimal :sia_380_1 sia_380_1))
            (setf f-old (win-surface-ratio-error cell offset-old setpoint-decimal))
            (incf counter 1))
          ;;check if window exceeds surface boundaries
          (if (> (xy-area offset-points) (cnet-net-area cell))
             (setf offset-points (cell-corners cell)))
          (setq x-min (apply 'min (mapcar 'first offset-points)))
          (setq x-max (apply 'max (mapcar 'first offset-points)))
          (setq y-min (apply 'min (mapcar 'second offset-points)))
          (setq y-max (apply 'max (mapcar 'second offset-points)))
          (setq offset-points (mapcar #'(lambda (coord)
                                (list (- (first coord) x-min) 
                                      (- (second coord) y-min)))
                              offset-points))
          (setf win (make-component (cnet-in cell) `((CE-WINDOW :N ,(concatenate-strings win-template (write-to-string name-counter)) :T ,win-template)
                                                     (:PAR :N X :V ,x-min)
                                                     (:PAR :N Y :V ,y-min)
                                                     (:PAR :N dx :V ,(- x-max x-min))
                                                     (:PAR :N dy :V ,(- y-max y-min))
                                                     ((AGGREGATE :N SHAPE :T SHAPE2D)
                                                      (:PAR :N NCORN :V ,(LENGTH offset-points))
                                                      (:PAR :N CORNERS :V ,(make-array (list (LENGTH offset-points) 2) :INITIAL-CONTENTS offset-points))))))
          (print win)
          (if glass-res
              (set-value win 'glazing (name glass-res)))
          (if area-fraction
              (set-value win '(frame area_fraction) area-fraction))
          (if u-value-frame
              (set-value win  '(frame u-value) u-value-frame))
          (if intshad-model
              (set-value win 'intshad-type 'OUTSIDE-BLIND))
          (if intshad-model
              (set-value win 'intshad-model (name intshad-model)))
          (if intshad-ctrl
              (set-value win 'internal_shading-control (name intshad-ctrl)))
          (if slat-angle
             (set-value system `(,(name intshad-model) slat_angle) slat-angle))
          (incf name-counter)
          ))))"""