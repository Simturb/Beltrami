import FreeCAD as App
import FreeCADGui as Gui
import Beltrami 

class modif():
    def GetResources(self):
        return {'Pixmap'  : App.getUserAppDataDir()+"Mod" + "/Beltrami/Resources/Icons/modif.svg", # the name of a svg file available in the resources
                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Mettre à jour le tracé - Profile update",
                'ToolTip' : "Mise-à-jour - Update"}
    
    def Activated(self):
        fp=App.ActiveDocument.getObject("Parametres")
        if not fp : return
        pM=fp.Proxy
        pM.modif(fp)
        return
        
Gui.addCommand('modif', modif()) 