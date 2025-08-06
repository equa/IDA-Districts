from plugins.utility_functions.files import *

#modes: debug & release

def switchPluginMode(mode):
    if mode=='debug':
        #debug mode
        replace_in_folder(
            root_folder=plugin_dir,
            old_string='#print(',
            new_string='print(',
            file_extensions=['.py'],
            exclude_filenames=['automated_testing.py']
        )
    elif mode =='release':
        #mode without prints
        replace_in_folder(
            root_folder=plugin_dir,
            old_string='print(',
            new_string='#print(',
            file_extensions=['.py'],
            exclude_filenames=['automated_testing.py']
        )
        
switchPluginMode("release")
print('--finished--')