(defun insert-district-distr (building b-ids &aux (plant (component building 'plant)) distr to-zone to-ahu)
   (for mode in '(heat cold) and mode-name in '("heat" "cold") and template in '(esbo-adv-heat-distr esbo-adv-cold-distr) do
     (setf distr (esbo-insert-adv-distr (find-view-pane plant 'form t) (find-template template plant) mode 'esbo-const-distr))
     (setf to-zone (component distr 'to-zone))
     (setf to-ahu (component distr 'to-ahu))
     (delete-component (component to-zone mode-name))
     (delete-component (component to-ahu mode-name))
     (for i in b-ids do
       (make-component to-zone `(layer :t ,(name (find-template 'esbo-const-distr to-zone)) :n ,(concatenate 'string mode-name (write-to-string i))))
       (make-component to-ahu `(layer :t ,(name (find-template 'esbo-const-distr to-zone)) :n ,(concatenate 'string mode-name (write-to-string i)))))))

(defun set-zone-constructions (zone construction-plist)
   (for wall in (ice-zone-enclosing-surfaces zone :roof) do
     (set-wall-construction wall construction-plist t)))
   
(defun set-wall-construction (wall construction-plist &optional (walls t))
   (let* ((slope (get-value wall '(geometry slope)))
          ext int grd)
      (cond
         ((< slope ice-min_wall_slope)
           (setq ext :external_floors int :internal_floors grd :ground_floors))
         ((> slope ice-max_wall_slope)
           (setq ext :roof int :internal_floors grd :ground_floors))
         (walls
           (setq ext :external_walls int :internal_walls grd :ground_walls))
         (t
           (return-from set-wall-construction)))
      (set-value wall 'construction_external (getf construction-plist ext))
      (set-value wall 'construction_internal (getf construction-plist int))
      (set-value wall 'construction_ground (getf construction-plist grd))))

(defun make-zone-from-qgis (building name floor_height_from_ground ceiling-height ncorn corners &aux zone)
   (setf zone (make-component building `(ce-zone :n ,name :t zone)))
   (set-value building  `(,name geometry floor_height_from_ground) 200) ; in order not to insect with other zones
   (set-value building  `(,name geometry origin) #(0 0))
   (set-value building  `(,name geometry ncorn) ncorn)
   (set-value building  `(,name geometry orientation) 0)
   (enclose_zone zone)
   (set-value building  `(,name geometry corners) corners)
   (set-value building  `(,name geometry ceiling-height) ceiling-height)
   (set-value building  `(,name geometry floor_height_from_ground) floor_height_from_ground)
   (zone-to-bsection zone)
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
          ))))