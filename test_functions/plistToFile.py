comp=[{':C': 'MODEL', ':N': '"PMT2mux_1_1_1_1"', ':T': 'PMT2\\m\\u\\x'}, 
        {':C': ':VAR', ':N': '|P_var|', ':V': '100000'}, 
        {':C': ':VAR', ':N': '|M_var|', ':V': '-0.04553'}, 
        {':C': ':VAR', ':N': '|T_var|', ':V': '70.0'}, 
        [{':C': 'CONNECTOR', ':N': '|term_a|'},
            {':C': ':VAR', ':N': '|inStream(T)|', ':V': '70.0'}], 
        [{':C': 'CONNECTOR', ':N': '|term_b|'}, 
            {':C': ':VAR', ':N': '|inStream(T)|', ':V': '70.0'}]]
            
# comp=[{':C': 'OUTPUT-FILE', ':N': '"DH"', ':T': 'OUTPUT-FILE', ':DF': ['DIAGRAM-FIELD', ':SUBFIELDS', [['X-AXIS-WIDGET', ':AT', [['62', '328'], ['629', '364']]], ['Y-AXIS-WIDGET', ':AT', [['4', '17'], ['76', '324']]], ['LEGEND-WIDGET', ':AT', [['20', '384'], ['644', '420']]]], ':AT', [['76', '52'], ['574', '318']], ':X', ':SLICE'], ':RP': 'T', ':COL': 'T', ':STM': '3916374755'}, 
#         {':C': ':VAR', ':N': 'P_SEQ', ':T': 'POWERCONS', ':D': '"P seq"', ':U': 'W', ':IV': 'NIL', ':B': '(1 "Flowmeter3" P)'}]

# comp={':C': 'CONNECTIONS', 
#         ':CONNS': [[['"HX_substation"', '|TbSet|'], ['"tbout_setpoint"', 'OUTSIGNALLINK'], '0', '0', 'NIL'], 
#                     [['"PMT2mux2"', '|term_b|'], ['"HX_substation"', '|liqBIn|'], '0', '0', 'NIL'], 
#                     [['"PMT2mux3"', '|term_b|'], ['"HX_substation"', '|liqBOut|'], '0', '0', 'NIL'], 
#                     [['"Lm_H_G_L_Nohs"', '|TSetH|'], ['"Const6"', 'LINK'], '0', '0', 'NIL'], 
#                     [['"Lm_H_G_L_Nohs"', '|HCMode|'], ['"Const5"', 'LINK'], '0', '0', 'NIL'], 
#                     [['"Lm_H_G_L_Nohs"', '|Electricity_m2|'], ['"Const4"', 'LINK'], '0', '0', 'NIL'], 
#                     [['"Lm_H_G_L_Nohs"', '|Occupancy_m2|'], ['"Const4"', 'LINK'], '0', '0', 'NIL'], 
#                     [['"PMT2mux4"', '|term_b|'], ['"Lm_H_G_L_Nohs"', '|liq2|'], '0', '0', 'NIL'], 
#                     [['"PMT2mux5"', '|term_b|'], ['"Lm_H_G_L_Nohs"', '|liq1|'], '0', '0', 'NIL'], 
#                     [['"PUMP"', 'PUMPCTR'], ['"Const8"', 'LINK'], '0', '0', 'NIL'], 
#                     [['"PUMP"', 'OUTLET'], ['"PMT2mux5"', '|term_a|'], '0', '0', 'NIL'], 
#                     [['"PUMP"', 'INLET'], ['"PMT2mux3"', '|term_a|'], '0', '0', 'NIL'], 
#                     [['"ExpVess2"', ['|term|', '2']], ['"PMT2mux4"', '|term_a|'], '0', '0', 'NIL'], 
#                     [['"ExpVess2"', ['|term|', '1']], ['"PMT2mux2"', '|term_a|'], '0', '0', 'NIL'], 
#                     [['"Flowmeter3"', ['TRET_LINK', '1']], ['"PMT2mux2"', 'T'], '0', '2', 'NIL'], 
#                     [['"Flowmeter3"', ['FLOW_RET_LINK', '1']], ['"PMT2mux2"', 'M'], '0', '2', 'NIL'], 
#                     [['"Flowmeter3"', ['TSUP_LINK', '1']], ['"PMT2mux3"', 'T'], '0', '2', 'NIL'], 
#                     [['"Flowmeter3"', ['FLOW_SUP_LINK', '1']], ['"PMT2mux3"', 'M'], '0', '2', 'NIL'], 
#                     [['"PMT2mux_1_1_1_2_T30"', '|term_b|'], '"1_1_1_2_T30"', '0', '0', 'NIL'], 
#                     [['"PMT2mux_1_1_1_2_T30"', '|term_a|'], ['"HX_substation"', '|liqAOut|'], '0', '0', 'NIL'], 
#                     [['"PMT2mux_1_1_1_1_T70"', '|term_b|'], '"1_1_1_1_T70"', '0', '0', 'NIL'], 
#                     [['"PMT2mux_1_1_1_1_T70"', '|term_a|'], ['"HX_substation"', '|liqAIn|'], '0', '0', 'NIL']]}

def listToBracketsString(A):
    r = ''
    i=0
    for item in A:
        if isinstance(item,list): 
            r+= ('(' if i==0 else ' ')+listToBracketsString(item)+(')' if i==len(A)-1 else '')
        else: 
            r+=('(' if i==0 else ' ') +item+(')' if i==len(A)-1 else '')
        i+=1
    return r
    
def pListToCompString(pList,level):
    r = ''
    i=0
    if type(pList)==dict:
        if pList[':C']=='CONNECTIONS':
            return '(CONNECTIONS {})'.format(''.join(['\n '+listToBracketsString(conn) for conn in pList[':CONNS']]))
    for item in pList:
        if isinstance(item,list): 
            r+= ('(' if i==0 else '\n'+''.join([" " for j in range(level+1)]))+pListToCompString(item,level+1)+(')' if i==len(pList)-1 else '')
        elif isinstance(item,dict):
            r+= ('(' if i==0 else '\n'+''.join([" " for j in range(level+1)]))+pListToCompString(item,level+1)+(')' if i==len(pList)-1 else '')
        else:
            if isinstance(pList[item],list):
                value=listToBracketsString(pList[item])
            else:
                value=pList[item]
            if item[0]==':':
                r+=('(' if i==0 else ' ') +('' if i==0 else item+' ')+value+(')' if i==len(pList)-1 else '')
            else:
                r+=('(' if i==0 else ' ') +item+(')' if i==len(pList)-1 else '')
        i+=1
    return r.rstrip()
    
print(comp)


           
print(pListToCompString(comp,0))

print(len(dict))
#for i in dict:
#    print(i)
#    print(dict[i])
