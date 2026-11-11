#upgrade functions in order to use "old" projects within newer versions of the Districts Modeler

from .utility_functions.db import getDBColumnInfo, ensureMaterialMechanicalColumns, ensurePipeTwinColumns
from .utility_functions.debug_log import dprint

#upgrade versions DB table structure
def upgradeVersionDB(cur,config):
    #check if network has columns liq_type, t_freeze and t_ref
    dprint('--upgrade--')
    table_info=getDBColumnInfo(cur,config['versionName'],'network')
    dprint(table_info)
    if 'liq_type' not in table_info:
        sql="""ALTER TABLE "{}".network ADD COLUMN liq_type integer DEFAULT 1;\n""".format(config['versionName'])
        cur.execute(sql)
    if 't_freeze' not in table_info:
        sql="""ALTER TABLE "{}".network ADD COLUMN t_freeze numeric DEFAULT 1;\n""".format(config['versionName'])
        cur.execute(sql)
    if 't_ref' not in table_info:
        sql="""ALTER TABLE "{}".network ADD COLUMN t_ref numeric DEFAULT 60;\n""".format(config['versionName'])
        cur.execute(sql)
    upgradeProjectDB(cur)
    dprint('--upgrade finished--')

#upgrade project DB table structure (schema public)
def upgradeProjectDB(cur):
    #mechanical properties of the materials (pipe statics)
    ensureMaterialMechanicalColumns(cur)
    #series and twin pipe casing of the pipes
    ensurePipeTwinColumns(cur)
    
    