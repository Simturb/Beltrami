import FreeCAD as App
import FreeCADGui as Gui
import Beltrami 

class coldStart():
    def GetResources(self):
        return {'Pixmap'  : App.getUserAppDataDir()+"Mod" + "/Beltrami/Resources/icons/coldStart.svg", # the name of a svg file available in the resources
                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Démarrage à froid d'un tracé - Cold start for a new blade",
                'ToolTip' : "Un nouveau tracé - A new blade"}
    
    def Activated(self):
        if (App.ActiveDocument==None):App.newDocument()
        param=App.ActiveDocument.getObject("Parametres")
        if param : 
            App.Console.PrintWarning("You can only work on one blade at a time in a model \n")
            return
        fp=App.ActiveDocument.addObject("App::FeaturePython","Parametres")
        docIU = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Interface_usager")
        docIU.addObject(fp)
        pM=Beltrami.beltrami(fp)
        return
        
Gui.addCommand('coldStart', coldStart()) 