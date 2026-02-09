from .files import *

def switchDebugMode(debug,plugin_dir):
    if debug:
        #debug mode
        replace_in_folder(
            root_folder=plugin_dir,
            old_string='#print(',
            new_string='print(',
            file_extensions=['.py'],
            exclude_filenames=['automated_testing.py','switchPluginMode.py','switch_debug_mode.py']
        )
    else:
        #mode without prints
        replace_in_folder(
            root_folder=plugin_dir,
            old_string='print(',
            new_string='#print(',
            file_extensions=['.py'],
            exclude_filenames=['automated_testing.py','switchPluginMode.py','switch_debug_mode.py']
        )