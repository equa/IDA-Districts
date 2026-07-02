#upgrade functions in order to use "old" projects within newer versions of the Districts Modeler

from .utility_functions.db import *

#upgrade versions DB table structure
def upgradeVersionDB(cur,config):
    #check if network has columns liq_type, t_freeze and t_ref
    #print('--upgrade--')
    table_info=getDBColumnInfo(cur,config['versionName'],'network')
    #print(table_info)
    if not 'liq_type' in table_info:
        sql="""ALTER TABLE "{}".network ADD COLUMN liq_type integer DEFAULT 1;\n""".format(config['versionName'])
        cur.execute(sql)
    if not 't_freeze' in table_info:
        sql="""ALTER TABLE "{}".network ADD COLUMN t_freeze numeric DEFAULT 1;\n""".format(config['versionName'])
        cur.execute(sql)
    if not 't_ref' in table_info:
        sql="""ALTER TABLE "{}".network ADD COLUMN t_ref numeric DEFAULT 60;\n""".format(config['versionName'])
        cur.execute(sql)
    #print('--upgrade finished--')
    
    