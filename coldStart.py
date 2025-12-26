# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD as App
import FreeCADGui as Gui
import Beltrami 
translate=App.Qt.translate 

def QT_TRANSLATE_NOOP(context, text):
    return text
        
class coldStart():

    def GetResources(self):
        return {'Pixmap'  : App.getUserAppDataDir()+"Mod" + "/Beltrami/Resources/icons/coldStart.svg", # the name of a svg file available in the resources
                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': QT_TRANSLATE_NOOP("coldStart","Cold start for a new blade"),
                'ToolTip' : QT_TRANSLATE_NOOP("coldStart","A new blade")}
    
    def Activated(self):
        if (App.ActiveDocument==None):App.newDocument()
        param=App.ActiveDocument.getObject("Parametres")
        if param : 
            App.Console.PrintWarning(translate("coldStart","You can only work on one blade at a time in a model \n"))
            return
        fp=App.ActiveDocument.addObject("App::FeaturePython","Parametres")
        docIU = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Interface_usager")
        docIU.addObject(fp)
        pM=Beltrami.beltrami(fp)
        App.ActiveDocument.recompute()
        return
        
Gui.addCommand('coldStart', coldStart()) 