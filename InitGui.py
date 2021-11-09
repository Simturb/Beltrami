import FreeCAD

class BeltramiWB (Workbench):
    def __init__(self):
        self.__class__.Icon=FreeCAD.getUserAppDataDir()+"Mod"+"/Beltrami/Resources/icons/Beltrami_workbench_icon.svg"
        self.__class__.MenuText="Beltrami"
        self.__class__.ToolTip="Tracé d'un aubage 3D"
        return

    def Initialize(self):
        import coldStart
        import modif
        self.list = ["coldStart","modif"]
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