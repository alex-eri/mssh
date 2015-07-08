import os
import site
import sys
import glob
from cx_Freeze import setup, Executable

siteDir = site.getsitepackages()[1]
includeDllPath = os.path.join(siteDir, "gnome")

#missingDll = glob.glob(includeDllPath + "\\" + '*.dll')
missingDll = [dll.strip() for dll in open("dlls.txt").readlines()]


includeFiles = [("mssh.glade","mssh.glade")]

for DLL in missingDll:
    includeFiles.append((os.path.join(includeDllPath, DLL), DLL))
    # includeFiles.append(DLL)

# You can import all Gtk Runtime data from gtk folder
#gtkLibs= ['etc','lib','share']

# You can import only important Gtk Runtime data from gtk folder
gtkLibs = ['lib\\gdk-pixbuf-2.0',
           'lib\\girepository-1.0',
           'share\\glib-2.0',
           'lib\\gtk-3.0',
           'share\\icons',
           'share\\locale\\en',
           'share\\locale\\ru',
           'etc\\fonts'
           ]


for lib in gtkLibs:
    includeFiles.append((os.path.join(includeDllPath, lib), lib))

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name = "mssh",
    version = "1.0",
    description = "Multi Mikrotik SSH executor",
    options = {'build_exe' : {
        'compressed': True,
        'includes': ["gi"],
        'excludes': ['wx', 'email', 'pydoc_data', 'curses'],
        'packages': ["gi"],
        'include_files': includeFiles
    }},
    executables = [
        Executable("mssh.py",
                   base=base
                   )
    ]
)
