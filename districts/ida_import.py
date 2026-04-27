from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsField,QgsProject
from qgis.PyQt.QtCore import QVariant
from .utility_functions.dialog import *
from .utility_functions.topology import *
from .utility_functions.db import *
import math
import copy

def checkInputBundleEditorInput(mappedAttributesValues):
    #check input data pipe
    if not mappedAttributesValues['Pipe inner diameter, m']:
        iface.messageBar().pushMessage("Error", "Please enter a pipe diameter!", level=Qgis.Warning)
        return False
    else:
        if not isFloat(mappedAttributesValues['Pipe inner diameter, m']):
            iface.messageBar().pushMessage("Error", "Pipe diameter is not a number!", level=Qgis.Warning)
            return False
    if not mappedAttributesValues['Roughness, m']:
        iface.messageBar().pushMessage("Error", "Please enter a pipe roughness factor!", level=Qgis.Warning)
        return False
    else:
        if not isFloat(mappedAttributesValues['Roughness, m']):
            iface.messageBar().pushMessage("Error", "Pipe roughness is not a number!", level=Qgis.Warning)
            return False
    
    #check input pipe bundle
    if not mappedAttributesValues['Number of parallel pipes']:
        iface.messageBar().pushMessage("Error", "Please enter a number of parallel pipes!", level=Qgis.Warning)
        return False
    else:
        if not isInt(mappedAttributesValues['Number of parallel pipes']):
            iface.messageBar().pushMessage("Error", "Number of parallel pipes is not an integer number!", level=Qgis.Warning)
            return False
    if not mappedAttributesValues['Horizontal distance, m']:
        iface.messageBar().pushMessage("Error", "Please enter a distance between pipes!", level=Qgis.Warning)
        return False
    else:
        if not isFloat(mappedAttributesValues['Horizontal distance, m']):
            iface.messageBar().pushMessage("Error", "Distance between pipes is not a number!", level=Qgis.Warning)
            return False
    if not mappedAttributesValues['Depth, m']:
        iface.messageBar().pushMessage("Error", "Please enter a depth below ground!", level=Qgis.Warning)
        return False
    else:
        if not isFloat(mappedAttributesValues['Depth, m']):
            iface.messageBar().pushMessage("Error", "Depth below ground is not a number!", level=Qgis.Warning)
            return False   
    
    return True
        
def generatePipebundleTyps(dlg_importNetworkTopologyFromLayer,dlg,layer,main):
    #print(dlg.mappedAttributes)
    sql=""
    main.cur=main.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    pipes_dict={} #{str([innder diameter, roughness, {sequence: [material, thickness]}]): pipe_id}
    pipes=[] #[innder diameter, roughness, {sequence: [material, thickness]}]
    constr={}
    pipe_constrs=[] #{sequence: [material, thickness]}
    pipe_constrs_dict={} #{pipe_construction_id: {sequence: [material, thickness]}}
    pipe_bundles=[] #[pipe_id, numb_pipe,distance,depth,ambient]
    pipe_bundles_dict={} #{str([pipe_id, numb_pipe,distance,depth,ambient]): bundle_id}
                
    if dlg.rbtn_extend.isChecked():
        #get all pipes from DB
        sql="""WITH  sub AS(        
    SELECT pl.pipe_construction_id, pl.sequence,pl.materialid||':'||m.name AS constr, pl.thickness 
        FROM pipe_layers pl, materials m
        WHERE pl.materialid=m.id
)
SELECT  p.id::text, p.innerpipediameter::text, p.piperoughnessfactor::text, sub.sequence, sub.thickness::text, sub.constr 
    FROM sub, pipes p
    WHERE sub.pipe_construction_id=p.pipe_construction_id
    ORDER BY p.id, sub.sequence DESC;"""
        #print(sql)
        main.cur.execute(sql)
        constr_layers=main.cur.fetchall()
        for constr_layer in constr_layers:
            #print(constr_layer)
            constr={constr_layer['sequence']:[constr_layer['constr'],constr_layer['thickness']]}|constr #add to begining of dict
            if constr_layer['sequence']==1:
                pipes.append([constr_layer['innerpipediameter'],constr_layer['piperoughnessfactor'],constr])
                pipes_dict[str([constr_layer['innerpipediameter'],constr_layer['piperoughnessfactor'],constr])]=constr_layer['id']
                constr={}
                
        #get all pipes constructions from DB
        sql="""SELECT pl.pipe_construction_id, pl.sequence, pl.materialid||':'||m.name AS name, pl.thickness::text 
    FROM pipe_layers pl, materials m 
    WHERE m.id=pl.materialid
    ORDER BY pl.pipe_construction_id, pl.sequence DESC;"""
        #print(sql)
        main.cur.execute(sql)
        constr_layers=main.cur.fetchall()

        constr={}
        for constr_layer in constr_layers:
            #print(constr_layer)
            constr={constr_layer['sequence']:[constr_layer['name'],constr_layer['thickness']]}|constr #add to begining of dict
            if constr_layer['sequence']==1:
                pipe_constrs.append(constr)
                pipe_constrs_dict[str(constr)]= str(constr_layer['pipe_construction_id']) 
                constr={}
        #print(pipe_constrs)
        #print(pipe_constrs_dict)
        
        #get all pipe bundle types from DB
        sql="""SELECT sequence, pipe_id::text, x, y, ambient::text, pipe_bundle_type_id::text FROM bundle_pipes ORDER BY pipe_bundle_type_id, sequence DESC;"""
        #print(sql)
        main.cur.execute(sql)
        exclude=False
        pipe_counter=0
        coord_list=[]
        for bundle_pipe in main.cur.fetchall():
            #print(bundle_pipe)
            coord_list.append([bundle_pipe['x'],bundle_pipe['y']])
            if pipe_counter!=0 and (y_old!=bundle_pipe['y'] or pipe_id_old!=bundle_pipe['pipe_id'] or ambient_old!=bundle_pipe['ambient']):
                exclude=True
            if bundle_pipe['sequence']==1:
                if exclude==False:
                    #check if distance is constant between pipes
                    dist_old=-1
                    for coord in coord_list:
                        dist=1000000
                        for coord2 in coord_list:
                            if coord2!=coord:
                                if math.sqrt((coord2[0]-coord[0])**2+(coord2[1]-coord[1])**2)<dist:
                                    dist=math.sqrt((coord2[0]-coord[0])**2+(coord2[1]-coord[1])**2)
                        if dist_old!=-1 and dist_old!=dist:
                            exclude=True
                        dist_old=dist
                    if exclude==False:
                        pipe_bundles.append([bundle_pipe['pipe_id'],str(pipe_counter+1),str(dist_old),str(bundle_pipe['y']),bundle_pipe['ambient']])
                        pipe_bundles_dict[str([bundle_pipe['pipe_id'],str(pipe_counter+1),str(dist_old),str(bundle_pipe['y']),bundle_pipe['ambient']])]=bundle_pipe['pipe_bundle_type_id']
                    else:
                        exclude=False
                else:
                    exclude=False
                coord_list=[]
                pipe_counter=0
            else:
                pipe_counter+=1
            ambient_old=bundle_pipe['ambient']
            y_old=bundle_pipe['y']
            pipe_id_old=bundle_pipe['pipe_id']
            sql=""
    else:
        sql="""TRUNCATE pipe_bundle_types CASCADE;
TRUNCATE pipe_constructions CASCADE;
TRUNCATE pipe_layers CASCADE;
TRUNCATE pipes CASCADE;
TRUNCATE bundle_pipes CASCADE;
TRUNCATE pipe_layers CASCADE;\n"""
        
    
    #Add field to layer if checkbox is checked
    if dlg.addPipeBundleTypeField.isChecked():
        #print('add field to layer')
        field_name=dlg.newFieldName.text()
        if field_name:
            #print(field_name)
            layer.startEditing()
            if field_name not in getLayerAttributesName(layer=layer):
                layer.dataProvider().addAttributes( [ QgsField(field_name, QVariant.Int)])
                # Update the attribute table
                layer.updateFields()                   
            bundle_idx=layer.fields().indexFromName(field_name)
        else:
            iface.messageBar().pushMessage("Error", "Please enter a field name!", level=Qgis.Warning)
            return False
    
    #loop over all features in layer
    # -- check if feature pipe parameters aready in list 
    pipes_max_id=getMaxIdSchema(main.cur,'pipes','public')
    pipe_bundles_max_id=getMaxIdSchema(main.cur,'pipe_bundle_types','public')
    bundle_pipes_max_id=getMaxIdSchema(main.cur,'bundle_pipes','public')
    constr_max_id=getMaxIdSchema(main.cur,'pipe_constructions','public')
    layer_max_id=getMaxIdSchema(main.cur,'pipe_layers','public')
    
    feature_count=layer.featureCount()
    main.dlg.update_progress(1)
    for index,feature in enumerate(layer.getFeatures()):
        main.dlg.update_progress(int(index/feature_count))
        mappedAttributesValues=copy.deepcopy(dlg.mappedAttributes) #make a copy in order to lose reference
        #print(feature)
        attributes=getLayerAttributesDict(feature,layer=layer)
        for mappedAttribute in dlg.mappedAttributes:
            if dlg.mappedAttributes[mappedAttribute]:              
                for attribute in attributes:
                    if attribute in dlg.mappedAttributes[mappedAttribute]:
                        mappedAttributesValues[mappedAttribute]=mappedAttributesValues[mappedAttribute].replace('"'+attribute+'"',str(attributes[attribute]))
                    if mappedAttribute=='layer_constr':
                        for layer_constr in [i for i in dlg.mappedAttributes[mappedAttribute]]:
                            if attribute in dlg.mappedAttributes[mappedAttribute][layer_constr][1]:
                                mappedAttributesValues[mappedAttribute][layer_constr][1]=mappedAttributesValues[mappedAttribute][layer_constr][1].replace('"'+attribute+'"',str(attributes[attribute]))
                for attribute in attributes:
                    if mappedAttribute=='layer_constr':
                        for layer_constr in mappedAttributesValues['layer_constr']:
                            try:
                                mappedAttributesValues['layer_constr'][layer_constr][1]=str(eval(mappedAttributesValues['layer_constr'][layer_constr][1]))
                            except:
                                pass
                    else:
                        try:
                            dict=strToDict(mappedAttributesValues[mappedAttribute].split('[')[0])
                            if dict:
                                mappedAttributesValues[mappedAttribute]=dict[mappedAttributesValues[mappedAttribute].split('}')[1].strip()[1:-1].replace('"','').replace("'",'')]
                            else:
                                mappedAttributesValues[mappedAttribute]=str(eval(mappedAttributesValues[mappedAttribute]))
                        except:
                            pass

        if not checkInputBundleEditorInput(mappedAttributesValues):
            return False
            
        constr={}
        for seq in range(0,dlg.tableWidget_pipe.rowCount()):
            #print(seq)
            constr[int(dlg.tableWidget_pipe.item(seq,0).text())]=[mappedAttributesValues['layer_constr'][str(seq+1)][0],mappedAttributesValues['layer_constr'][str(seq+1)][1]]
        feature_pipe=[mappedAttributesValues[dlg.pipe_bundle_type_attributes[0]],mappedAttributesValues[dlg.pipe_bundle_type_attributes[6]],constr]
            
        if constr not in pipe_constrs:
            #print('**********Add pipe construction*********')
            #print(constr)
            constr_max_id+=1
            #add to pipe layers
            for seq in constr:
                if not constr[seq][1]:
                    iface.messageBar().pushMessage("Warning", "Please enter a construction layer thickness!", level=Qgis.Warning)
                    return False
                layer_max_id+=1
                sql+="""INSERT INTO pipe_layers (id,pipe_construction_id,materialid,thickness,sequence) VALUES ({},{},{},{},{});\n""".format(
                    layer_max_id,constr_max_id,constr[seq][0].split(':')[0],constr[seq][1],seq)
            
            pipe_constrs.append(constr)
            pipe_constrs_dict[str(constr)]=constr_max_id
            
            #add to pipe constructions
            sql+="""INSERT INTO pipe_constructions (id,name) VALUES ({},'{}');\n""".format(
                constr_max_id,str(constr).replace("'",''))
             
        if feature_pipe not in pipes:
            #print('**********Add pipe*********')
            pipes_max_id+=1
            pipes.append(feature_pipe)
            pipes_dict[str(feature_pipe)]=str(pipes_max_id)
            #add pipe to DB
            sql+="""INSERT INTO pipes (id,name,innerpipediameter,piperoughnessfactor,pipe_construction_id) VALUES ({},'{}',{},{},{});\n""".format(
                pipes_max_id,str(feature_pipe).replace("'",''),mappedAttributesValues[dlg.pipe_bundle_type_attributes[0]],mappedAttributesValues[dlg.pipe_bundle_type_attributes[6]],pipe_constrs_dict[str(constr)])
            

        #print(pipes_dict)
        feature_bundle=[pipes_dict[str(feature_pipe)],mappedAttributesValues[dlg.pipe_bundle_type_attributes[4]],mappedAttributesValues[dlg.pipe_bundle_type_attributes[2]],mappedAttributesValues[dlg.pipe_bundle_type_attributes[3]],mappedAttributesValues[dlg.pipe_bundle_type_attributes[5]]]
        
        #print(feature_bundle)
        #print(pipe_bundles)
           
        if feature_bundle not in pipe_bundles:
            #print('*****--*****Add bundle*****---****')
            pipe_bundles.append(feature_bundle)
            pipe_bundles_max_id+=1
            pipe_bundles_dict[str(feature_bundle)]=str(pipe_bundles_max_id)
            #to add to DB
            #Add to pipe bundle types
            sql+="""INSERT INTO pipe_bundle_types (id,description) VALUES ({},'{} pipes: {} m depth; {} m distance');\n""".format(pipe_bundles_max_id,feature_bundle[1],feature_bundle[3],feature_bundle[2])
            
            #Add to bundle_pipes
            for seq in range(1,int(feature_bundle[1])+1):
                bundle_pipes_max_id+=1
                x=float(feature_bundle[2])*((2*seq-1-int(feature_bundle[1]))/2)
                sql+="""INSERT INTO bundle_pipes (id,pipe_bundle_type_id,sequence,pipe_id,x,y,ambient) VALUES ({},{},{},{},{},{},{});\n""".format(
                    bundle_pipes_max_id,pipe_bundles_max_id,seq,str(feature_bundle[0]),x,feature_bundle[3],feature_bundle[4])
        if dlg.addPipeBundleTypeField.isChecked():
            #print(pipe_bundles_dict)
            #print(feature.id())
            #print(pipe_bundles_dict[str(feature_bundle)])
            #print(bundle_idx)
            layer.changeAttributeValue(feature.id(), bundle_idx, pipe_bundles_dict[str(feature_bundle)])
    if dlg_importNetworkTopologyFromLayer:
        dlg_importNetworkTopologyFromLayer.listWidget_layerAttributes.addItem(field_name)
    
    #print(sql)
    main.cur.execute(sql)    
    layer.commitChanges()
    main.dlg.statusMessage.setText('Pipe bundle types are added to the DB!')
         
         
def getDHCLayerNameByType(type,dlg):
    """Get layer name by type"""
    if type=='line':
        layer_name='lines'
    else:
        if dlg.rbtn_plant.isChecked():
            layer_name='energy_plants'
        else:
            layer_name='customers'
    return layer_name
        
def setLayerListAttributes(signal,list,dlg):
    """Sets the layer attributes if combobox has changed"""
    list.clear()
    dlg.tableWidget.setRowCount(0)
    layer=QgsProject.instance().mapLayersByName(tr('@default',signal))
    if layer:
        layer=layer[0]
        #print(layer)
        attributes=layer.fields()
        attributes=[str(i.name()) for i in attributes]
        #print(attributes)
        list.addItems(attributes)
    
def getImportLayer(dlg):
    """Get import layer"""
    layer=QgsProject.instance().mapLayersByName(dlg.selectLayer.currentText())
    if layer:
        layer=layer[0]
    return layer
    
def getLayerAttributesDict(feature,layer=False,layerName=False):
    attributes={}
    if not layer:
        layer=QgsProject.instance().mapLayersByName(tr('@default',layerName))
        if layer:
            layer=layer[0]
    if layer:
        attributes=dict([(field.name(),feature[field.name()]) for field in layer.fields()])
    return attributes
        
def importLayerToDb(type,dlg,main):
    """Import the mapped layer into lines"""
    #print(type)
    main.dlg.update_progress(0)
    layer_name=getDHCLayerNameByType(type,dlg)
    #print(dlg.mappedAttributes)
    layer=QgsProject.instance().mapLayersByName(dlg.selectLayer.currentText())
    #print(layer)
    
    if main.conn:
        if main.config['versionName']:
            main.cur = main.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            if layer:
                main.dlg.update_progress(1)
                layer=layer[0]
                try:
                    layer_srid=layer.crs().authid().split(':')[1]            
                    #print(layer_srid)
                except:
                    iface.messageBar().pushMessage("Info", "Please set a valid layer srid!", level=Qgis.Warning)
                    return False

                generateId=False
                #attribute names
                attributes= [i for i in dlg.mappedAttributes if dlg.mappedAttributes[i]]
                #print(attributes)
                
                if dlg.rbtn_truncate.isChecked():
                    ids=[]
                    sql='TRUNCATE "{}".{};'.format(main.config['versionName'],layer_name)
                    main.cur.execute(sql)
                else:
                    sql='SELECT id FROM "{}".{};'.format(main.config['versionName'],layer_name)
                    main.cur.execute(sql)
                    ids=[i['id'] for i in main.cur.fetchall()]
                
                #check if id is mapped
                if not 'id' in attributes:
                    dlg_question = QMessageBox(dlg)
                    dlg_question.setWindowTitle('Identifier is missing!')
                    dlg_question.setText("""The id is not mapped in "{}". Do you want to use a serial id instead?""".format(layer_name))
                    dlg_question.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
                    dlg_question.setIcon(QMessageBox.Icon.Question)
                    button = dlg_question.exec()

                    if button == QMessageBox.StandardButton.Yes:
                        #print("Use serial id")
                        if dlg.rbtn_truncate.isChecked():
                            generateId=1
                        else:
                            generateId=getMaxIdSchema(main.cur,layer_name,main.config['versionName'])+1
                    else:
                        #print("Cancel!")
                        return False
                        
                sql=""
                i=0 
                attributes={}
                for feature in layer.getFeatures():
                    mappedAttributesValues=dlg.mappedAttributes.copy() #make a copy in order to lose reference
                    #print(mappedAttributesValues)
                    attributes=getLayerAttributesDict(feature,layer=layer)
                    for mappedAttribute in dlg.mappedAttributes:
                        if dlg.mappedAttributes[mappedAttribute]:
                            for attribute in attributes:
                                if attribute in dlg.mappedAttributes[mappedAttribute]:
                                    mappedAttributesValues[mappedAttribute]=mappedAttributesValues[mappedAttribute].replace('"'+attribute+'"',str(attributes[attribute]))
                    values=[]
                    #print(attributes)
                    attributes=[attribute for attribute in mappedAttributesValues if mappedAttributesValues[attribute]]
                    #print(mappedAttributesValues)
                    for attribute in attributes:
                        #print(attribute)
                        try:
                            values.append(str(eval(mappedAttributesValues[attribute])))
                        except:
                            pass

                    if type=='line':
                        values.append('ST_Transform(ST_SetSRID(ST_Force3D(ST_LineMerge(ST_GeomFromText(\''+str(feature.geometry().asWkt())+'\'))),'+layer_srid+'),'+ str(main.projectConfig['srid'])+')')
                    else:
                        values.append('ST_Transform(ST_SetSRID(ST_Force3D(ST_GeomFromText(\''+str(feature.geometry().asWkt())+'\')),'+layer_srid+'),'+ str(main.projectConfig['srid'])+')')
                    if generateId:
                        values.append(str(generateId+i))
                        sql+="""INSERT INTO "{}".{} ({}) VALUES ({});\n""".format(main.config['versionName'],layer_name,','.join(attributes+['geom','id']),','.join(values))
                    else:
                        if values[attributes.index('id')] in ids:
                            iface.messageBar().pushMessage("Error", "Id: {} occurs twice in layer: {}!".format(str(values[attributes.index('id')]),layer), level=Qgis.Warning)
                            return False
                        else:
                            ids.append(values[attributes.index('id')])
                        sql+="""INSERT INTO "{}".{} ({}) VALUES ({});\n""".format(main.config['versionName'],layer_name,','.join(attributes+['geom']),','.join(values))
                    i+=1
                #print(sql)
                main.cur.execute(sql)
                main.dlg.update_progress(100)
                main.dlg.statusMessage.setText(f'Import {type} layer compleded!')
                closeDialog(dlg)
            else:
                iface.messageBar().pushMessage("Info", "No Layer is selected!", level=Qgis.Info)
        else:
            iface.messageBar().pushMessage("Info", "No project version is loaded!", level=Qgis.Info)
    else:
        iface.messageBar().pushMessage("Info", "You are not connected to the DB!", level=Qgis.Info)
