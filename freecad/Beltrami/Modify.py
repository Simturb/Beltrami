# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the Beltrami addon.

import FreeCAD as App
import FreeCADGui as Gui
import freecad.Beltrami as Beltrami
translate=App.Qt.translate 

def QT_TRANSLATE_NOOP(context, text):
    return text 

class modif():
    def GetResources(self):
        return {'Pixmap'  : App.getUserAppDataDir()+"Mod" + "/Beltrami/freecad/Beltrami/Resources/Icons/Modify.svg", # the name of a svg file available in the resources
                'Accel' : "Shift+U", # a default shortcut (optional)
                'MenuText': QT_TRANSLATE_NOOP("modif","Edited profile update"),
                'ToolTip' : QT_TRANSLATE_NOOP("modif","Update")}
    
    def Activated(self):
        if (App.ActiveDocument==None): 
            App.Console.PrintWarning(translate('modif','There is no existing profile to modify'))
            return
        fp=App.ActiveDocument.getObject("Parametres")
        if not fp : 
            print(translate('modif','Cold start must be activated first'))
            return
        pM=fp.Proxy
        pM.modif(fp)
        return
        
Gui.addCommand('modif', modif()) 