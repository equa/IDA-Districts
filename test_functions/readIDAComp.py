seq=[['MODEL', ':N', '"PMT2mux_1_1_1_1_T70"', ':T', 'PMT2\\m\\u\\x'], 
        [':VAR', ':N', '|P_var|', ':V', '100000'], 
        [':VAR', ':N', '|M_var|', ':V', '-0.04553'], 
        [':VAR', ':N', '|T_var|', ':V', '70.0'], 
        [['CONNECTOR', ':N', '|term_a|'], [':VAR', ':N', '|inStream', ['T'], '|', ':V', '70.0']], 
        [['CONNECTOR', ':N', '|term_b|'], [':VAR', ':N', '|inStream', ['T'], '|', ':V', '70.0']]]

seq=[['MODEL', ':N', '"PMT2mux_1_1_1_1_T70"', ':T', 'PMT2\\m\\u\\x'], [':VAR', ':N', '|P_var|', ':V', '100000'], [':VAR', ':N', '|M_var|', ':V', '-0.04553'], [':VAR', ':N', '|T_var|', ':V', '70.0'], [['CONNECTOR', ':N', '|term_a|'], [':VAR', ':N', '|inStream', ['T'], '|', ':V', '70.0']], [['CONNECTOR', ':N', '|term_b|'], [':VAR', ':N', '|inStream', ['T'], '|', ':V', '70.0']]]        
def propertyListIDM(seq):
    #print(seq)
    i=0
    comp_list=[]
    dict={}
    while i<len(seq):
        #print(i)
        #print(seq[i])
        if type(seq[i])==list:
            #print('recursive call')
            comp_list.append(propertyListIDM(seq[i]))
            i+=1
        else:
            if i==0:
                dict[':C']=seq[0]
                i+=1
            if seq[i+1]=='|inStream':
                #print('inStream(T)')
                dict[seq[i]]='|inStream(T)|'
                i+=2
            else:
                try:
                    dict[seq[i]]=seq[i+1].asList()
                except:
                    dict[seq[i]]=seq[i+1]
            #print(dict)
            i+=2
        
    if comp_list:
        return comp_list
    else:
        return dict       
   
print(propertyListIDM(seq))