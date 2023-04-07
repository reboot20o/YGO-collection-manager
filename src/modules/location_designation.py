# # Used to find the path to the file
# from pathlib import Path

import sys
import os


# def path(file):
#     """Method returns relative path to file in assets folder."""
#
#     path_to_db = Path(__file__).parent
#     relative_path = "../../assets/" + f"{file}"
#     return str((path_to_db / relative_path).resolve())

def asset_path(file):
    if getattr(sys, 'frozen', False):
        if sys.platform.startswith('win'):
            dir_path = os.path.join(os.environ['APPDATA'], 'YGOCollectionManager/assets')
        if not os.path.exists(dir_path):
            os.makedirs(os.path.join(dir_path, 'images'))
        return os.path.join(dir_path, file)
    else:
        return path(file)

def path(file):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    relative_path = f"assets/{file}"
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("../../")

    return os.path.join(base_path, relative_path)