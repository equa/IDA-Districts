#upgrade functions in order to use "old" projects within newer versions of the Districts Modeler

from .utility_functions.db import getDBColumnInfo, ensureMaterialMechanicalColumns, ensurePipeSeriesTables, ensurePipeTwinColumns
from .ai.access import ensureAiSettingsTable
from .utility_functions.debug_log import dprint
from .utility_functions.economic_data import dropBundleCostColumns, ensureEconomicTables, ensurePipeCostColumns
from .utility_functions.statics_db import ensureStaticsParameters, ensureStaticsTables

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
    #surface class of the streets (trench cost curves of the economic scenarios)
    if getDBColumnInfo(cur,config['versionName'],'streets') and 'surface' not in getDBColumnInfo(cur,config['versionName'],'streets'):
        cur.execute("""ALTER TABLE "{}".streets ADD COLUMN surface text;""".format(config['versionName'])) # nosec B608
    #statics model and its overrides (pipe statics)
    ensureStaticsTables(cur,config['versionName'])
    upgradeProjectDB(cur)
    dprint('--upgrade finished--')

#upgrade project DB table structure (schema public)
def upgradeProjectDB(cur):
    #mechanical properties of the materials (pipe statics)
    ensureMaterialMechanicalColumns(cur)
    #series and twin pipe casing of the pipes
    ensurePipeTwinColumns(cur)
    #product data of the series and the bend radius of the pipes (pipe statics)
    ensurePipeSeriesTables(cur)
    #parameters of the statics model
    ensureStaticsParameters(cur)
    #costs: maintenance, lifetime, p_max of the pipes and the economic scenarios
    ensurePipeCostColumns(cur)
    ensureEconomicTables(cur)
    #costs of the pipe bundles: never used
    dropBundleCostColumns(cur)
    #permission of the AI assistant (off until allowed)
    ensureAiSettingsTable(cur)
    
    