from plugins.utility_functions.files import *

#modes: debug & release

def switchDebugMode(debug,plugin_dir):
    if debug:
        #debug mode
        replace_in_folder(
            root_folder=plugin_dir,
            old_string='print(',
            new_string='print(',
            file_extensions=['.py'],
            exclude_filenames=['automated_testing.py','switchPluginMode.py']
        )
    else:
        #mode without prints
        replace_in_folder(
            root_folder=plugin_dir,
            old_string='print(',
            new_string='print(',
            file_extensions=['.py'],
            exclude_filenames=['automated_testing.py','switchPluginMode.py']
        )
        
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
        
switchDebugMode(True,plugin_dir)
print('--finished--')