import FreeCAD as App
import FreeCADGui as Gui
import Beltrami 

class coldStart():
    def GetResources(self):
        return {'Pixmap'  : App.getUserAppDataDir()+"Mod" + "/Beltrami/Resources/Icons/coldStart.svg", # the name of a svg file available in the resources
                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Démarrage à froid d'un tracé - Cold start for a new blade",
                'ToolTip' : "Un nouveau tracé - A new blade"}
    
    def Activated(self):
        if (App.ActiveDocument==None):App.newDocument()
        param=App.ActiveDocument.getObject("Parametres")
        if param : 
            print("On ne peut travailler que sur une aube à la fois dans un modèle.")
            return
        fp=App.ActiveDocument.addObject("App::FeaturePython","Parametres")
        pM=Beltrami.beltrami(fp)
        return
        
Gui.addCommand('coldStart', coldStart()) 