# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the Beltrami addon.

import FreeCAD
#translate=FreeCAD.Qt.Translate


class BeltramiWB (Workbench):
    def __init__(self):
        self.__class__.Icon=FreeCAD.getUserAppDataDir()+"Mod"+"/Beltrami/Resources/icons/Beltrami_workbench_icon.svg"
        self.__class__.MenuText="Beltrami"
#        self.__class__.ToolTip=translate("Beltrami","3D blade profile")
#        self.__class__.ToolTip="3D blade profile"
        return
 
    def Initialize(self):
        def QT_TRANSLATE_NOOP(context, text):
            return text
        import coldStart
        import modif
        FreeCADGui.addLanguagePath(":/translations")
        FreeCADGui.updateLocale()
        
        self.list = [QT_TRANSLATE_NOOP("Workbench","coldStart"),QT_TRANSLATE_NOOP("Workbench","modif")]
#        self.list = ["coldStart","modif"]
        self.appendToolbar("Beltrami Commands",self.list) # creates a new toolbar with your commands
        self.appendMenu("Beltrami",self.list) # creates a new menu

    def Activated(self):
        "This function is executed when the workbench is activated"
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        return

    def ContextMenu(self, recipient):
        "This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        self.appendContextMenu("My commands",self.list) # add commands to the context menu

    def GetClassName(self): 
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"
    
Gui.addWorkbench(BeltramiWB())