# -*- coding: utf-8 -*-

__title__ = "Beltrami"
__author__ = "Michel Sabourin (sabm01)"
__license__ = "https://michelsabourin.scenari-community.org/SimTurb/co/1siteWeb_1.html"
__doc__ = "https://michelsabourin.scenari-community.org/SimTurbMeth/co/GenerationProfil3D.html"

import os
import FreeCAD as App
import FreeCADGui as Gui 
import math, Sketcher, Part, Spreadsheet
import numpy as np
from freecad.Curves import IsoCurve as iso
from freecad.Curves import Discretize
from freecad.Curves import approximate
from freecad.Curves import _utils
#debug = _utils.debug
debug = _utils.doNothing

def get_module_path():
    """ Returns the current module path.
    Determines where this file is running from, so works regardless of whether
    the module is installed in the app's module directory or the user's app data folder.
    (The second overrides the first.)
    """
    return os.path.dirname(__file__)
    
TOOL_ICON = App.getUserAppDataDir()+"Mod" + "/Beltrami/Resources/Icons/coldStart.svg"

Gui.activateWorkbench("SketcherWorkbench")

class beltrami:
    def __init__(self, fp): # Ordre coldStart
        debug('Beltrami - init')
    #
    #   Création des listes pour sauvegarder l'information
    #
        fp.addProperty("App::PropertyString","Version","Base","Numéro de version").Version="1.0.6"
        fp.addProperty("App::PropertyInteger","Naubes","Base","Nombre d'aubes").Naubes=13
        fp.addProperty("App::PropertyIntegerConstraint","Nfilets","Base","Nombre de filets").Nfilets=(6,2,65,1)
        fp.addProperty("App::PropertyIntegerConstraint","preNfilets","Base","Nombre de filets précédents").preNfilets=0
        fp.addProperty("App::PropertyIntegerConstraint","Npts","Base","Nombre de points par filet").Npts=(9,9,1025,8)
        fp.addProperty("App::PropertyIntegerConstraint","Sens","Base","Rotation(1:anti-horaire, -1:horaire)").Sens=(-1,-1,1,2)
        fp.addProperty("App::PropertyBool","Modifiable","Base","Vrai pour modification").Modifiable=False
        fp.addProperty("App::PropertyBool","Init","Base","Vrai pour modification").Init=True
        fp.addProperty("App::PropertyInteger","Def_t","Base","Nombre de poles en t").Def_t=4
        fp.Proxy=self
        fp.setEditorMode("Version",1)
        fp.setEditorMode("Label",1)
        fp.setEditorMode("Modifiable",2)
        fp.setEditorMode("Init",2)
        fp.setEditorMode("Def_t",2)
        fp.setEditorMode("preNfilets",2)
    #   fp est le feature python nommé Parametres
    #   Création des sketchs de pilotages
        self.initPilote(fp)
    #   Traçage du plan méridien
        self.traceMeridien(fp)
    #   Traçage du plan des épaisseurs
        self.traceEpaisseur(fp)
    #   Traçage du plan de la cascade
        self.traceCascade(fp)
    #   Traçage de la géométrie 3D
        self.voile3D(fp)
        fp.preNfilets=fp.Nfilets
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
        return 
    def modif(self,fp):     # Ordre modif
        self.sauveTableur(fp)
        self.sauveEpaisseur(fp)
        self.sauveMeridien(fp)
        self.sauveCascade(fp)
        return
    def initPilote(self,fp):
        debug('initPilote')
        self.initTableur(fp)
    #   création et stokage des sketch de pilotage de la géométrie 
        docPilote = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Pilote")
        self.initCascade(fp)
        self.initEpaisseur(fp)
        self.initMeridien(fp)
        fp.Init=False
        App.ActiveDocument.recompute()
        debug('initPilote - fin')
        return
#
#
#       Routines système FreeCAD
#
#
    def onChanged(self, fp, prop):
        debug('onChanged propriété changée: '+prop)
        debug('Modifiable = '+str(fp.Modifiable))
        if fp.Init : return
        if (prop == "Init") : return
        if not fp.Modifiable :
            if('Up-to-date' in fp.State): 
                fp.Modifiable=True
                debug('Statut modifiable changé = '+str(fp.Modifiable))
        if not fp.Modifiable : return
        debug('Modifiable = '+str(fp.Modifiable))
        if (prop == "ExpressionEngine" or prop == "Proxy" or prop =="Visibility" or prop=="Label" or prop=="Shape" or prop=="Points" or prop=="Naubes"):
            debug('Avec ExpressionEngine,Proxy, Visibility, Label, Shape, Points: pas de calcul ')
            return
        if (prop == "Sens"):
            debug('Beltrami.onChanged '+prop)
            self.modifCascade(fp,fp.Nfilets) 
            self.modifVoile(fp)
            fp.recompute()
            debug('onChanged - fin')
            return
        if(prop == "Npts"):
            debug('Beltrami.onChanged Npts')
            debug(prop)
            self.onChangedNpts( fp)
            debug('Beltrami.onChanged Npts - fin')
            return
        if(prop == "Nfilets"):
            self.onChangedNfilets(fp)
            debug('onChanged - fin')
            return
        elif (prop == "Epaisseur"):
            debug('on est rendu à if prop ==Epaisseur')
            self.modifEpaisseur(fp)
            # self.modifCascade(fp)
            # self.modifVoile(fp)
            debug('onChanged - fin Epaisseur')
            return
        elif (prop == "Alpha"):
            debug('on est rendu à if prop == Alpha')
            self.modifCascade(fp, fp.Nfilets)
            self.modifVoile(fp)
        debug('onChanged - fin')
        return 
    def onChangedNpts(self, fp):
        for i in range(fp.Nfilets):
            I=str(i+1)
            debug('Pour le filet '+str(i))
            FiletMi=App.ActiveDocument.getObject("FiletM"+I)
            FiletMi.Number=fp.Npts
            FiletMi.recompute()
            debug('Filet méridien traité')
            fpe=App.ActiveDocument.getObject("LoiEpaisseur"+I+"e")
            fpe.Number=fp.Npts
            fpe.recompute()
            debug("LoiEpaisseur"+I+"e traité")
            fpi=App.ActiveDocument.getObject("LoiEpaisseur"+I+"i")
            fpi.Number=fp.Npts
            fpi.recompute()
            debug("LoiEpaisseur"+I+"i traité")
            fpes=App.ActiveDocument.getObject("LoiEpaisseur"+I+"es")
            fpes.Npts=fp.Npts
            fpes.recompute()
            debug("LoiEpaisseur"+I+"es traité")
            fpis=App.ActiveDocument.getObject("LoiEpaisseur"+I+"is")
            fpis.Npts=fp.Npts
            fpis.recompute()
            debug("LoiEpaisseur"+I+"is traité")
            Ts=App.ActiveDocument.getObject("Theta_sortie")
            Usmax=self.CascadeUsmax(i)
            sketchA=App.ActiveDocument.getObject('Cascade'+I)
            sketchA.setDatum(24,App.Units.Quantity(str(Usmax)))
            debug('Usmax= '+str(Usmax))
            fpAa=App.ActiveDocument.getObject("FiletCAa"+I)
            fpAa.a3=App.Vector(Usmax,fp.Sens*1000.*math.radians(Ts.Points[i].z),0)
            fpAa.Number=fp.Npts
            fpAa.recompute()
            debug("FiletCAa"+I+" traité")
            fpAs=App.ActiveDocument.getObject("FiletCAs"+I)
            fpAs.Npts=fp.Npts
            fpAs.recompute()
            debug("FiletCAs"+I+" traité")
            fpLa=App.ActiveDocument.getObject("FiletCLa"+I)
            fpLa.Npts=fp.Npts
            fpLa.recompute()
            debug("FiletCLa"+I+" traité")
            fpLe=App.ActiveDocument.getObject("FiletCLe"+I)
            fpLe.Npts=fp.Npts
            fpLe.recompute()
            debug("FiletCLe"+I+" traité")
            fpLi=App.ActiveDocument.getObject("FiletCLi"+I)
            fpLi.Npts=fp.Npts
            fpLi.recompute()
            debug("FiletCLi"+I+" traité")
            fpAe=App.ActiveDocument.getObject("FiletCAe"+I)
            fpAe.Npts=fp.Npts
            fpAe.recompute()
            debug("FiletCAe"+I+" traité")
            fpAi=App.ActiveDocument.getObject("FiletCAi"+I)
            fpAi.Npts=fp.Npts
            fpAi.recompute()
            debug("FiletCAi"+I+" traité")
            App.ActiveDocument.recompute()
        self.modifVoile(fp)
        return
    def onChangedNfilets(self, fp):
        Gui.Selection.clearSelection()
        debug('onChangedNfilets')
        if(fp.Nfilets ==fp.preNfilets):
            debug('onChangedNfilets - fin')
            return
    #   Plan méridien
        docPlanMeridien=App.ActiveDocument.getObject('Plan_Meridien')
        IsoCurve=App.ActiveDocument.getObject('IsoCurve')
        IsoCurve.NumberU=fp.Nfilets
        IsoCurve.recompute()
    #   Traitement du plan des épaisseurs
        EpMaxXEx = App.ActiveDocument.getObject( "EpMaxXEx") 
        EpMaxXEx.Number=fp.Nfilets
        EpMaxXEx.recompute()
        EpMaxXIn = App.ActiveDocument.getObject( "EpMaxXIn") 
        EpMaxXIn.Number=fp.Nfilets
        EpMaxXIn.recompute()
        EpMaxYEx = App.ActiveDocument.getObject( "EpMaxYEx") 
        EpMaxYEx.Number=fp.Nfilets
        EpMaxYEx.recompute()
        EpMaxYIn = App.ActiveDocument.getObject( "EpMaxYIn") 
        EpMaxYIn.Number=fp.Nfilets
        EpMaxYIn.recompute()
        EpInflexEx = App.ActiveDocument.getObject( "EpInflexEx") 
        EpInflexEx.Number=fp.Nfilets
        EpInflexEx.recompute()
        EpInflexIn = App.ActiveDocument.getObject( "EpInflexIn") 
        EpInflexIn.Number=fp.Nfilets
        EpInflexIn.recompute()
        EpLastEx = App.ActiveDocument.getObject( "EpLastEx") 
        EpLastEx.Number=fp.Nfilets
        EpLastEx.recompute()
        EpLastIn = App.ActiveDocument.getObject( "EpLastIn") 
        EpLastIn.Number=fp.Nfilets
        EpLastIn.recompute()
    #   pour les fonctions pilotes
        Te = App.ActiveDocument.getObject("Theta_entree")
        Te.Number = fp.Nfilets
        Te.recompute()
        Ts = App.ActiveDocument.getObject("Theta_sortie")
        Ts.Number = fp.Nfilets
        Ts.recompute()
        Ae = App.ActiveDocument.getObject("Alpha_entree")
        Ae.Number = fp.Nfilets
        Ae.recompute()
        As = App.ActiveDocument.getObject("Alpha_sortie")
        As.Number = fp.Nfilets
        As.recompute()
        We = App.ActiveDocument.getObject("Poids_entree")
        We.Number = fp.Nfilets
        We.recompute()
        Ws = App.ActiveDocument.getObject("Poids_sortie")
        Ws.Number = fp.Nfilets
        Ws.recompute()
        Le = App.ActiveDocument.getObject("Long_entree")
        Le.Number = fp.Nfilets
        Le.recompute()
        Ls = App.ActiveDocument.getObject("Long_sortie")
        Ls.Number = fp.Nfilets
        Ls.recompute()
    #
    #   pour fp.Nfilets > fp.preNfilets
    #
        if (fp.Nfilets > fp.preNfilets):
        #   Plan méridien
            for i in range (fp.preNfilets):
                I=str(i+1)
                debug(I)
                App.ActiveDocument.getObject("FiletM"+I).recompute()
            debug('fp.Nfilets= '+str(fp.Nfilets))
            for i in range(fp.preNfilets,fp.Nfilets):
                I=str(i+1)
                debug(I)
                fpM = App.ActiveDocument.addObject("Part::FeaturePython","FiletM"+I)
                docPlanMeridien.addObject(fpM)
                Discretize.Discretization(fpM, (App.ActiveDocument.getObject("IsoCurve"),"Edge"+I))
                fpM.Number=fp.Npts
                Discretize.ViewProviderDisc(fpM.ViewObject)
                fpM.ViewObject.PointSize = 3
                if fp.preNfilets > 0 :fpM.Visibility=App.ActiveDocument.getObject('FiletM'+str(i)).Visibility
                fpM.recompute()
            #   Plan épaisseurs
            self.sketchDiscEpaisseur(fp, EpMaxXEx, EpMaxXIn, EpMaxYEx, EpMaxYIn, EpInflexEx, EpInflexIn, EpLastEx, EpLastIn)
        #   Plans des longueurs et de la cascade
            self.sketchDiscCascade(fp, Te, Ts, Ae, As, We, Ws, Le, Ls)
        #   Voile 3D 
            self.modifVoile(fp)
    #
    #   pour Nfilets < preNfilets
    #
        else: 
            debug("pour Nfilets < preNfilets")
        #   plan méridien
            for i in range (fp.Nfilets):
                I=str(i+1)
                debug(I)
                App.ActiveDocument.getObject("FiletM"+I).recompute()
            for i in range (fp.Nfilets,fp.preNfilets):
                I=str(i+1)
                App.ActiveDocument.removeObject("FiletM"+I)
        #   plan des épaisseurs
            for i in range (fp.Nfilets):
                I=str(i+1)
                debug(I)
                App.ActiveDocument.getObject('LoiEpaisseur'+I+'e').recompute()
                App.ActiveDocument.getObject("LoiEpaisseur"+I+"es").recompute()
                App.ActiveDocument.getObject('LoiEpaisseur'+I+'i').recompute()
                App.ActiveDocument.getObject("LoiEpaisseur"+I+"is").recompute()
            for i in range (fp.Nfilets,fp.preNfilets):
                I=str(i+1)
                App.ActiveDocument.removeObject("skLoiEpaisseur"+I+"e")
                App.ActiveDocument.removeObject("LoiEpaisseur"+I+"e")
                App.ActiveDocument.removeObject("LoiEpaisseur"+I+"es")
                App.ActiveDocument.removeObject("skLoiEpaisseur"+I+"i")
                App.ActiveDocument.removeObject("LoiEpaisseur"+I+"i")
                App.ActiveDocument.removeObject("LoiEpaisseur"+I+"is")
        #   Plans des longueurs et de la cascade
            self.modifCascade(fp,fp.Nfilets)
            for i in range (fp.Nfilets,fp.preNfilets):
                I=str(i+1)
                App.ActiveDocument.removeObject("Cascade"+I)
                App.ActiveDocument.removeObject("FiletCAa"+I)
                App.ActiveDocument.removeObject("FiletCAs"+I)
                App.ActiveDocument.removeObject("FiletCAe"+I)
                App.ActiveDocument.removeObject("FiletCAi"+I)
                App.ActiveDocument.removeObject("FiletCLa"+I)
                App.ActiveDocument.removeObject("FiletCLe"+I)
                App.ActiveDocument.removeObject("FiletCLi"+I)
        #   Voile 3D
            for i in  range(fp.Nfilets):
                debug('Mise-à-jour des points des voiles existants')
                I=str(i+1)
                debug(I)
                fpVA = App.ActiveDocument.getObject('Voile3Da'+I)
                fpVE = App.ActiveDocument.getObject('Voile3De'+I)
                fpVI = App.ActiveDocument.getObject('Voile3Di'+I)
            #   Calcul des 3 voiles A, E, I      
                FiletMeridien=App.ActiveDocument.getObject('FiletM'+I)
                FiletM=FiletMeridien.Points
                FiletCascadeA=App.ActiveDocument.getObject('FiletCAs'+I)
                FiletCA=FiletCascadeA.Points
                FiletCascadeE=App.ActiveDocument.getObject('FiletCAe'+I)
                FiletCE=FiletCascadeE.Points
                FiletCascadeI=App.ActiveDocument.getObject('FiletCAi'+I)
                FiletCI=FiletCascadeI.Points
                debug('$$$$$$$$$Calcul des points du voile')
                debug(I)
                debug('FiletM= '+str(FiletM))
                debug('FiletCA= '+str(FiletCA))
                debug('FiletCI= '+str(FiletCI))
                debug('FiletCE= '+str(FiletCE))
                Voile3DDiscretization.calcul(fpVA, FiletM, FiletCA, fp.Npts)
                Voile3DDiscretization.calcul(fpVI, FiletM, FiletCI, fp.Npts)
                Voile3DDiscretization.calcul(fpVE, FiletM, FiletCE, fp.Npts)
                debug('fpVA')
                debug(fpVA.Points)
            for i in range (fp.Nfilets,fp.preNfilets):
                I=str(i+1)
                debug(I)
                App.ActiveDocument.removeObject("Voile3Da"+I)
                App.ActiveDocument.removeObject("Voile3De"+I)
                App.ActiveDocument.removeObject("Voile3Di"+I)
        debug('calcul des surfaces des voiles')
    #   Voile 3D
        docVoile3Da = App.ActiveDocument.getObject("Voile3Da")
        docVoile3De = App.ActiveDocument.getObject("Voile3De")
        docVoile3Di = App.ActiveDocument.getObject("Voile3Di")
        fpSA=App.ActiveDocument.getObject("Ame")
        fpSE=App.ActiveDocument.getObject("Extrados")
        fpSI=App.ActiveDocument.getObject("Intrados")
        debug(docVoile3Da.Content)
        fpSA.PointObject=docVoile3Da
#        fpSA.LastIndex=fp.Nfilets-1
        fpSE.PointObject=docVoile3De
#        fpSE.LastIndex=fp.Nfilets-1
        fpSI.PointObject=docVoile3Di
#        fpSI.LastIndex=fp.Nfilets-1
        App.activeDocument().recompute(None,True,True)
        fp.preNfilets=fp.Nfilets
        debug('onChangedNfilets - fin')
        return
    def __setstate__(self, state):
        debug('setstate')
        fp=App.ActiveDocument.getObject('Parametres')
        fp.Modifiable=False
        debug('Modifiable = '+str(fp.Modifiable))
        debug('setstate - fin')
        return 
#
#
#       Routines génériques
#
#       
    def immobilisePoint(self,sketch, Pt, nom): 
        #
        # fixe des contraintes au point
        # Pt: posision du point dans sketch.Geometry  
        # nom: chaîne de caractère pour identifier le point
        # 
        # 
        #Création du point de coin
        #
        pt=sketch.Geometry[Pt]
        sketch.toggleConstruction(Pt)
        Ddlx=sketch.addConstraint(Sketcher.Constraint('DistanceX',Pt,1,pt.X))
        sketch.renameConstraint(Ddlx,nom+'x')
        Ddly=sketch.addConstraint(Sketcher.Constraint('DistanceY',Pt,1,pt.Y))
        sketch.renameConstraint(Ddly,nom+'y')
        return(Ddlx,Ddly)
    def planBS(self,sketch,Pt0,Pt1,Pt2,Pt3):
    #
    #   Création d'une BSpline de degré 3 dans le plan méridien
    #   Chaque point est défini par sa géométrie dans le sketch à l'indice Vx
    #
    #   Coordonnées des extrémités
        Geo=sketch.Geometry
        v0=App.Vector(Geo[Pt0].X,Geo[Pt0].Y,0)
        v1=App.Vector(Geo[Pt1].X,Geo[Pt1].Y,0)
        v2=App.Vector(Geo[Pt2].X,Geo[Pt2].Y,0)
        v3=App.Vector(Geo[Pt3].X,Geo[Pt3].Y,0)
    #
    #   Le bspline
    #
        dx=Geo[Pt3].X-Geo[Pt0].X
        dy=Geo[Pt3].Y-Geo[Pt0].Y
    #   Poids local pour les pts de contrôle
        rayon=0.1*math.sqrt(dx*dx+dy*dy)
    #
        C1=sketch.addGeometry(Part.Circle(v0,App.Vector(0,0,1),rayon),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C1,3,Pt0,1))
        C2=sketch.addGeometry(Part.Circle(v1,App.Vector(0,0,1),rayon),True)
        sketch.addConstraint(Sketcher.Constraint('Radius',C1,rayon)) 
        sketch.addConstraint(Sketcher.Constraint('Equal',C1,C2))
        sketch.addConstraint(Sketcher.Constraint('Coincident',C2,3,Pt1,1)) 
        C3=sketch.addGeometry(Part.Circle(v2,App.Vector(0,0,1),rayon),True)
        sketch.addConstraint(Sketcher.Constraint('Equal',C1,C3)) 
        sketch.addConstraint(Sketcher.Constraint('Coincident',C3,3,Pt2,1))
        C4=sketch.addGeometry(Part.Circle(v3,App.Vector(0,0,1),rayon),True)
        sketch.addConstraint(Sketcher.Constraint('Equal',C1,C4)) 
        sketch.addConstraint(Sketcher.Constraint('Coincident',C4,3,Pt3,1)) 
        BS=sketch.addGeometry(Part.BSplineCurve([v0,v1,v2,v3],None,None,False,3,None,False),False)
        l1=Part.LineSegment(v0,v1)
        L1=sketch.addGeometry(l1,True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C1,3,L1,1))
        sketch.addConstraint(Sketcher.Constraint('Coincident',C2,3,L1,2))
        l2=Part.LineSegment(v2,v3)
        L2=sketch.addGeometry(l2,True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C3,3,L2,1))
        sketch.addConstraint(Sketcher.Constraint('Coincident',C4,3,L2,2))
        conList = []
        conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C1,3,BS,0))
        conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C2,3,BS,1))
        conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C3,3,BS,2))
        conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C4,3,BS,3))
        sketch.addConstraint(conList)
        sketch.exposeInternalGeometry(BS)
        sketch.recompute()
        return (BS,L1,L2)        
#
#
#       Routines tableur
#
#
    def initTableur(self,fp):
        Feuil=App.ActiveDocument.addObject('Spreadsheet::Sheet','Tableau_pilote')
        docIU=App.ActiveDocument.getObject("Interface_usager")
        docIU.addObject(Feuil)
        Feuil.set("A1", "Ordonnée t")
        Feuil.set("B1", "0.0")
        Feuil.set("C1", "0.3333333333")
        Feuil.set("D1", "0.6666666666")
        Feuil.set("E1", "1.0")
        Feuil.set("B2", "deg")
        Feuil.set("C2", "deg")
        Feuil.set("D2", "deg")
        Feuil.set("E2", "deg")
        Feuil.set("A3", "Theta_entree")
        Feuil.set("B3", "0.0")
        Feuil.set("C3", "-1.33")
        Feuil.set("D3", "-2.66")
        Feuil.set("E3", "-4.0")
        Feuil.set("A4", "Theta_sortie")
        Feuil.set("B4", "-30.0")
        Feuil.set("C4", "-40.0")
        Feuil.set("D4", "-50.0")
        Feuil.set("E4", "-60.0")
        Feuil.set("A5", "Alpha_entree")
        Feuil.set("B5", "-56.77")
        Feuil.set("C5", "-51.72")
        Feuil.set("D5", "-49.32")
        Feuil.set("E5", "-48.34")
        Feuil.set("A6", "Alpha_sortie")
        Feuil.set("B6", "-56.77")
        Feuil.set("C6", "-51.72")
        Feuil.set("D6", "-49.32")
        Feuil.set("E6", "-48.34")
        Feuil.set("B7", "mm")
        Feuil.set("C7", "mm")
        Feuil.set("D7", "mm")
        Feuil.set("E7", "mm")
        Feuil.set("A8", "Poids_entree")
        Feuil.set("B8", "100.0")
        Feuil.set("C8", "100.0")
        Feuil.set("D8", "100.0")
        Feuil.set("E8", "100.0")
        Feuil.set("A9", "Poids_sortie")
        Feuil.set("B9", "100.0")
        Feuil.set("C9", "100.0")
        Feuil.set("D9", "100.0")
        Feuil.set("E9", "100.0")
        Feuil.set("A10", "Long_entree")
        Feuil.set("B10", "208.67")
        Feuil.set("C10", "286.6")
        Feuil.set("D10", "363.13")
        Feuil.set("E10", "436.06")
        Feuil.set("A11", "Long_sortie")
        Feuil.set("B11", "208.67")
        Feuil.set("C11", "286.6")
        Feuil.set("D11", "363.13")
        Feuil.set("E11", "436.06")
        Feuil.set("A12", "EpMaxX_extrados")
        Feuil.set("B12", "300.0")
        Feuil.set("C12", "300.0")
        Feuil.set("D12", "300.0")
        Feuil.set("E12", "300.0")
        Feuil.set("A13", "EpMaxX_intrados")
        Feuil.set("B13", "300.0")
        Feuil.set("C13", "300.0")
        Feuil.set("D13", "300.0")
        Feuil.set("E13", "300.0")
        Feuil.set("A14", "EpMaxY_extrados")
        Feuil.set("B14", "50.0")
        Feuil.set("C14", "50.0")
        Feuil.set("D14", "50.0")
        Feuil.set("E14", "50.0")
        Feuil.set("A15", "EpMaxY_intrados")
        Feuil.set("B15", "50.0")
        Feuil.set("C15", "50.0")
        Feuil.set("D15", "50.0")
        Feuil.set("E15", "50.0")
        Feuil.set("A16", "EpInflex_extrados")
        Feuil.set("B16", "750.0")
        Feuil.set("C16", "750.0")
        Feuil.set("D16", "750.0")
        Feuil.set("E16", "750.0")
        Feuil.set("A17", "EpInflex_intrados")
        Feuil.set("B17", "750.0")
        Feuil.set("C17", "750.0")
        Feuil.set("D17", "750.0")
        Feuil.set("E17", "750.0")
        Feuil.set("A18", "EpLast_extrados")
        Feuil.set("B18", "0.85")
        Feuil.set("C18", "0.85")
        Feuil.set("D18", "0.85")
        Feuil.set("E18", "0.85")
        Feuil.set("A19", "EpLast_intrados")
        Feuil.set("B19", "0.85")
        Feuil.set("C19", "0.85")
        Feuil.set("D19", "0.85")
        Feuil.set("E19", "0.85")
        Feuil.setAlignment('B1:E19', 'center', 'keep')
        Feuil.setBackground('B1:E1', (1.000000,1.000000,0.498039))
        Feuil.setBackground('B3:E6', (0.666667,1.000000,0.498039))
        Feuil.setBackground('B8:E11', (0.666667,1.000000,0.498039))
        Feuil.setBackground('B12:E19', (0.666667,1.000000,1.000000))
        Feuil.setBackground('B2:E2', (0.752941,0.752941,0.752941))
        Feuil.setBackground('A2:A19', (0.752941,0.752941,0.752941))
        Feuil.setBackground('B7:E7', (0.752941,0.752941,0.752941))
        Feuil.setStyle('B2:E2', 'bold', 'add')
        Feuil.setStyle('B7:E7', 'bold', 'add')
        Feuil.setStyle('A1:A19', 'bold', 'add')
        Feuil.recompute()
        return
    def sauveTableur(self,fp):
    #   Met à jour les pilotes à partir des cellules du tableur
        debug('sauveTableur')
        Feuil=App.ActiveDocument.getObject('Tableau_pilote')
        sketchTheta_entree=App.ActiveDocument.getObject('skTheta_entree')
        sketchTheta_sortie=App.ActiveDocument.getObject('skTheta_sortie')
        sketchAlpha_entree=App.ActiveDocument.getObject('skAlpha_entree')
        sketchAlpha_sortie=App.ActiveDocument.getObject('skAlpha_sortie')
        sketchPoids_entree=App.ActiveDocument.getObject('skPoids_entree')
        sketchPoids_sortie=App.ActiveDocument.getObject('skPoids_sortie')
        sketchLong_entree=App.ActiveDocument.getObject('skLong_entree')
        sketchLong_sortie=App.ActiveDocument.getObject('skLong_sortie')
        sketchEpMaxXEx=App.ActiveDocument.getObject('skEpMaxXEx')
        sketchEpMaxXIn=App.ActiveDocument.getObject('skEpMaxXIn')
        sketchEpMaxYEx=App.ActiveDocument.getObject('skEpMaxYEx')
        sketchEpMaxYIn=App.ActiveDocument.getObject('skEpMaxYIn')
        sketchEpInflexEx=App.ActiveDocument.getObject('skEpInflexEx')
        sketchEpInflexIn=App.ActiveDocument.getObject('skEpInflexIn')
        sketchEpLastEx=App.ActiveDocument.getObject('skEpLastEx')
        sketchEpLastIn=App.ActiveDocument.getObject('skEpLastIn')
        t0=str(Feuil.B1*100.)+' mm'
        t1=str(Feuil.C1*100.)+' mm'
        t2=str(Feuil.D1*100.)+' mm'
        t3=str(Feuil.E1*100.)+' mm'
        tt0=str(Feuil.B1)+' mm'
        tt1=str(Feuil.C1)+' mm'
        tt2=str(Feuil.D1)+' mm'
        tt3=str(Feuil.E1)+' mm'
        sketchTheta_entree.setDatum(0,App.Units.Quantity(t0))
        debug('0= '+ str(t0))
        sketchTheta_entree.setDatum(1,App.Units.Quantity(str(Feuil.B3)+' mm'))
        debug('1= '+str(Feuil.B3)+' mm'  )
        sketchTheta_entree.setDatum(2,App.Units.Quantity(t1))
        debug('2= '+ str(t1))
        sketchTheta_entree.setDatum(3,App.Units.Quantity(str(Feuil.C3)+' mm'))
        debug('3= '+str(Feuil.C3)+' mm'  )
        sketchTheta_entree.setDatum(4,App.Units.Quantity(t2))
        debug('4= '+ str(t2))
        sketchTheta_entree.setDatum(5,App.Units.Quantity(str(Feuil.D3)+' mm'))
        debug('5= '+str(Feuil.D3)+' mm'  )
        sketchTheta_entree.setDatum(6,App.Units.Quantity(t3))
        sketchTheta_entree.setDatum(7,App.Units.Quantity(str(Feuil.E3)+' mm'))
        sketchTheta_sortie.setDatum(0,App.Units.Quantity(t0))
        sketchTheta_sortie.setDatum(1,App.Units.Quantity(str(Feuil.B4)+' mm'))
        sketchTheta_sortie.setDatum(2,App.Units.Quantity(t1))
        sketchTheta_sortie.setDatum(3,App.Units.Quantity(str(Feuil.C4)+' mm'))
        sketchTheta_sortie.setDatum(4,App.Units.Quantity(t2))
        sketchTheta_sortie.setDatum(5,App.Units.Quantity(str(Feuil.D4)+' mm'))
        sketchTheta_sortie.setDatum(6,App.Units.Quantity(t3))
        sketchTheta_sortie.setDatum(7,App.Units.Quantity(str(Feuil.E4)+' mm'))
        sketchAlpha_entree.setDatum(0,App.Units.Quantity(t0))
        sketchAlpha_entree.setDatum(1,App.Units.Quantity(str(Feuil.B5)+' mm'))
        sketchAlpha_entree.setDatum(2,App.Units.Quantity(t1))
        sketchAlpha_entree.setDatum(3,App.Units.Quantity(str(Feuil.C5)+' mm'))
        sketchAlpha_entree.setDatum(4,App.Units.Quantity(t2))
        sketchAlpha_entree.setDatum(5,App.Units.Quantity(str(Feuil.D5)+' mm'))
        sketchAlpha_entree.setDatum(6,App.Units.Quantity(t3))
        sketchAlpha_entree.setDatum(7,App.Units.Quantity(str(Feuil.E5)+' mm'))
        sketchAlpha_sortie.setDatum(0,App.Units.Quantity(t0))
        sketchAlpha_sortie.setDatum(1,App.Units.Quantity(str(Feuil.B6)+' mm'))
        sketchAlpha_sortie.setDatum(2,App.Units.Quantity(t1))
        sketchAlpha_sortie.setDatum(3,App.Units.Quantity(str(Feuil.C6)+' mm'))
        sketchAlpha_sortie.setDatum(4,App.Units.Quantity(t2))
        sketchAlpha_sortie.setDatum(5,App.Units.Quantity(str(Feuil.D6)+' mm'))
        sketchAlpha_sortie.setDatum(6,App.Units.Quantity(t3))
        sketchAlpha_sortie.setDatum(7,App.Units.Quantity(str(Feuil.E6)+' mm'))
        sketchPoids_entree.setDatum(0,App.Units.Quantity(t0))
        sketchPoids_entree.setDatum(1,App.Units.Quantity(str(Feuil.B8)+' mm'))
        sketchPoids_entree.setDatum(2,App.Units.Quantity(t1))
        sketchPoids_entree.setDatum(3,App.Units.Quantity(str(Feuil.C8)+' mm'))
        sketchPoids_entree.setDatum(4,App.Units.Quantity(t2))
        sketchPoids_entree.setDatum(5,App.Units.Quantity(str(Feuil.D8)+' mm'))
        sketchPoids_entree.setDatum(6,App.Units.Quantity(t3))
        sketchPoids_entree.setDatum(7,App.Units.Quantity(str(Feuil.E8)+' mm'))
        sketchPoids_sortie.setDatum(0,App.Units.Quantity(t0))
        sketchPoids_sortie.setDatum(1,App.Units.Quantity(str(Feuil.B9)+' mm'))
        sketchPoids_sortie.setDatum(2,App.Units.Quantity(t1))
        sketchPoids_sortie.setDatum(3,App.Units.Quantity(str(Feuil.C9)+' mm'))
        sketchPoids_sortie.setDatum(4,App.Units.Quantity(t2))
        sketchPoids_sortie.setDatum(5,App.Units.Quantity(str(Feuil.D9)+' mm'))
        sketchPoids_sortie.setDatum(6,App.Units.Quantity(t3))
        sketchPoids_sortie.setDatum(7,App.Units.Quantity(str(Feuil.E9)+' mm'))
        sketchLong_entree.setDatum(0,App.Units.Quantity(t0))
        sketchLong_entree.setDatum(1,App.Units.Quantity(str(Feuil.B10)+' mm'))
        sketchLong_entree.setDatum(2,App.Units.Quantity(t1))
        sketchLong_entree.setDatum(3,App.Units.Quantity(str(Feuil.C10)+' mm'))
        sketchLong_entree.setDatum(4,App.Units.Quantity(t2))
        sketchLong_entree.setDatum(5,App.Units.Quantity(str(Feuil.D10)+' mm'))
        sketchLong_entree.setDatum(6,App.Units.Quantity(t3))
        sketchLong_entree.setDatum(7,App.Units.Quantity(str(Feuil.E10)+' mm'))
        sketchLong_sortie.setDatum(0,App.Units.Quantity(t0))
        sketchLong_sortie.setDatum(1,App.Units.Quantity(str(Feuil.B11)+' mm'))
        sketchLong_sortie.setDatum(2,App.Units.Quantity(t1))
        sketchLong_sortie.setDatum(3,App.Units.Quantity(str(Feuil.C11)+' mm'))
        sketchLong_sortie.setDatum(4,App.Units.Quantity(t2))
        sketchLong_sortie.setDatum(5,App.Units.Quantity(str(Feuil.D11)+' mm'))
        sketchLong_sortie.setDatum(6,App.Units.Quantity(t3))
        sketchLong_sortie.setDatum(7,App.Units.Quantity(str(Feuil.E11)+' mm'))
        sketchEpMaxXEx.setDatum(0,App.Units.Quantity(t0))
        sketchEpMaxXEx.setDatum(1,App.Units.Quantity(str(Feuil.B12)+' mm'))
        sketchEpMaxXEx.setDatum(2,App.Units.Quantity(t1))
        sketchEpMaxXEx.setDatum(3,App.Units.Quantity(str(Feuil.C12)+' mm'))
        sketchEpMaxXEx.setDatum(4,App.Units.Quantity(t2))
        sketchEpMaxXEx.setDatum(5,App.Units.Quantity(str(Feuil.D12)+' mm'))
        sketchEpMaxXEx.setDatum(6,App.Units.Quantity(t3))
        sketchEpMaxXEx.setDatum(7,App.Units.Quantity(str(Feuil.E12)+' mm'))
        sketchEpMaxXIn.setDatum(0,App.Units.Quantity(t0))
        sketchEpMaxXIn.setDatum(1,App.Units.Quantity(str(Feuil.B13)+' mm'))
        sketchEpMaxXIn.setDatum(2,App.Units.Quantity(t1))
        sketchEpMaxXIn.setDatum(3,App.Units.Quantity(str(Feuil.C13)+' mm'))
        sketchEpMaxXIn.setDatum(4,App.Units.Quantity(t2))
        sketchEpMaxXIn.setDatum(5,App.Units.Quantity(str(Feuil.D13)+' mm'))
        sketchEpMaxXIn.setDatum(6,App.Units.Quantity(t3))
        sketchEpMaxXIn.setDatum(7,App.Units.Quantity(str(Feuil.E13)+' mm'))
        sketchEpMaxYEx.setDatum(0,App.Units.Quantity(t0))
        sketchEpMaxYEx.setDatum(1,App.Units.Quantity(str(Feuil.B14)+' mm'))
        sketchEpMaxYEx.setDatum(2,App.Units.Quantity(t1))
        sketchEpMaxYEx.setDatum(3,App.Units.Quantity(str(Feuil.C14)+' mm'))
        sketchEpMaxYEx.setDatum(4,App.Units.Quantity(t2))
        sketchEpMaxYEx.setDatum(5,App.Units.Quantity(str(Feuil.D14)+' mm'))
        sketchEpMaxYEx.setDatum(6,App.Units.Quantity(t3))
        sketchEpMaxYEx.setDatum(7,App.Units.Quantity(str(Feuil.E14)+' mm'))
        sketchEpMaxYIn.setDatum(0,App.Units.Quantity(t0))
        sketchEpMaxYIn.setDatum(1,App.Units.Quantity(str(Feuil.B15)+' mm'))
        sketchEpMaxYIn.setDatum(2,App.Units.Quantity(t1))
        sketchEpMaxYIn.setDatum(3,App.Units.Quantity(str(Feuil.C15)+' mm'))
        sketchEpMaxYIn.setDatum(4,App.Units.Quantity(t2))
        sketchEpMaxYIn.setDatum(5,App.Units.Quantity(str(Feuil.D15)+' mm'))
        sketchEpMaxYIn.setDatum(6,App.Units.Quantity(t3))
        sketchEpMaxYIn.setDatum(7,App.Units.Quantity(str(Feuil.E15)+' mm'))
        sketchEpInflexEx.setDatum(0,App.Units.Quantity(t0))
        sketchEpInflexEx.setDatum(1,App.Units.Quantity(str(Feuil.B16)+' mm'))
        sketchEpInflexEx.setDatum(2,App.Units.Quantity(t1))
        sketchEpInflexEx.setDatum(3,App.Units.Quantity(str(Feuil.C16)+' mm'))
        sketchEpInflexEx.setDatum(4,App.Units.Quantity(t2))
        sketchEpInflexEx.setDatum(5,App.Units.Quantity(str(Feuil.D16)+' mm'))
        sketchEpInflexEx.setDatum(6,App.Units.Quantity(t3))
        sketchEpInflexEx.setDatum(7,App.Units.Quantity(str(Feuil.E16)+' mm'))
        sketchEpInflexIn.setDatum(0,App.Units.Quantity(t0))
        sketchEpInflexIn.setDatum(1,App.Units.Quantity(str(Feuil.B17)+' mm'))
        sketchEpInflexIn.setDatum(2,App.Units.Quantity(t1))
        sketchEpInflexIn.setDatum(3,App.Units.Quantity(str(Feuil.C17)+' mm'))
        sketchEpInflexIn.setDatum(4,App.Units.Quantity(t2))
        sketchEpInflexIn.setDatum(5,App.Units.Quantity(str(Feuil.D17)+' mm'))
        sketchEpInflexIn.setDatum(6,App.Units.Quantity(t3))
        sketchEpInflexIn.setDatum(7,App.Units.Quantity(str(Feuil.E17)+' mm'))
        sketchEpLastEx.setDatum(0,App.Units.Quantity(tt0))
        sketchEpLastEx.setDatum(1,App.Units.Quantity(str(Feuil.B18)+' mm'))
        sketchEpLastEx.setDatum(2,App.Units.Quantity(tt1))
        sketchEpLastEx.setDatum(3,App.Units.Quantity(str(Feuil.C18)+' mm'))
        sketchEpLastEx.setDatum(4,App.Units.Quantity(tt2))
        sketchEpLastEx.setDatum(5,App.Units.Quantity(str(Feuil.D18)+' mm'))
        sketchEpLastEx.setDatum(6,App.Units.Quantity(tt3))
        sketchEpLastEx.setDatum(7,App.Units.Quantity(str(Feuil.E18)+' mm'))
        sketchEpLastIn.setDatum(0,App.Units.Quantity(tt0))
        sketchEpLastIn.setDatum(1,App.Units.Quantity(str(Feuil.B19)+' mm'))
        sketchEpLastIn.setDatum(2,App.Units.Quantity(tt1))
        sketchEpLastIn.setDatum(3,App.Units.Quantity(str(Feuil.C19)+' mm'))
        sketchEpLastIn.setDatum(4,App.Units.Quantity(tt2))
        sketchEpLastIn.setDatum(5,App.Units.Quantity(str(Feuil.D19)+' mm'))
        sketchEpLastIn.setDatum(6,App.Units.Quantity(tt3))
        sketchEpLastIn.setDatum(7,App.Units.Quantity(str(Feuil.E19)+' mm'))
        App.ActiveDocument.recompute()
        debug("sauveTableur - fin")
        return
#
#
#       Plan méridien
#
#
    def initMeridien(self,fp):
        debug("initMeridien")
        LoiMeridien=[]
        LoiMeridien.append(App.Vector(549,-72.7,0))
        LoiMeridien.append(App.Vector(536.13,-30.64,0))
        LoiMeridien.append(App.Vector(526.46,17.81,0))
        LoiMeridien.append(App.Vector(520,72.7,0))
        LoiMeridien.append(App.Vector(388.74,62.49,0))
        LoiMeridien.append(App.Vector(275.42,11.25,0))
        LoiMeridien.append(App.Vector(186,-57,0))
        LoiMeridien.append(App.Vector(271.03,-202.24,0))
        LoiMeridien.append(App.Vector(415.81,-242.24,0))
        LoiMeridien.append(App.Vector(500,-229,0))
        LoiMeridien.append(App.Vector(495.17,-138.42,0))
        LoiMeridien.append(App.Vector(511.50,-86.32,0))
        fp.addProperty("App::PropertyVectorList","Meridien","Plan 1 - Meridien","Vecteurs des points").Meridien=LoiMeridien
        fp.setEditorMode("Meridien",1)
        sketch=App.ActiveDocument.addObject('Sketcher::SketchObject','Meridien')
        docIU=App.ActiveDocument.getObject("Interface_usager")
        docIU.addObject(sketch)
#        sketch.Label='Meridien'
        sketch.Placement = App.Placement(App.Vector(0.000000,0.000000,0.000000),App.Rotation(-0.707107,0.000000,0.000000,-0.707107))
        docPilote = App.ActiveDocument.getObject("Pilote")
    #   On s'assure d'avoir des coordonnées cohérentes avec le sens de rotation
        fp=App.ActiveDocument.getObject('Parametres')
    #
    #   On crée les points et on applique les contraintes fixes pour immobiliser les coins
    #
        debug('Plan méridien : ')
        debug(sketch.Name)
        #
        Pt=[]
        for i in range(12):
            I=str(i+1)
            Pt.append(sketch.addGeometry(Part.Point(fp.Meridien[i])))
            self.immobilisePoint(sketch, Pt[i], "M"+I)
    #
    #   On crée les 4 arêtes délimitant l'aubage dans le plan méridien
    #
        (BS1,L11,L12)=self.planBS(sketch,Pt[0],Pt[1],Pt[2],Pt[3])   # "Edge1"
        (BS2,L21,L22)=self.planBS(sketch,Pt[3],Pt[4],Pt[5],Pt[6])   # "Edge2"
        (BS3,L31,L32)=self.planBS(sketch,Pt[6],Pt[7],Pt[8],Pt[9])   # "Edge3"
        (BS4,L41,L42)=self.planBS(sketch,Pt[9],Pt[10],Pt[11],Pt[0])   # "Edge4"      
    #
    #   groupe Meridien 
    #
    #
        docPlanMeridien = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Plan_Meridien")
    #
    #   Création de la surface servant à  interpoler les filets 
    # 
        surfMeridien=App.ActiveDocument.addObject("Surface::GeomFillSurface","Surface")
        surfMeridien.BoundaryList=[(sketch,("Edge1")),(sketch,("Edge2")),(sketch,("Edge3")),(sketch,("Edge4"))]
        docPlanMeridien.addObject(surfMeridien)
        sketch.Visibility=True
        debug("initMeridien-fin")
        return
    def traceMeridien(self,fp):
        debug('traceMeridien')
    #
    #   groupe et sketch Meridien 
    #
    #
        docPlanMeridien = App.ActiveDocument.getObject("Plan_Meridien")
        sketch=App.ActiveDocument.getObject('Meridien')
    #
    #   Création de la surface servant à  interpoler les filets 
    # 
        surfMeridien=App.ActiveDocument.getObject("Surface")
    #
    #   Création du réseau de filets dans le plan méridien
    #
        fpCiso=iso.makeIsoCurveFeature()
        debug('fpCiso créé vide')
        docPlanMeridien.addObject(fpCiso)
        debug('mis dans le groupe Plan_Meridien')
        fpCiso.Label='IsoCurve'
        fpCiso.Face=(surfMeridien,['Face1',])
        debug('fpCiso attribut Face1')
        fpCiso.NumberU=fp.Nfilets
        fpCiso.NumberV=0
#        fpCiso.recompute()
    #
    #   Discretisation des filets
    #
        i=0
        for edge in fpCiso.Shape.Edges:
            I=str(i+1)
            debug(I)
            fpM = App.ActiveDocument.addObject("Part::FeaturePython","FiletM"+I)
            docPlanMeridien.addObject(fpM)
            Discretize.Discretization(fpM, (App.ActiveDocument.getObject("IsoCurve"),"Edge"+I))
            fpM.Number=fp.Npts
            Discretize.ViewProviderDisc(fpM.ViewObject)
            fpM.ViewObject.PointSize = 3
#            fpM.recompute()
            i+=1
        App.ActiveDocument.recompute()
        debug('traceMeridien - fin')
        return  
    def sauveMeridien(self,fp):
        # Sauve dans Parametres les points du sketch Meridien après une modification par l'usager
        debug('sauveMeridien')
        fp.Init=False
        sketch=App.ActiveDocument.Meridien
        LoiMeridien=[]
        for i in range(0,24,2) : LoiMeridien.append(App.Vector(sketch.Constraints[i].Value,sketch.Constraints[i+1].Value,0))
        fp.Meridien=LoiMeridien
        App.ActiveDocument.recompute()
        debug('sauveMeridien - fin')
        return

#
#
#       Plan des épaisseurs
#
#
    def initEpaisseur(self,fp):
        debug("initEpaisseur")
    #
    #   Routine pour créer les splines à 5 points(0,1,2,3,4) qui pilotent les variables:
    #
    #   EpMaxXEx -> position en x du point 2 qui contrôle l'épaisseur maximale pour l'extrados
    #   EpMaxXIn -> ....   ....   pour l'intrados
    #   EpMaxYEx -> position en y du point 2 qui contrôle l'épaisseur maximale pour l'extrados
    #   EpMaxYIn -> ....   ....   pour l'intrados
    #   EpInflexEx -> position en x du point 3 qui contrôle l'inflexion pour l'extrados
    #   EpInflexIn -> ....   ....   pour l'intrados
    #   EpLastEx -> position en x de la troncature du profil au bord de fuite pour l'extrados
    #   EpLastIn -> ....   ....   pour l'intrados
        docPilote = App.ActiveDocument.getObject("Pilote")
        Feuil= App.ActiveDocument.getObject("Tableau_pilote")
        LoiEpaisseur=[]
        sketchEpMaxXEx=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpMaxXEx')
        docPilote.addObject(sketchEpMaxXEx)
        sketchEpMaxXIn=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpMaxXIn')
        docPilote.addObject(sketchEpMaxXIn)
        sketchEpMaxYEx=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpMaxYEx')
        docPilote.addObject(sketchEpMaxYEx)
        sketchEpMaxYIn=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpMaxYIn')
        docPilote.addObject(sketchEpMaxYIn)
        sketchEpInflexEx=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpInflexEx')
        docPilote.addObject(sketchEpInflexEx)
        sketchEpInflexIn=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpInflexIn')
        docPilote.addObject(sketchEpInflexIn)
        sketchEpLastEx=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpLastEx')
        docPilote.addObject(sketchEpLastEx)
        sketchEpLastIn=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpLastIn')
        docPilote.addObject(sketchEpLastIn)
     #   les abscisses des esquisses sont fonction de t*100, t variant de 0 à 100 mm dans FreeCAD
        t0=Feuil.B1*100.
        t1=Feuil.C1*100.
        t2=Feuil.D1*100.
        t3=Feuil.E1*100.
    #
    #   Initialisation des variables
    #
        LoiEpaisseur.append(App.Vector(t0, Feuil.B12,0)) #(t,ÉpaisseurMaxXExtrados)
        LoiEpaisseur.append(App.Vector(t1, Feuil.C12, 0))
        LoiEpaisseur.append(App.Vector(t2, Feuil.D12, 0))
        LoiEpaisseur.append(App.Vector(t3, Feuil.E12, 0))
        LoiEpaisseur.append(App.Vector(t0, Feuil.B14,0)) #(t,ÉpaisseurMaxYExtrados)
        LoiEpaisseur.append(App.Vector(t1, Feuil.C14, 0))
        LoiEpaisseur.append(App.Vector(t2, Feuil.D14, 0))
        LoiEpaisseur.append(App.Vector(t3, Feuil.E14, 0))
        LoiEpaisseur.append(App.Vector(t0, Feuil.B16,0)) #(t,ÉpaisseurInflexionExtrados)
        LoiEpaisseur.append(App.Vector(t1, Feuil.C16, 0))
        LoiEpaisseur.append(App.Vector(t2, Feuil.D16, 0))
        LoiEpaisseur.append(App.Vector(t3, Feuil.E16, 0))
        tt0=Feuil.B1
        tt1=Feuil.C1
        tt2=Feuil.D1
        tt3=Feuil.E1
        LoiEpaisseur.append(App.Vector(tt0, Feuil.B18, 0)) #(t,ÉpaisseurLastExtrados)
        LoiEpaisseur.append(App.Vector(tt1, Feuil.C18, 0))
        LoiEpaisseur.append(App.Vector(tt2, Feuil.D18, 0))
        LoiEpaisseur.append(App.Vector(tt3, Feuil.E18, 0))
        LoiEpaisseur.append(App.Vector(t0, Feuil.B13,0)) #(t,ÉpaisseurMaxXIntrados)
        LoiEpaisseur.append(App.Vector(t1, Feuil.C13, 0))
        LoiEpaisseur.append(App.Vector(t2, Feuil.D13, 0))
        LoiEpaisseur.append(App.Vector(t3, Feuil.E13, 0))
        LoiEpaisseur.append(App.Vector(t0, Feuil.B15,0)) #(t,ÉpaisseurMaxYIntrados)
        LoiEpaisseur.append(App.Vector(t1, Feuil.C15, 0))
        LoiEpaisseur.append(App.Vector(t2, Feuil.D15, 0))
        LoiEpaisseur.append(App.Vector(t3, Feuil.E15, 0))
        LoiEpaisseur.append(App.Vector(t0, Feuil.B17,0)) #(t,ÉpaisseurInflexionIntrados)
        LoiEpaisseur.append(App.Vector(t1, Feuil.C17, 0))
        LoiEpaisseur.append(App.Vector(t2, Feuil.D17, 0))
        LoiEpaisseur.append(App.Vector(t3, Feuil.E17, 0))
        LoiEpaisseur.append(App.Vector(tt0, Feuil.B19, 0)) #(t,ÉpaisseurLastIntrados)
        LoiEpaisseur.append(App.Vector(tt1, Feuil.C19, 0))
        LoiEpaisseur.append(App.Vector(tt2, Feuil.D19, 0))
        LoiEpaisseur.append(App.Vector(tt3, Feuil.E19, 0))
        fp.addProperty("App::PropertyVectorList","Epaisseur","Plan 2 - Epaisseur","Loi des épaisseurs").Epaisseur=LoiEpaisseur
        fp.setEditorMode("Epaisseur",1)
    #
    #   Loi déterminant l'épaisseur maximum en X pour l'extrados
    # 
        Pt0=sketchEpMaxXEx.addGeometry(Part.Point(LoiEpaisseur[0]))
        Pt1=sketchEpMaxXEx.addGeometry(Part.Point(LoiEpaisseur[1]))
        Pt2=sketchEpMaxXEx.addGeometry(Part.Point(LoiEpaisseur[2]))
        Pt3=sketchEpMaxXEx.addGeometry(Part.Point(LoiEpaisseur[3]))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpMaxXEx, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpMaxXEx, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpMaxXEx, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpMaxXEx, Pt3, "PtEx3")
        self.planBS(sketchEpMaxXEx,Pt0, Pt1, Pt2, Pt3)
    #
    #   Loi déterminant l'épaisseur maximum en Y pour l'extrados
    # 
        Pt0=sketchEpMaxYEx.addGeometry(Part.Point(LoiEpaisseur[4]))
        Pt1=sketchEpMaxYEx.addGeometry(Part.Point(LoiEpaisseur[5]))
        Pt2=sketchEpMaxYEx.addGeometry(Part.Point(LoiEpaisseur[6]))
        Pt3=sketchEpMaxYEx.addGeometry(Part.Point(LoiEpaisseur[7]))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpMaxYEx, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpMaxYEx, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpMaxYEx, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpMaxYEx, Pt3, "PtEx3")
        self.planBS(sketchEpMaxYEx,Pt0, Pt1, Pt2, Pt3)
    #
    #   Loi déterminant l'inflexion en X pour l'extrados
    # 
        Pt0=sketchEpInflexEx.addGeometry(Part.Point(LoiEpaisseur[8]))
        Pt1=sketchEpInflexEx.addGeometry(Part.Point(LoiEpaisseur[9]))
        Pt2=sketchEpInflexEx.addGeometry(Part.Point(LoiEpaisseur[10]))
        Pt3=sketchEpInflexEx.addGeometry(Part.Point(LoiEpaisseur[11]))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpInflexEx, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpInflexEx, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpInflexEx, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpInflexEx, Pt3, "PtEx3")
        self.planBS(sketchEpInflexEx,Pt0, Pt1, Pt2, Pt3)
    #
    #   Loi déterminant le dernier pt en X pour l'extrados
    # 
        Pt0=sketchEpLastEx.addGeometry(Part.Point(LoiEpaisseur[12]))
        Pt1=sketchEpLastEx.addGeometry(Part.Point(LoiEpaisseur[13]))
        Pt2=sketchEpLastEx.addGeometry(Part.Point(LoiEpaisseur[14]))
        Pt3=sketchEpLastEx.addGeometry(Part.Point(LoiEpaisseur[15]))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpLastEx, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpLastEx, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpLastEx, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpLastEx, Pt3, "PtEx3")
        self.planBS(sketchEpLastEx,Pt0, Pt1, Pt2, Pt3)
    #
    #  Loi déterminant l'épaisseur maximum en X pour l'intrados
    #
        Pt0=sketchEpMaxXIn.addGeometry(Part.Point(LoiEpaisseur[16]))
        Pt1=sketchEpMaxXIn.addGeometry(Part.Point(LoiEpaisseur[17]))
        Pt2=sketchEpMaxXIn.addGeometry(Part.Point(LoiEpaisseur[18]))
        Pt3=sketchEpMaxXIn.addGeometry(Part.Point(LoiEpaisseur[19]))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpMaxXIn, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpMaxXIn, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpMaxXIn, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpMaxXIn, Pt3, "PtIn3")
        self.planBS(sketchEpMaxXIn,Pt0, Pt1, Pt2, Pt3)
    #
    #   Loi déterminant l'épaisseur maximum en Y pour l'intrados
    # 
        Pt0=sketchEpMaxYIn.addGeometry(Part.Point(LoiEpaisseur[20]))
        Pt1=sketchEpMaxYIn.addGeometry(Part.Point(LoiEpaisseur[21]))
        Pt2=sketchEpMaxYIn.addGeometry(Part.Point(LoiEpaisseur[22]))
        Pt3=sketchEpMaxYIn.addGeometry(Part.Point(LoiEpaisseur[23]))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpMaxYIn, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpMaxYIn, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpMaxYIn, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpMaxYIn, Pt3, "PtIn3")
        self.planBS(sketchEpMaxYIn,Pt0, Pt1, Pt2, Pt3)
    #
    #   Loi déterminant l'inflexion en X pour l'intrados
    # 
        Pt0=sketchEpInflexIn.addGeometry(Part.Point(LoiEpaisseur[24]))
        Pt1=sketchEpInflexIn.addGeometry(Part.Point(LoiEpaisseur[25]))
        Pt2=sketchEpInflexIn.addGeometry(Part.Point(LoiEpaisseur[26]))
        Pt3=sketchEpInflexIn.addGeometry(Part.Point(LoiEpaisseur[27]))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpInflexIn, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpInflexIn, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpInflexIn, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpInflexIn, Pt3, "PtIn3")
        self.planBS(sketchEpInflexIn,Pt0, Pt1, Pt2, Pt3)
    #
    #   Loi déterminant le dernier pt en X pour l'intrados
    # 
        Pt0=sketchEpLastIn.addGeometry(Part.Point(LoiEpaisseur[28]))
        Pt1=sketchEpLastIn.addGeometry(Part.Point(LoiEpaisseur[29]))
        Pt2=sketchEpLastIn.addGeometry(Part.Point(LoiEpaisseur[30]))
        Pt3=sketchEpLastIn.addGeometry(Part.Point(LoiEpaisseur[31]))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpLastIn, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpLastIn, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpLastIn, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpLastIn, Pt3, "PtIn3")
        self.planBS(sketchEpLastIn,Pt0, Pt1, Pt2, Pt3) 
        debug("initEpaisseur - fin")
        return
    def traceEpaisseur(self,fp):
    #    
    #   Creation des lois d'épaisseur en 2D pour éventuellement transférer sur chacun des filets Cascade
    #    
        debug("traceEpaisseur")
    # #
    # #   Stokage pour sauvegarde de l'information dans Epaisseur
    # #   
        docPlanEpaisseur = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Plan_Epaisseurs")
        docPilote = App.ActiveDocument.getObject("Pilote")
    #
    #   Discretisation des pilotes des variables pour chaque filet
    #
        EpMaxXEx = App.ActiveDocument.addObject("Part::FeaturePython", "EpMaxXEx")
        docPilote.addObject(EpMaxXEx)
        Discretize.Discretization(EpMaxXEx, (App.ActiveDocument.getObject("skEpMaxXEx"),"Edge1"))
        EpMaxXEx.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpMaxXEx.ViewObject)
        EpMaxXEx.ViewObject.PointSize = 3
        EpMaxXIn = App.ActiveDocument.addObject("Part::FeaturePython", "EpMaxXIn")
        docPilote.addObject(EpMaxXIn)
        Discretize.Discretization(EpMaxXIn, (App.ActiveDocument.getObject("skEpMaxXIn"),"Edge1"))
        EpMaxXIn.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpMaxXIn.ViewObject)
        EpMaxXIn.ViewObject.PointSize = 3
        EpMaxYEx = App.ActiveDocument.addObject("Part::FeaturePython", "EpMaxYEx")
        docPilote.addObject(EpMaxYEx)
        Discretize.Discretization(EpMaxYEx, (App.ActiveDocument.getObject("skEpMaxYEx"),"Edge1"))
        EpMaxYEx.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpMaxYEx.ViewObject)
        EpMaxYEx.ViewObject.PointSize = 3
        EpMaxYIn = App.ActiveDocument.addObject("Part::FeaturePython", "EpMaxYIn")
        docPilote.addObject(EpMaxYIn)
        Discretize.Discretization(EpMaxYIn, (App.ActiveDocument.getObject("skEpMaxYIn"),"Edge1"))
        EpMaxYIn.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpMaxYIn.ViewObject)
        EpMaxYIn.ViewObject.PointSize = 3
        EpInflexEx = App.ActiveDocument.addObject("Part::FeaturePython", "EpInflexEx")
        docPilote.addObject(EpInflexEx)
        Discretize.Discretization(EpInflexEx, (App.ActiveDocument.getObject("skEpInflexEx"),"Edge1"))
        EpInflexEx.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpInflexEx.ViewObject)
        EpInflexEx.ViewObject.PointSize = 3
        EpInflexIn = App.ActiveDocument.addObject("Part::FeaturePython", "EpInflexIn")
        docPilote.addObject(EpInflexIn)
        Discretize.Discretization(EpInflexIn, (App.ActiveDocument.getObject("skEpInflexIn"),"Edge1"))
        EpInflexIn.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpInflexIn.ViewObject)
        EpInflexIn.ViewObject.PointSize = 3
        EpLastEx = App.ActiveDocument.addObject("Part::FeaturePython", "EpLastEx")
        docPilote.addObject(EpLastEx)
        Discretize.Discretization(EpLastEx, (App.ActiveDocument.getObject("skEpLastEx"),"Edge1"))
        EpLastEx.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpLastEx.ViewObject)
        EpLastEx.ViewObject.PointSize = 3
        EpLastIn = App.ActiveDocument.addObject("Part::FeaturePython", "EpLastIn")
        docPilote.addObject(EpLastIn)
        Discretize.Discretization(EpLastIn, (App.ActiveDocument.getObject("skEpLastIn"),"Edge1"))
        EpLastIn.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpLastIn.ViewObject)
        EpLastIn.ViewObject.PointSize = 3         
    #   création du sketch en x-y, x représentant la corde du profil et y son épaisseur pour chacun des filets
        self.sketchDiscEpaisseur(fp, EpMaxXEx, EpMaxXIn, EpMaxYEx, EpMaxYIn, EpInflexEx, EpInflexIn, EpLastEx, EpLastIn)
        App.ActiveDocument.recompute()
        debug("traceEpaisseur - fin")
        return
    def sketchDiscEpaisseur(self,fp, EpMaxXEx, EpMaxXIn, EpMaxYEx, EpMaxYIn, EpInflexEx, EpInflexIn, EpLastEx, EpLastIn):
        debug('sketchDiscEpaisseur')
        docPlanEpaisseur=App.ActiveDocument.getObject('Plan_Epaisseurs')
        debug('fp.preNfilets= '+str(fp.preNfilets))
        for i in range (fp.preNfilets):
            I=str(i+1)
            debug(I)
            App.ActiveDocument.getObject('LoiEpaisseur'+I+'e').recompute()
            App.ActiveDocument.getObject("LoiEpaisseur"+I+"es").recompute()
            App.ActiveDocument.getObject('LoiEpaisseur'+I+'i').recompute()
            App.ActiveDocument.getObject("LoiEpaisseur"+I+"is").recompute()
        debug('fp.Nfilets= '+str(fp.Nfilets))
        for i in range(fp.preNfilets,fp.Nfilets):
            I=str(i+1)
            debug(I)
    #   Création du sketch extrados
            sketch_e=App.ActiveDocument.addObject('Sketcher::SketchObject','skLoiEpaisseur'+I+'e')
            if fp.preNfilets > 0 :sketch_e.Visibility=App.ActiveDocument.getObject('skLoiEpaisseur'+str(i)+'e').Visibility
            docPlanEpaisseur.addObject(sketch_e)            
            fpe = App.ActiveDocument.addObject("Part::FeaturePython",'LoiEpaisseur'+I+'e')
            docPlanEpaisseur.addObject(fpe)
            debug(I)
    #
    #   Création de la loi d'épaisseur dans le plan de l'épaisseur
    #   il y a une loi pour l'extrados et une autre pour l'intrados
    #   On assume un profil de corde 1000 mm dans FreeCAD
    #
    #   Création des 5 poles du spline extrados et du poids de chacun
    #       point 0 extrados
            r00=100.
            Pt00=sketch_e.addGeometry(Part.Point(App.Vector(0., 0., r00)))
    #       point 1 extrados
            r01=100.
            Pt01=sketch_e.addGeometry(Part.Point(App.Vector(0., EpMaxYEx.Points[i].y, r01 )))
    #       point 2 extrados
            r02=100.
            Pt02=sketch_e.addGeometry(Part.Point(App.Vector(EpMaxXEx.Points[i].y, EpMaxYEx.Points[i].y, r02)))
    #       point 3 extrados            
            r03=100.
            Pt03=sketch_e.addGeometry(Part.Point(App.Vector(EpInflexEx.Points[i].y, 0., r03)))
    #       point 4 extrados  
            r04=100.
            Pt04=sketch_e.addGeometry(Part.Point(App.Vector(1000., 0., r04)))
    #       Création du BSpline extrados
            debug('Geo sketch_e ='+str(sketch_e.Geometry))
            BSe=self.epaisseurBS(sketch_e,Pt00,Pt01,Pt02,Pt03,Pt04)
            sketch_e.recompute()
    #       on immobilise tous les points
            (Ddl00x,Ddl00y)=self.immobilisePoint(sketch_e, Pt00, "Ep"+I+"e0") #18
            (Ddl01x,Ddl01y)=self.immobilisePoint(sketch_e, Pt01, "Ep"+I+"e1") #20
            (Ddl02x,Ddl02y)=self.immobilisePoint(sketch_e, Pt02, "Ep"+I+"e2") #22
            (Ddl03x,Ddl03y)=self.immobilisePoint(sketch_e, Pt03, "Ep"+I+"e3") #24
            (Ddl04x,Ddl04y)=self.immobilisePoint(sketch_e, Pt04, "Ep"+I+"e4") #26
    #       On calcul les points sur le profil d'épaisseur extrados
            Discretize.Discretization(fpe, (App.ActiveDocument.getObject("skLoiEpaisseur"+I+"e"),"Edge1"))
            fpe.ParameterLast=1.
            fpe.Algorithm="Number"
            fpe.Number=fp.Npts
            # Discretize.ViewProviderDisc(fpe.ViewObject)
            # fpe.ViewObject.PointSize = 3
            fpe.recompute()
    #       On interpole les points pour qu'ils correspondent à la coordonnée s du plan meridien
            sX=[]
        #   fpes est comme fpe mais avec une distribution suivant s du plan méridien
            fpes = App.ActiveDocument.addObject("Part::FeaturePython","LoiEpaisseur"+I+"es")
            docPlanEpaisseur.addObject(fpes)
            eLast=EpLastEx.Points[i].y
            DiscEp_s(fpes, fpe, fp.Npts, eLast)
            ViewProviderDisc(fpes.ViewObject)
            fpes.ViewObject.PointSize = 3 
            if fp.preNfilets > 0 :fpes.Visibility=App.ActiveDocument.getObject('LoiEpaisseur'+str(i)+'es').Visibility
            debug('fpes.Points')
            debug(fpes.Points)
    #   Création du sketch intrados
            sketch_i=App.ActiveDocument.addObject('Sketcher::SketchObject','skLoiEpaisseur'+I+'i')
            if fp.preNfilets > 0 :sketch_i.Visibility=App.ActiveDocument.getObject('skLoiEpaisseur'+str(i)+'i').Visibility
            docPlanEpaisseur.addObject(sketch_i) 
            fpi = App.ActiveDocument.addObject("Part::FeaturePython",'LoiEpaisseur'+I+'i')
            docPlanEpaisseur.addObject(fpi)
    #   Création des 5 poles du spline intrados et du poids de chacun
    #       point 0 intrados
            r10=100.
            Pt10=sketch_i.addGeometry(Part.Point(App.Vector(0., 0., r10)))
    #       point 1 intrados
            r11=100.
            Pt11=sketch_i.addGeometry(Part.Point(App.Vector(0., -EpMaxYIn.Points[i].y, r11 )))
    #       point 2 intrados
            r12=100.
            Pt12=sketch_i.addGeometry(Part.Point(App.Vector(EpMaxXIn.Points[i].y, -EpMaxYIn.Points[i].y, r12)))
    #       point 3 intrados            
            r13=100.
            Pt13=sketch_i.addGeometry(Part.Point(App.Vector(EpInflexIn.Points[i].y, 0., r13)))
    #       point 4 intrados 
            r14=100.
            Pt14=sketch_i.addGeometry(Part.Point(App.Vector(1000., 0., r14)))
    #       Création du BSpline intrados
            debug('Geo sketch_i ='+str(sketch_i.Geometry))
            BSi=self.epaisseurBS(sketch_i,Pt10,Pt11,Pt12,Pt13,Pt14)
            sketch_i.recompute()
    #       on immobilise tous les points
            (Ddl10x,Ddl10y)=self.immobilisePoint(sketch_i, Pt10, "Ep"+I+"i0") #18
            (Ddl11x,Ddl11y)=self.immobilisePoint(sketch_i, Pt11, "Ep"+I+"i1") #20
            (Ddl12x,Ddl12y)=self.immobilisePoint(sketch_i, Pt12, "Ep"+I+"i2") #22
            (Ddl13x,Ddl13y)=self.immobilisePoint(sketch_i, Pt13, "Ep"+I+"i3") #24
            (Ddl14x,Ddl14y)=self.immobilisePoint(sketch_i, Pt14, "Ep"+I+"i4") #26
    #       On calcul les points sur le profil d'épaisseur intrados
            Discretize.Discretization(fpi, (App.ActiveDocument.getObject("skLoiEpaisseur"+I+"i"),"Edge1"))
            fpi.ParameterLast=1.
            fpi.Algorithm="Number"
            fpi.Number=fp.Npts
            # Discretize.ViewProviderDisc(fpi.ViewObject)
            # fpi.ViewObject.PointSize = 3
            fpi.recompute()
    #       On interpole les points pour qu'ils correspondent à la coordonnée s du plan meridien
            sX=[]
        #   fpis est comme fpi mais avec une distribution suivant s du plan méridien
            fpis = App.ActiveDocument.addObject("Part::FeaturePython","LoiEpaisseur"+I+"is")
            docPlanEpaisseur.addObject(fpis)
            iLast=EpLastIn.Points[i].y
            DiscEp_s(fpis,fpi, fp.Npts, iLast)
            ViewProviderDisc(fpis.ViewObject)
            fpis.ViewObject.PointSize = 3 
            if fp.preNfilets > 0 :fpis.Visibility=App.ActiveDocument.getObject('LoiEpaisseur'+str(i)+'is').Visibility
            debug('fpis.Points')
            debug(fpis.Points)
        debug('sketchDiscEpaisseur - fin')
        return
    def modifEpaisseur(self,fp):
    #
    #   Routine pour mettre à jours les sketchs LoisEpaisseurI à partir des points discrétisés sur les sketchs des pilotes
        debug("modifEpaisseur")
        EpMaxXEx=App.ActiveDocument.getObject("EpMaxXEx")
        EpMaxXIn=App.ActiveDocument.getObject("EpMaxXIn")
        EpMaxYEx=App.ActiveDocument.getObject("EpMaxYEx")
        EpMaxYIn=App.ActiveDocument.getObject("EpMaxYIn")
        EpInflexEx=App.ActiveDocument.getObject("EpInflexEx")
        EpInflexIn=App.ActiveDocument.getObject("EpInflexIn")
        EpLastEx=App.ActiveDocument.getObject("EpLastEx")
        EpLastIn=App.ActiveDocument.getObject("EpLastIn")
        for i in range(fp.Nfilets):
            I=str(i+1)
            sketch_e=App.ActiveDocument.getObject("skLoiEpaisseur"+I+"e")
            sketch_i=App.ActiveDocument.getObject("skLoiEpaisseur"+I+"i")
            fpes=App.ActiveDocument.getObject("LoiEpaisseur"+I+"es")
            fpis=App.ActiveDocument.getObject("LoiEpaisseur"+I+"is")
#
            sketch_e.setDatum(21,App.Units.Quantity(str(EpMaxYEx.Points[i].y))) 
            sketch_e.setDatum(22,App.Units.Quantity(str(EpMaxXEx.Points[i].y)))
            sketch_e.setDatum(23,App.Units.Quantity(str(EpMaxYEx.Points[i].y)))
            sketch_e.setDatum(24,App.Units.Quantity(str(EpInflexEx.Points[i].y)))
            sketch_i.setDatum(21,App.Units.Quantity(str(-EpMaxYIn.Points[i].y)))
            sketch_i.setDatum(22,App.Units.Quantity(str(EpMaxXIn.Points[i].y)))
            sketch_i.setDatum(23,App.Units.Quantity(str(-EpMaxYIn.Points[i].y)))
            sketch_i.setDatum(24,App.Units.Quantity(str(EpInflexIn.Points[i].y)))
            fpes.Last=EpLastEx.Points[i].y
            fpis.Last=EpLastIn.Points[i].y
        App.ActiveDocument.recompute()
        debug("modifEpaisseur - fin")
        return
    def sauveEpaisseur(self,fp):
        debug('sauveEpaisseur')
        # Sauve dans Parametres les contraintes des sketch du plan Epaisseur après une modification par l'usager
        skEpMaxXEx=App.ActiveDocument.getObject("skEpMaxXEx") 
        skEpMaxXIn=App.ActiveDocument.getObject("skEpMaxXIn")
        skEpMaxYEx=App.ActiveDocument.getObject("skEpMaxYEx")
        skEpMaxYIn=App.ActiveDocument.getObject("skEpMaxYIn")
        skEpInflexEx=App.ActiveDocument.getObject("skEpInflexEx")
        skEpInflexIn=App.ActiveDocument.getObject("skEpInflexIn")
        skEpLastEx=App.ActiveDocument.getObject("skEpLastEx")
        skEpLastIn=App.ActiveDocument.getObject("skEpLastIn")
        LoiEpaisseur=[]
    #   (t,ÉpaisseurMaxXExtrados, r)
        for i in range(0,8,2):LoiEpaisseur.append(App.Vector(skEpMaxXEx.Constraints[i].Value,skEpMaxXEx.Constraints[i+1].Value,100.))
    #   (t,ÉpaisseurMaxYExtrados, r)
        for i in range(0,8,2):LoiEpaisseur.append(App.Vector(skEpMaxYEx.Constraints[i].Value,skEpMaxYEx.Constraints[i+1].Value,100.))    
    #   (t,ÉpaisseurInflexionExtrados)
        for i in range(0,8,2):LoiEpaisseur.append(App.Vector(skEpInflexEx.Constraints[i].Value,skEpInflexEx.Constraints[i+1].Value,100.))
    #   (t,ÉpaisseurLastExtrados)
        for i in range(0,8,2):LoiEpaisseur.append(App.Vector(skEpLastEx.Constraints[i].Value,skEpLastEx.Constraints[i+1].Value,100.))
    #   (t,ÉpaisseurMaxXIntrados, r)
        for i in range(0,8,2):LoiEpaisseur.append(App.Vector(skEpMaxXIn.Constraints[i].Value,skEpMaxXIn.Constraints[i+1].Value,100.))
    #   (t,ÉpaisseurMaxYIntrados, r)
        for i in range(0,8,2):LoiEpaisseur.append(App.Vector(skEpMaxYIn.Constraints[i].Value,skEpMaxYIn.Constraints[i+1].Value,100.))    
    #   (t,ÉpaisseurInflexionIntrados)
        for i in range(0,8,2):LoiEpaisseur.append(App.Vector(skEpInflexIn.Constraints[i].Value,skEpInflexIn.Constraints[i+1].Value,100.))    
    #   (t,ÉpaisseurLastIntrados)
        for i in range(0,8,2):LoiEpaisseur.append(App.Vector(skEpLastIn.Constraints[i].Value,skEpLastIn.Constraints[i+1].Value,100.))
        fp.Epaisseur=LoiEpaisseur
        App.ActiveDocument.recompute()
        debug('sauveEpaisseur - fin')
        return
    def epaisseurBS(self,sketch,Pt0,Pt1,Pt2,Pt3,Pt4):
    #
    #   Création d'une BSpline de degré 3 dans le plan Epaisseur
    #   Chaque point est défini par sa géométrie dans le sketch à l'indice Vx
    #
    #   Coordonnées des extrémités
        debug("epaisseurBS")
        Geo=sketch.Geometry
        v0=App.Vector(Geo[Pt0].X,Geo[Pt0].Y,0)
        v1=App.Vector(Geo[Pt1].X,Geo[Pt1].Y,0)
        v2=App.Vector(Geo[Pt2].X,Geo[Pt2].Y,0)
        v3=App.Vector(Geo[Pt3].X,Geo[Pt3].Y,0)
        v4=App.Vector(Geo[Pt4].X,Geo[Pt4].Y,0)
        r0=100.
        r1=100.
        r2=100.
        r3=100.
        r4=100.
        debug('v0= '+str(v0))
        debug('v1= '+str(v1))
        debug('v2= '+str(v2))
        debug('v3= '+str(v3))
        debug('v4= '+str(v4))
    #
    #   Les pôles du bspline
    #
        C0=sketch.addGeometry(Part.Circle(v0,App.Vector(0,0,1),r0),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C0,3,Pt0,1))
        sketch.addConstraint(Sketcher.Constraint('Radius',C0,r0)) 
    #    
        C1=sketch.addGeometry(Part.Circle(v1,App.Vector(0,0,1),r1),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C1,3,Pt1,1))
        sketch.addConstraint(Sketcher.Constraint('Radius',C1,r1))
    #    
        C2=sketch.addGeometry(Part.Circle(v2,App.Vector(0,0,1),r2),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C2,3,Pt2,1))
        sketch.addConstraint(Sketcher.Constraint('Radius',C2,r2))
    #    
        C3=sketch.addGeometry(Part.Circle(v3,App.Vector(0,0,1),r3),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C3,3,Pt3,1))
        sketch.addConstraint(Sketcher.Constraint('Radius',C3,r3))
    #    
        C4=sketch.addGeometry(Part.Circle(v4,App.Vector(0,0,1),r4),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C4,3,Pt4,1))
        sketch.addConstraint(Sketcher.Constraint('Radius',C4,r4))
    #
        BS=sketch.addGeometry(Part.BSplineCurve([v0,v1,v2,v3,v4],None,None,False,3,None,False),False)
       
    #
        conList1 = []
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C0,4,BS,0))
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C1,4,BS,1))
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C2,4,BS,2))
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C3,4,BS,3))
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C4,4,BS,4))
        sketch.addConstraint(conList1)
        sketch.exposeInternalGeometry(BS)
    #    
        debug("epaisseurBS - fin")
        
        return (BS)
#
#
#       Plan de la cascade
#
#
    def initCascade(self,fp):
        debug("initCascade") 
    #
    #   Routine pour créer les splines à 4 pôles(0,1,2,3) qui pilotent pour l'âme
    #   les variables évolutant selon la coordonnée normalisée t de la ceinture au plafond :
    #  
    #   sketchTheta : position angulaire à l'entrée et à la sortie
    #   sketchAlpha : angle d'incidence à l'entrée et à la sortie
    #   sketchPoids : poids (rayon) d'influence des pôles à l'entrée et à la sortie
    #   sketchLong  : longueur entre les pôles d'entrée et de sortie ( coord. norm. s)
        LoiAlpha=[]
        sketchTheta_entree=App.ActiveDocument.addObject('Sketcher::SketchObject','skTheta_entree')
        sketchTheta_entree.Placement = App.Placement(App.Vector(0.000000,0.000000,0.000000),App.Rotation(0.5,0.5,0.5,0.5))
        sketchTheta_sortie=App.ActiveDocument.addObject('Sketcher::SketchObject','skTheta_sortie')
        sketchTheta_sortie.Placement = App.Placement(App.Vector(0.000000,0.000000,0.000000),App.Rotation(0.5,0.5,0.5,0.5))
        sketchAlpha_entree=App.ActiveDocument.addObject('Sketcher::SketchObject','skAlpha_entree')
        sketchAlpha_entree.Placement = App.Placement(App.Vector(0.000000,0.000000,0.000000),App.Rotation(0.5,0.5,0.5,0.5))
        sketchAlpha_sortie=App.ActiveDocument.addObject('Sketcher::SketchObject','skAlpha_sortie')
        sketchAlpha_sortie.Placement = App.Placement(App.Vector(0.000000,0.000000,0.000000),App.Rotation(0.5,0.5,0.5,0.5))
        sketchPoids_entree=App.ActiveDocument.addObject('Sketcher::SketchObject','skPoids_entree')
        sketchPoids_entree.Placement = App.Placement(App.Vector(0.000000,0.000000,0.000000),App.Rotation(0.5,0.5,0.5,0.5))
        sketchPoids_sortie=App.ActiveDocument.addObject('Sketcher::SketchObject','skPoids_sortie')
        sketchPoids_sortie.Placement = App.Placement(App.Vector(0.000000,0.000000,0.000000),App.Rotation(0.5,0.5,0.5,0.5))
        sketchLong_entree=App.ActiveDocument.addObject('Sketcher::SketchObject','skLong_entree')
        sketchLong_entree.Placement = App.Placement(App.Vector(0.000000,0.000000,0.000000),App.Rotation(0.5,0.5,0.5,0.5))
        sketchLong_sortie=App.ActiveDocument.addObject('Sketcher::SketchObject','skLong_sortie')
        sketchLong_sortie.Placement = App.Placement(App.Vector(0.000000,0.000000,0.000000),App.Rotation(0.5,0.5,0.5,0.5))
        Feuil= App.ActiveDocument.getObject("Tableau_pilote")
        docPilote = App.ActiveDocument.getObject("Pilote")
        docPilote.addObject(sketchTheta_entree)
        docPilote.addObject(sketchTheta_sortie)
        docPilote.addObject(sketchAlpha_entree)
        docPilote.addObject(sketchAlpha_sortie)
        docPilote.addObject(sketchPoids_entree)
        docPilote.addObject(sketchPoids_sortie)
        docPilote.addObject(sketchLong_entree)
        docPilote.addObject(sketchLong_sortie)
    #   Pour la représentation dans FreeCAD t varie de 0 à 100 mm de la ceinture au plafond.
        t0=Feuil.B1*100.
        t1=Feuil.C1*100.
        t2=Feuil.D1*100.
        t3=Feuil.E1*100.
    #   Alpha (angle incident) contient les lois selon t qui définissent les pôles de la cascade indépendamment du nombbre de filet.
    #   Il y a 4 Bspline du bord d'attaque au bord de fuite selon s eux-mêmes définis chacun par 4 poles. Donc 16 poles.
    #   Ces splines sont définis dans l'espace (t,Alpha) par les deux points d'extrémité entrée et sortie. 
    #   Pour la ceinture (t=0) et le plafond (t=100) on a 2 vecteurs  (alpha1, w1, L1) et (alpha2, w2, L2)  
    #   1 indice pour entree
    #   2 indice pour sortie
        nseg=fp.Npts-1
    #
    #   Transfert du tableur à LoiAlpha pour ensuite sauvegarder dans Parametres (fp.Alpha) 
    #   LoiAlpha et fp.Alpha sont des noms génériques qui contiennent toutes les données (theta, alpha, poids et long)
    #
        LoiAlpha.append(App.Vector(Feuil.B3,Feuil.B4,t0)) #Ceinture (theta_entree, theta_sortie, t)
        LoiAlpha.append(App.Vector(Feuil.C3,Feuil.C4,t1))
        LoiAlpha.append(App.Vector(Feuil.D3,Feuil.D4,t2))
        LoiAlpha.append(App.Vector(Feuil.E3,Feuil.E4,t3))
        LoiAlpha.append(App.Vector(Feuil.B5,Feuil.B8,Feuil.B10))
        LoiAlpha.append(App.Vector(Feuil.B6,Feuil.B9,Feuil.B11))
        LoiAlpha.append(App.Vector(Feuil.C5,Feuil.C8,Feuil.C10))
        LoiAlpha.append(App.Vector(Feuil.C6,Feuil.C9,Feuil.C11))
        LoiAlpha.append(App.Vector(Feuil.D5,Feuil.D8,Feuil.D10))
        LoiAlpha.append(App.Vector(Feuil.D6,Feuil.D9,Feuil.D11))
        LoiAlpha.append(App.Vector(Feuil.E5,Feuil.E8,Feuil.E10))
        LoiAlpha.append(App.Vector(Feuil.E6,Feuil.E9,Feuil.E11))
    #   Sauvegarde du résultat
        fp.addProperty("App::PropertyVectorList","Alpha","Plan 3 - Cascade","Distribution des positions angulaires et angles").Alpha=LoiAlpha
        fp.setEditorMode("Alpha",1)
    #
    #
    #   Construction des sketchs et des bsplines entrée et sortie pour tous les pilotes.
    #
    #
    #   Loi de theta 
    #
    #   au bord d'attaque (t,theta,0)
        t0=LoiAlpha[0].z
        t1=LoiAlpha[1].z
        t2=LoiAlpha[2].z
        t3=LoiAlpha[3].z
        Te0=sketchTheta_entree.addGeometry(Part.Point(App.Vector(t0,LoiAlpha[0].x,0)))
        Te1=sketchTheta_entree.addGeometry(Part.Point(App.Vector(t1,LoiAlpha[1].x,0)))
        Te2=sketchTheta_entree.addGeometry(Part.Point(App.Vector(t2,LoiAlpha[2].x,0)))
        Te3=sketchTheta_entree.addGeometry(Part.Point(App.Vector(t3,LoiAlpha[3].x,0)))
        (Te0x,Te0y)=self.immobilisePoint(sketchTheta_entree, Te0, "Te0")
        (Te1x,Te1y)=self.immobilisePoint(sketchTheta_entree, Te1, "Te1")
        (Te2x,Te2y)=self.immobilisePoint(sketchTheta_entree, Te2, "Te2")
        (Te3x,Te3y)=self.immobilisePoint(sketchTheta_entree, Te3, "Te3")
    #   au bord de fuite
        Ts0=sketchTheta_sortie.addGeometry(Part.Point(App.Vector(t0,LoiAlpha[0].y,0)))
        Ts1=sketchTheta_sortie.addGeometry(Part.Point(App.Vector(t1,LoiAlpha[1].y,0)))
        Ts2=sketchTheta_sortie.addGeometry(Part.Point(App.Vector(t2,LoiAlpha[2].y,0)))
        Ts3=sketchTheta_sortie.addGeometry(Part.Point(App.Vector(t3,LoiAlpha[3].y,0)))
        (Ts0x,Ts0y)=self.immobilisePoint(sketchTheta_sortie, Ts0, "Ts0")
        (Ts1x,Ts1y)=self.immobilisePoint(sketchTheta_sortie, Ts1, "Ts1")
        (Ts2x,Ts2y)=self.immobilisePoint(sketchTheta_sortie, Ts2, "Ts2")
        (Ts3x,Ts3y)=self.immobilisePoint(sketchTheta_sortie, Ts3, "Ts3")
    #   Construction des Bspline
        (BSte,ceinte,plfte)=self.planBS(sketchTheta_entree,Te0,Te1,Te2,Te3)   # BORD D'ATTAQUE
        (BSts,ceints,plfts)=self.planBS(sketchTheta_sortie,Ts0,Ts1,Ts2,Ts3)   # BORD DE FUITE       
#        App.ActiveDocument.recompute()
    #
    #   Loi d'alpha 
    #
    #   au bord d'attaque
        Ae0=sketchAlpha_entree.addGeometry(Part.Point(App.Vector(t0,LoiAlpha[4].x,0)))
        Ae1=sketchAlpha_entree.addGeometry(Part.Point(App.Vector(t1,LoiAlpha[6].x,0)))
        Ae2=sketchAlpha_entree.addGeometry(Part.Point(App.Vector(t2,LoiAlpha[8].x,0)))
        Ae3=sketchAlpha_entree.addGeometry(Part.Point(App.Vector(t3,LoiAlpha[10].x,0)))
        (Ae0x,Ae0y)=self.immobilisePoint(sketchAlpha_entree, Ae0, "Ae0")
        (Ae1x,Ae1y)=self.immobilisePoint(sketchAlpha_entree, Ae1, "Ae1")
        (Ae2x,Ae2y)=self.immobilisePoint(sketchAlpha_entree, Ae2, "Ae2")
        (Ae3x,Ae3y)=self.immobilisePoint(sketchAlpha_entree, Ae3, "Ae3")
    #   au bord de fuite
        As0=sketchAlpha_sortie.addGeometry(Part.Point(App.Vector(t0,LoiAlpha[5].x,0)))
        As1=sketchAlpha_sortie.addGeometry(Part.Point(App.Vector(t1,LoiAlpha[7].x,0)))
        As2=sketchAlpha_sortie.addGeometry(Part.Point(App.Vector(t2,LoiAlpha[9].x,0)))
        As3=sketchAlpha_sortie.addGeometry(Part.Point(App.Vector(t3,LoiAlpha[11].x,0)))
        (As0x,As0y)=self.immobilisePoint(sketchAlpha_sortie, As0, "As0")
        (As1x,As1y)=self.immobilisePoint(sketchAlpha_sortie, As1, "As1")
        (As2x,As2y)=self.immobilisePoint(sketchAlpha_sortie, As2, "As2")
        (As3x,As3y)=self.immobilisePoint(sketchAlpha_sortie, As3, "As3")
    #   Construction des Bspline
        (BSae,ceinae,plfae)=self.planBS(sketchAlpha_entree,Ae0,Ae1,Ae2,Ae3)   # BORD D'ATTAQUE
        (BSas,ceinas,plfas)=self.planBS(sketchAlpha_sortie,As0,As1,As2,As3)   # BORD DE FUITE       
        App.ActiveDocument.recompute()
    #
    #   Loi de poids 
    #
    #   au bord d'attaque
        We0=sketchPoids_entree.addGeometry(Part.Point(App.Vector(t0,LoiAlpha[4].y,0)))
        We1=sketchPoids_entree.addGeometry(Part.Point(App.Vector(t1,LoiAlpha[6].y,0)))
        We2=sketchPoids_entree.addGeometry(Part.Point(App.Vector(t2,LoiAlpha[8].y,0)))
        We3=sketchPoids_entree.addGeometry(Part.Point(App.Vector(t3,LoiAlpha[10].y,0)))
        (We0x,We0y)=self.immobilisePoint(sketchPoids_entree, We0, "We0")
        (We1x,We1y)=self.immobilisePoint(sketchPoids_entree, We1, "We1")
        (We2x,We2y)=self.immobilisePoint(sketchPoids_entree, We2, "We2")
        (We3x,We3y)=self.immobilisePoint(sketchPoids_entree, We3, "We3")
    #   au bord de fuite 
        Ws0=sketchPoids_sortie.addGeometry(Part.Point(App.Vector(t0,LoiAlpha[5].y,0)))
        Ws1=sketchPoids_sortie.addGeometry(Part.Point(App.Vector(t1,LoiAlpha[7].y,0)))
        Ws2=sketchPoids_sortie.addGeometry(Part.Point(App.Vector(t2,LoiAlpha[9].y,0)))
        Ws3=sketchPoids_sortie.addGeometry(Part.Point(App.Vector(t3,LoiAlpha[11].y,0)))
        (Ws0x,Ws0y)=self.immobilisePoint(sketchPoids_sortie, Ws0, "Ws0")
        (Ws1x,Ws1y)=self.immobilisePoint(sketchPoids_sortie, Ws1, "Ws1")
        (Ws2x,Ws2y)=self.immobilisePoint(sketchPoids_sortie, Ws2, "Ws2")
        (Ws3x,Ws3y)=self.immobilisePoint(sketchPoids_sortie, Ws3, "Ws3")
    #   Construction des Bspline
        (BSWe,ceinwe,plfwe)=self.planBS(sketchPoids_entree,We0,We1,We2,We3)   # BORD D'ATTAQUE
        App.ActiveDocument.recompute()
        (BSWs,ceinws,plfws)=self.planBS(sketchPoids_sortie,Ws0,Ws1,Ws2,Ws3)   # BORD DE FUITE       
        App.ActiveDocument.recompute()
    #
    #   Loi des Longueurs 
    #
    #   au bord d'attaque
        Le0=sketchLong_entree.addGeometry(Part.Point(App.Vector(t0,LoiAlpha[4].z,0)))
        Le1=sketchLong_entree.addGeometry(Part.Point(App.Vector(t1,LoiAlpha[6].z,0)))
        Le2=sketchLong_entree.addGeometry(Part.Point(App.Vector(t2,LoiAlpha[8].z,0)))
        Le3=sketchLong_entree.addGeometry(Part.Point(App.Vector(t3,LoiAlpha[10].z,0)))
        (Le0x,Le0y)=self.immobilisePoint(sketchLong_entree, Le0, "Le0")
        (Le1x,Le1y)=self.immobilisePoint(sketchLong_entree, Le1, "Le1")
        (Le2x,Le2y)=self.immobilisePoint(sketchLong_entree, Le2, "Le2")
        (Le3x,Le3y)=self.immobilisePoint(sketchLong_entree, Le3, "Le3")
    #   au bord de fuite 
        Ls0=sketchLong_sortie.addGeometry(Part.Point(App.Vector(t0,LoiAlpha[5].z,0)))
        Ls1=sketchLong_sortie.addGeometry(Part.Point(App.Vector(t1,LoiAlpha[7].z,0)))
        Ls2=sketchLong_sortie.addGeometry(Part.Point(App.Vector(t2,LoiAlpha[9].z,0)))
        Ls3=sketchLong_sortie.addGeometry(Part.Point(App.Vector(t3,LoiAlpha[11].z,0)))
        (Ls0x,Ls0y)=self.immobilisePoint(sketchLong_sortie, Ls0, "Ls0")
        (Ls1x,Ls1y)=self.immobilisePoint(sketchLong_sortie, Ls1, "Ls1")
        (Ls2x,Ls2y)=self.immobilisePoint(sketchLong_sortie, Ls2, "Ls2")
        (Ls3x,Ls3y)=self.immobilisePoint(sketchLong_sortie, Ls3, "Ls3")
    #   Construction des Bspline
        (BSLe,ceinle,plfle)=self.planBS(sketchLong_entree,Le0,Le1,Le2,Le3)   # BORD D'ATTAQUE
        App.ActiveDocument.recompute()
        (BSLs,ceinls,plfls)=self.planBS(sketchLong_sortie,Ls0,Ls1,Ls2,Ls3)   # BORD DE FUITE       
        # sketchTheta_entree.recompute()
        # sketchTheta_sortie.recompute()
        # sketchAlpha_entree.recompute()
        # sketchAlpha_sortie.recompute()
        # sketchPoids_entree.recompute()
        # sketchPoids_sortie.recompute()
        # sketchLong_entree.recompute()
        # sketchLong_sortie.recompute()
        App.ActiveDocument.recompute()
        debug('initCascade - fin')
        return
    def traceCascade(self,fp):
        debug('traceCascade')
    #    
        docPilote = App.ActiveDocument.getObject("Pilote")
    #   Creation des profils dans les plan des longueurs et de casacade pour éventuellement être assemblés pour former le voile en 3D
    #    
        docPlanCascade = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Plan_Cascade")
        docPlanLongueurs = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Plan_Longueurs")
    #
    #   Discretisation des pilotes Bspine pour chaque filet
    #
        #   Loi de theta 
        #
        Te = App.ActiveDocument.addObject("Part::FeaturePython","Theta_entree")
        docPilote.addObject(Te)
        Discretize.Discretization(Te, (App.ActiveDocument.getObject("skTheta_entree"),"Edge1"))
        Te.Number=fp.Nfilets
        Discretize.ViewProviderDisc(Te.ViewObject)
        Te.ViewObject.PointSize = 3
        Te.recompute()
        Ts = App.ActiveDocument.addObject("Part::FeaturePython","Theta_sortie")
        docPilote.addObject(Ts)        
        Discretize.Discretization(Ts, (App.ActiveDocument.getObject("skTheta_sortie"),"Edge1"))
        Ts.Number=fp.Nfilets
        Discretize.ViewProviderDisc(Ts.ViewObject)
        Ts.ViewObject.PointSize = 3
        Ts.recompute()
        #
        #   Loi de alpha 
        #
        Ae = App.ActiveDocument.addObject("Part::FeaturePython","Alpha_entree")
        docPilote.addObject(Ae)
        Discretize.Discretization(Ae, (App.ActiveDocument.getObject("skAlpha_entree"),"Edge1"))
        Ae.Number=fp.Nfilets
        Discretize.ViewProviderDisc(Ae.ViewObject)
        Ae.ViewObject.PointSize = 3
        Ae.recompute()
        As = App.ActiveDocument.addObject("Part::FeaturePython","Alpha_sortie")
        docPilote.addObject(As)
        Discretize.Discretization(As, (App.ActiveDocument.getObject("skAlpha_sortie"),"Edge1"))
        As.Number=fp.Nfilets
        Discretize.ViewProviderDisc(As.ViewObject)
        As.ViewObject.PointSize = 3
        As.recompute()
        #
        #   Loi de poids 
        #
        We = App.ActiveDocument.addObject("Part::FeaturePython","Poids_entree")
        docPilote.addObject(We)
        Discretize.Discretization(We, (App.ActiveDocument.getObject("skPoids_entree"),"Edge1"))
        We.Number=fp.Nfilets
        Discretize.ViewProviderDisc(We.ViewObject)
        We.ViewObject.PointSize = 3
        We.recompute()
        Ws = App.ActiveDocument.addObject("Part::FeaturePython","Poids_sortie")
        docPilote.addObject(Ws)
        Discretize.Discretization(Ws, (App.ActiveDocument.getObject("skPoids_sortie"),"Edge1"))
        Ws.Number=fp.Nfilets
        Discretize.ViewProviderDisc(Ws.ViewObject)
        Ws.ViewObject.PointSize = 3
        Ws.recompute()
        #
        #   Loi des Longueurs 
        #
        #   au bord d'attaque
        Le = App.ActiveDocument.addObject("Part::FeaturePython","Long_entree")
        docPilote.addObject(Le)
        Discretize.Discretization(Le, (App.ActiveDocument.getObject("skLong_entree"),"Edge1"))
        Le.Number=fp.Nfilets
        Discretize.ViewProviderDisc(Le.ViewObject)
        Le.ViewObject.PointSize = 3
        Le.recompute()
        Ls = App.ActiveDocument.addObject("Part::FeaturePython","Long_sortie")
        docPilote.addObject(Ls)
        Discretize.Discretization(Ls, (App.ActiveDocument.getObject("skLong_sortie"),"Edge1"))
        Ls.Number=fp.Nfilets
        Discretize.ViewProviderDisc(Ls.ViewObject)
        Ls.ViewObject.PointSize = 3
        Ls.recompute()
        self.sketchDiscCascade(fp, Te, Ts, Ae, As, We, Ws, Le, Ls)
        App.ActiveDocument.recompute()
        debug('traceCascade - fin')
        return
    def sketchDiscCascade(self,fp, Te, Ts, Ae, As, We, Ws, Le, Ls):
        debug("sketchDiscCascade")
        docPlanCascade = App.ActiveDocument.getObject("Plan_Cascade")
        docPlanLongueurs = App.ActiveDocument.getObject("Plan_Longueurs")
    #
    #       Creation de la géométrie incluant un sketch pour chaque filet de Cascade
    #
        debug('fp.preNfilets= '+str(fp.preNfilets))
        self.modifCascade(fp,fp.preNfilets)
        debug('fp.Nfilets= '+str(fp.Nfilets))
        for i in range(fp.preNfilets,fp.Nfilets):   #FiletMeridien in FiletsMeridien:   
            I=str(i+1)
            debug('I= '+I+'i= '+str(i))
            debug(str(i)+" "+I)
        #
        #   Création fp fpAa qui contient l'information du Discretized_Edge du voile 2D
        #
            fpAa = App.ActiveDocument.addObject("Part::FeaturePython","FiletCAa"+I)
            docPlanCascade.addObject(fpAa)
        #   Calcul de Usmax pour chaque filet qui dépend de Npts    
            Usmax=self.CascadeUsmax(i)
            debug('Usmax= '+str(Usmax))
        # Les informations pour les points du BSpline pour Cascade
            fpAa.addProperty("App::PropertyVector","a0","Contraintes","Position(u,v)").a0=App.Vector(0,fp.Sens*1000.*math.radians(Te.Points[i].z),0)
            fpAa.addProperty("App::PropertyVector","a1","Contraintes","Position(alpha,poids,long)").a1=App.Vector(fp.Sens*Ae.Points[i].z, We.Points[i].z, Le.Points[i].z)
            fpAa.addProperty("App::PropertyVector","a2","Contraintes","Position(alpha,poids,long)").a2=App.Vector(fp.Sens*As.Points[i].z, Ws.Points[i].z, Ls.Points[i].z)
            fpAa.addProperty("App::PropertyVector","a3","Contraintes","Position(u,v)").a3=App.Vector(Usmax,fp.Sens*1000.*math.radians(Ts.Points[i].z),0)
#           sketchA pour contenir le Bspline de la cascade 
            sketchA=self.CascadeSketch(fpAa,I)
            if fp.preNfilets > 0 :sketchA.Visibility=App.ActiveDocument.getObject('Cascade'+str(i)).Visibility
            docPlanCascade.addObject(sketchA)
        #
        #   Discretisation du filet voile 2D de la cascade A
        #
            Discretize.Discretization(fpAa, (App.ActiveDocument.getObject("Cascade"+I),"Edge1"))
            fpAa.Number=fp.Npts
            # ViewProviderDisc(fpAa.ViewObject)
            # fpAa.ViewObject.PointSize = 3
            sketchA.recompute()
            fpAa.recompute()
        #   fpAs est comme fpAa mais avec une distribution suivant s du plan méridien
            fpAs = App.ActiveDocument.addObject("Part::FeaturePython","FiletCAs"+I)
            docPlanCascade.addObject(fpAs)
        #   Synchronisation des u,v avec l'abscisse s du plan meridien
            DiscCa_s(fpAs, fpAa, fp.Npts, i)
            ViewProviderDisc(fpAs.ViewObject)
            fpAs.ViewObject.PointSize = 3
            if fp.preNfilets > 0 :fpAs.Visibility=App.ActiveDocument.getObject('FiletCAs'+str(i)).Visibility
            fpAs.recompute()
            App.ActiveDocument.recompute()
            v_s=[]
            for point in fpAs.Points: v_s.append(point.z)
    #   Calcul de la discretisation de la cascade L
    #
    #

        # 
        #   Calcul des points dans le plan des longueurs m-n
        #               âme
            fpLa = App.ActiveDocument.addObject("Part::FeaturePython",'FiletCLa'+I)
            docPlanLongueurs.addObject(fpLa)
            DiscCl_s(fpLa, fpAs, fp.Npts, i)          
            ViewProviderDisc(fpLa.ViewObject)
            fpLa.ViewObject.PointSize = 3
            if fp.preNfilets > 0 :fpLa.Visibility=App.ActiveDocument.getObject('FiletCLa'+str(i)).Visibility

                #       extrados
            fpLe = App.ActiveDocument.addObject("Part::FeaturePython",'FiletCLe'+I)
            docPlanLongueurs.addObject(fpLe)
            DiscCle_s(fpLe, fpAs, fp.Npts, fp.Sens, i)
            ViewProviderDisc(fpLe.ViewObject)
            fpLe.ViewObject.PointSize = 3
            if fp.preNfilets > 0 :fpLe.Visibility=App.ActiveDocument.getObject('FiletCLe'+str(i)).Visibility
                #       intrados
            fpLi = App.ActiveDocument.addObject("Part::FeaturePython",'FiletCLi'+I)
            docPlanLongueurs.addObject(fpLi)
            DiscCli_s(fpLi, fpAs, fp.Npts, fp.Sens, i)
            ViewProviderDisc(fpLi.ViewObject)
            fpLi.ViewObject.PointSize = 3
            if fp.preNfilets > 0 :fpLi.Visibility=App.ActiveDocument.getObject('FiletCLi'+str(i)).Visibility
        #
        #
        # Les informations pour les points discretisés pour Cascade
        #
        #       extrados                
            fpAe = App.ActiveDocument.addObject("Part::FeaturePython","FiletCAe"+I)
#            fpAe.Label="FiletCAe"+I
            docPlanCascade.addObject(fpAe)
            DiscCe_s(fpAe, fpAs, fpLe, fp.Npts, i)
            ViewProviderDisc(fpAe.ViewObject)
            fpAe.ViewObject.PointSize = 3
            if fp.preNfilets > 0 :fpAe.Visibility=App.ActiveDocument.getObject('FiletCAe'+str(i)).Visibility
        #       intrados
            fpAi = App.ActiveDocument.addObject("Part::FeaturePython","FiletCAi"+I)
#            fpAi.Label='FiletCAi'+I           
            docPlanCascade.addObject(fpAi)
            DiscCi_s(fpAi, fpAs, fpLi, fp.Npts, i)
            ViewProviderDisc(fpAi.ViewObject)
            fpAi.ViewObject.PointSize = 3
            if fp.preNfilets > 0 :fpAi.Visibility=App.ActiveDocument.getObject('FiletCAi'+str(i)).Visibility
            i+=1
            I=str(i+1)
#        App.ActiveDocument.recompute()
        debug("sketchDiscCascade - fin")
        return   
    def modifCascade(self,fp,Nfilets):
        debug('modifCascade')
        nseg=fp.Npts - 1
        Theta_entree = App.ActiveDocument.getObject("Theta_entree")
        Theta_sortie = App.ActiveDocument.getObject("Theta_sortie")
        Alpha_entree = App.ActiveDocument.getObject("Alpha_entree")
        Alpha_sortie = App.ActiveDocument.getObject("Alpha_sortie")
        Poids_entree = App.ActiveDocument.getObject("Poids_entree")
        Poids_sortie = App.ActiveDocument.getObject("Poids_sortie")
        Long_entree = App.ActiveDocument.getObject("Long_entree")
        Long_sortie = App.ActiveDocument.getObject("Long_sortie")
        for i in range(Nfilets):     #FiletMeridien in FiletsMeridien:
            I=str(i+1)
            FiletMeridien=App.ActiveDocument.getObject('FiletM'+I)
            debug(FiletMeridien.Name)
#            fpAa = App.ActiveDocument.getObject("FiletCAa"+I)
            #   Calcul de Usmax pour chaque filet qui dépend de Npts    
            Usmax=self.CascadeUsmax(i)
            #   m-à-j des données de "FiletCAa"+I
            fpAa = App.ActiveDocument.getObject("FiletCAa"+I)
            fpAa.a0=App.Vector(0,fp.Sens*1000.*math.radians(Theta_entree.Points[i].z),0)
            debug('fpAs.a..      *******')
            debug(Theta_entree.Points)
            debug(fpAa.a0)
            fpAa.a1=App.Vector(fp.Sens*Alpha_entree.Points[i].z, Poids_entree.Points[i].z, Long_entree.Points[i].z)
            debug(fpAa.a1)
            fpAa.a2=App.Vector(fp.Sens*Alpha_sortie.Points[i].z, Poids_sortie.Points[i].z, Long_sortie.Points[i].z)
            debug(fpAa.a2)
            fpAa.a3=App.Vector(Usmax,fp.Sens*1000.*math.radians(Theta_sortie.Points[i].z),0)
            debug(fpAa.a3)
            fpAa.recompute()
        #   sketchA pour contenir la cascade 
            sketchA=App.ActiveDocument.getObject('Cascade'+I)
            debug(sketchA.Name)
            for j in sketchA.Constraints:
                sketchA.setDatum(3,App.Units.Quantity(str(fpAa.a1.y))) #Poids_entree w1
                sketchA.setDatum(5,App.Units.Quantity(str(fpAa.a2.y)))  #Poids_sortie w2
                sketchA.setDatum(19,App.Units.Quantity(str(fpAa.a0.y))) #Theta_entree  CA1_0y
                sketchA.setDatum(20,App.Units.Quantity(str(fpAa.a1.x)+' deg')) #Alpha_entree 
                sketchA.setDatum(21,App.Units.Quantity(str(fpAa.a1.z))) #Long_entree
                sketchA.setDatum(22,App.Units.Quantity(str(fpAa.a2.x)+' deg')) #Alpha_sortie
                sketchA.setDatum(23,App.Units.Quantity(str(fpAa.a2.z))) #Long_sortie
                sketchA.setDatum(24,App.Units.Quantity(str(fpAa.a3.x))) #u_s(nseg) CA1_3x
                sketchA.setDatum(25,App.Units.Quantity(str(fpAa.a3.y))) #Thet CA1_3y
            sketchA.recompute()
        #   fpAs est comme fpAa mais avec une distribution suivant s du plan méridien
            fpAs = App.ActiveDocument.getObject("FiletCAs"+I)
            fpAs.recompute()
        #    
        # 
        #   Calcul des points dans le plan des longueurs m-n
        #               âme
            fpLa = App.ActiveDocument.getObject('FiletCLa'+I)
            fpLa.recompute()
                #       extrados
            fpLe = App.ActiveDocument.getObject('FiletCLe'+I)
            fpLe.Sens=fp.Sens
            fpLe.recompute()
                #       intrados
            fpLi = App.ActiveDocument.getObject('FiletCLi'+I)
            fpLi.Sens=fp.Sens
            fpLi.recompute()
        #
        #
        # Les informations pour les points discretisés pour Cascade
        #
        #       extrados                
            fpAe = App.ActiveDocument.getObject("FiletCAe"+I)
            fpAe.recompute()
        #       intrados
            fpAi = App.ActiveDocument.getObject("FiletCAi"+I)
            fpAi.recompute()
            i+=1
            I=str(i+1)
        App.ActiveDocument.recompute()
        debug('modifCascade- fin')
        return
    def sauveCascade(self,fp):
    #   Sauve les nouvelles limites du sketchAngles 
        debug('sauveCascade')
        sketchTheta_entree=App.ActiveDocument.skTheta_entree
        sketchTheta_sortie=App.ActiveDocument.skTheta_sortie
        sketchAlpha_entree=App.ActiveDocument.skAlpha_entree
        sketchAlpha_sortie=App.ActiveDocument.skAlpha_sortie
        sketchPoids_entree=App.ActiveDocument.skPoids_entree
        sketchPoids_sortie=App.ActiveDocument.skPoids_sortie
        sketchLong_entree=App.ActiveDocument.skLong_entree
        sketchLong_sortie=App.ActiveDocument.skLong_sortie
#       Sauvegarde du résultat
#
#       fp.Alpha ou LoiAlpha
#
#       1   B3  B4  B1
#       2   C3  C4  C1
#       3   D3  D4  D1
#       4   E3  E4  E1
#       5   B5  B8  B10
#       6   B6  B9  B11
#       7   C5  C8  C10
#       8   C6  C9  C11
#       9   D5  D8  D10
#       10  D6  D9  D11
#       11  E5  E8  E10
#       12  R6  E9  E11
#
        LoiAlpha=[]
        for i in range(0,8,2): LoiAlpha.append(App.Vector(sketchTheta_entree.getDatum(i+1),sketchTheta_sortie.getDatum(i+1),sketchTheta_entree.getDatum(i)))
        for i in range(0,8,2) : 
            LoiAlpha.append(App.Vector(sketchAlpha_entree.getDatum(i+1),sketchPoids_entree.getDatum(i+1),sketchLong_entree.getDatum(i+1)))
            LoiAlpha.append(App.Vector(sketchAlpha_sortie.getDatum(i+1),sketchPoids_sortie.getDatum(i+1),sketchLong_sortie.getDatum(i+1)))
        fp.Alpha=LoiAlpha
        App.ActiveDocument.recompute()
        debug('sauveCascade - fin')
        return        
    def planBSCascade(self,sketch,Pt0,Pt1,Pt2,Pt3,r0,r1,r2,r3):
    #
    #   Création d'une BSpline de degré 3 dans le plan Meridien
    #   Chaque point est défini par sa géométrie dans le sketch à l'indice Vx
    #
    #   Coordonnées des extrémités
        Geo=sketch.Geometry
        v0=App.Vector(Geo[Pt0].X,Geo[Pt0].Y,0)
        v1=App.Vector(Geo[Pt1].X,Geo[Pt1].Y,0)
        v2=App.Vector(Geo[Pt2].X,Geo[Pt2].Y,0)
        v3=App.Vector(Geo[Pt3].X,Geo[Pt3].Y,0)
    #
    #   Le bspline
    #
        dx=Geo[Pt3].X-Geo[Pt0].X
        dy=Geo[Pt3].Y-Geo[Pt0].Y
    #   Poids local pour les pts de contrôle
        rayon=0.1*math.sqrt(dx*dx+dy*dy)
    #
        C1=sketch.addGeometry(Part.Circle(v0,App.Vector(0,0,1),r0),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C1,3,Pt0,1))
        sketch.addConstraint(Sketcher.Constraint('Radius',C1,r0))
        #
        C2=sketch.addGeometry(Part.Circle(v1,App.Vector(0,0,1),r1),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C2,3,Pt1,1))
        sketch.addConstraint(Sketcher.Constraint('Radius',C2,r1))
        #
        C3=sketch.addGeometry(Part.Circle(v2,App.Vector(0,0,1),r2),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C3,3,Pt2,1))
        sketch.addConstraint(Sketcher.Constraint('Radius',C3,r2))
        #
        C4=sketch.addGeometry(Part.Circle(v3,App.Vector(0,0,1),r3),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C4,3,Pt3,1))
        sketch.addConstraint(Sketcher.Constraint('Radius',C4,r3))
        #
        BS=sketch.addGeometry(Part.BSplineCurve([v0,v1,v2,v3],None,None,False,3,None,False),False)
        l1=Part.LineSegment(v0,v1)
        L1=sketch.addGeometry(l1,True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C1,3,L1,1))
        sketch.addConstraint(Sketcher.Constraint('Coincident',C2,3,L1,2))
        l2=Part.LineSegment(v2,v3)
        L2=sketch.addGeometry(l2,True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C3,3,L2,1))
        sketch.addConstraint(Sketcher.Constraint('Coincident',C4,3,L2,2))
        conList = []
        conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C1,3,BS,0))
        conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C2,3,BS,1))
        conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C3,3,BS,2))
        conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C4,3,BS,3))
        sketch.addConstraint(conList)
        sketch.exposeInternalGeometry(BS)
        sketch.recompute()
        return (BS,L1,L2)
    def CascadeUsmax(self,i):
        debug('CascadeUsMax')
    #
    #   Calcul des coordonnées (m,n)à partir de (u,v) de la discretisation
    # 
    #
        I=str(i+1)
        FiletMeridien=App.ActiveDocument.getObject('FiletM'+I)
        nseg=FiletMeridien.Number-1
        pj=FiletMeridien.Points[0]
        debug("FiletMeridien.Points= "+str(FiletMeridien.Points))
    #   l'indice _s correspond à la coordonnée curviligne dans le plan méridien
        m_n=App.ActiveDocument.getObject("IsoCurve").Shape.Edges[i].Length
        debug("m_n= "+str(m_n))
        dm=m_n/nseg
        u=0
        for pj in FiletMeridien.Points[1:]:
            u+=1000.*dm/pj.x
        debug('CascadeUsMax - fin')
        return (u)
    def CascadeSketch(self,fpAa,I):
        debug('CascadeSketch')
        sketchA=App.ActiveDocument.addObject('Sketcher::SketchObject','Cascade'+I)
        debug('Cascade '+I)
        sketchA.Placement = App.Placement(App.Vector(0.000000,0.000000,0.000000),App.Rotation(0.5,0.5,0.5,0.5))
 #       sketchA.Label='Cascade'+I 
    #   Calcul des pôles de la Bspline de la Cascade
        pt0=Part.Point(fpAa.a0)
        Pt0=sketchA.addGeometry(pt0)
    # On calcule les coordonnées cartésienne pour les points 1 et 2
        x1=fpAa.a0.x + fpAa.a1.z * math.cos(math.radians(fpAa.a1.x)) #u
        y1=fpAa.a0.y + fpAa.a1.z * math.sin(math.radians(fpAa.a1.x)) #v 
        r1=fpAa.a1.y
        a1=App.Vector(x1,y1,r1)
        pt1=Part.Point(a1)
        Pt1=sketchA.addGeometry(pt1)
        x2=fpAa.a3.x - fpAa.a2.z * math.cos(math.radians(fpAa.a2.x))
        y2=fpAa.a3.y - fpAa.a2.z * math.sin(math.radians(fpAa.a2.x))
        r2=fpAa.a2.y
        a2=App.Vector(x2,y2,r2)
        pt2=Part.Point(a2)
        Pt2=sketchA.addGeometry(pt2)
    #
        pt3=Part.Point(fpAa.a3)
        Pt3=sketchA.addGeometry(pt3)
    #   Génération du bspline et immobilisation des pts de contrôle pour Cascade
        (BSA,L1,L2)=self.planBSCascade(sketchA,Pt0,Pt1,Pt2,Pt3,100.,fpAa.a1.y,fpAa.a2.y, 100.)
        (Ddl1x,Ddl1y)=self.immobilisePoint(sketchA, Pt0, "CA"+I+"_0") 
        A1=sketchA.addConstraint(Sketcher.Constraint('Angle',L1,math.radians(fpAa.a1.x)))
        D1=sketchA.addConstraint(Sketcher.Constraint('Distance',L1,fpAa.a1.z))
        A2=sketchA.addConstraint(Sketcher.Constraint('Angle',L2,math.radians(fpAa.a2.x)))
        D2=sketchA.addConstraint(Sketcher.Constraint('Distance',L2,fpAa.a2.z))
        (Ddl4x,Ddl4y)=self.immobilisePoint(sketchA, Pt3, "CA"+I+"_3")
        sketchA.recompute()
        debug('CascadeSketch - fin')
        return sketchA

#
#
#       Domaine 3D
#
#
    def voile3D(self, fp):
        #
        # Association des deux plans pour obtenir la géométrie en 3D
        #
        # Filets.... contient les Discretize_Edge de chaque plan
        #
        debug('voile3D')
    #   Création des groupes pour classement
    #   Domaine3D
        docDomaine3D = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Domaine3D")
    #   a pour âme
    #   e pour extrados
    #   i pour intrados
    #   on crée les groupes
        docVoile3Da = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Voile3Da")
        docDomaine3D.addObject(docVoile3Da)
        docVoile3De = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Voile3De")
        docDomaine3D.addObject(docVoile3De)
        docVoile3Di = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Voile3Di")
        docDomaine3D.addObject(docVoile3Di)
        self.calculVoile(fp, docVoile3Da, docVoile3De, docVoile3Di, docDomaine3D)
            #   Création des surfaces
        fpSa=App.ActiveDocument.addObject("Part::FeaturePython","Ame") #add object to document
        approximate.Approximate(fpSa,docVoile3Da)
        fpSa.Parametrization='Curvilinear'
        fpSa.ApproxTolerance = 0.01
#        fpSa.recompute()
        # fpSa.Method="Smoothing Algorithm"
        # fpSa.CurvatureWeight = 9.00
        approximate.ViewProviderApp(fpSa.ViewObject)
        docDomaine3D.addObject(fpSa)
        fpSe=App.ActiveDocument.addObject("Part::FeaturePython","Extrados") #add object to document
        approximate.Approximate(fpSe,docVoile3De)
        fpSe.Parametrization='Curvilinear'
        fpSe.ApproxTolerance = 0.01
#        fpSe.recompute()
        # fpSe.Method="Smoothing Algorithm"
        # fpSe.CurvatureWeight = 9.00
        approximate.ViewProviderApp(fpSe.ViewObject)
        docDomaine3D.addObject(fpSe)
        fpSi=App.ActiveDocument.addObject("Part::FeaturePython","Intrados") #add object to document
        approximate.Approximate(fpSi,docVoile3Di)
        fpSi.Parametrization='Curvilinear'
        fpSi.ApproxTolerance = 0.01
        # fpSi.Method="Smoothing Algorithm"
        # fpSi.CurvatureWeight = 9.00
        approximate.ViewProviderApp(fpSi.ViewObject)
        docDomaine3D.addObject(fpSi)
#        fpSi.recompute()
        App.ActiveDocument.recompute()
        debug('voile3D - fin '+str(App.ActiveDocument.Objects.__len__()))
        return
    def calculVoile(self, fp, docVoile3Da, docVoile3De, docVoile3Di, docDomaine3D):
        debug('calculVoile')
        for i in range (fp.preNfilets):
            I=str(i+1)
            App.ActiveDocument.getObject('Voile3Da'+I).recompute()
            App.ActiveDocument.getObject('Voile3De'+I).recompute()
            App.ActiveDocument.getObject('Voile3Di'+I).recompute()
        for i in range(fp.preNfilets,fp.Nfilets):   #FiletMeridien in FiletsMeridien:   
    #       Creation et initialisation des séries de points 3D du voile
            I=str(i+1)
            ip1=i+1
            Ip1=str(ip1)
            fpVA = App.ActiveDocument.addObject("Part::FeaturePython",'Voile3Da'+I)
            fpVA.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points")
            fpVA.addProperty("App::PropertyInteger",   "Number",    "Discretization",   "Number").Number=fp.Npts
            debug(fpVA.Label)
            ViewProviderDisc(fpVA.ViewObject)
            fpVA.ViewObject.PointSize = 3
            docVoile3Da.addObject(fpVA)
            fpVE = App.ActiveDocument.addObject("Part::FeaturePython",'Voile3De'+I)
            fpVE.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points")
            fpVE.addProperty("App::PropertyInteger",   "Number",    "Discretization",   "Number").Number=fp.Npts
            debug(fpVE.Label)
            ViewProviderDisc(fpVE.ViewObject)
            fpVE.ViewObject.PointSize = 3
            docVoile3De.addObject(fpVE)
            fpVI = App.ActiveDocument.addObject("Part::FeaturePython",'Voile3Di'+I)
            fpVI.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points")
            fpVI.addProperty("App::PropertyInteger",   "Number",    "Discretization",   "Number").Number=fp.Npts
            debug(fpVI.Label)
            ViewProviderDisc(fpVI.ViewObject)
            fpVI.ViewObject.PointSize = 3
            docVoile3Di.addObject(fpVI)
        #   Calcul des 3 voiles A, E, I      
            FiletMeridien=App.ActiveDocument.getObject('FiletM'+Ip1)
            FiletM=FiletMeridien.Points
            FiletCascadeA=App.ActiveDocument.getObject('FiletCAs'+Ip1)
            FiletCA=FiletCascadeA.Points
            FiletCascadeE=App.ActiveDocument.getObject('FiletCAe'+Ip1)
            FiletCE=FiletCascadeE.Points
            FiletCascadeI=App.ActiveDocument.getObject('FiletCAi'+Ip1)
            FiletCI=FiletCascadeI.Points
            debug('$$$$$$$$$Calcul des points du voile')
            debug(I)
            debug('FiletM= '+str(FiletM))
            debug('FiletCA= '+str(FiletCA))
            debug('FiletCI= '+str(FiletCI))
            debug('FiletCE= '+str(FiletCE))
            Voile3DDiscretization.calcul(fpVA, FiletM, FiletCA, fp.Npts)
            Voile3DDiscretization.calcul(fpVI, FiletM, FiletCI, fp.Npts)
            Voile3DDiscretization.calcul(fpVE, FiletM, FiletCE, fp.Npts)
        debug('calculVoile - fin')
        return
    def modifVoile(self, fp):
        #
        # Association des deux plans pour obtenir la géométrie en 3D
        #
        # Filets.... contient les Discretize_Edge de chaque plan
        #
        debug('modifVoile')
    #   Récupération des groupes pour classement
    #   Domaine3D
        docDomaine3D = App.ActiveDocument.getObject("Domaine3D")
        docVoile3Da = App.ActiveDocument.getObject("Voile3Da")
        docVoile3De = App.ActiveDocument.getObject("Voile3De")
        docVoile3Di = App.ActiveDocument.getObject("Voile3Di")
    #   Creation et initialisation des séries de points 3D du voile
        for i in  range(fp.preNfilets):
            debug('Mise-à-jour des points des voiles existants')
            I=str(i+1)
            debug(I)
            fpVA = App.ActiveDocument.getObject('Voile3Da'+I)
            fpVE = App.ActiveDocument.getObject('Voile3De'+I)
            fpVI = App.ActiveDocument.getObject('Voile3Di'+I)
        #   Calcul des 3 voiles A, E, I      
            FiletMeridien=App.ActiveDocument.getObject('FiletM'+I)
            FiletM=FiletMeridien.Points
            FiletCascadeA=App.ActiveDocument.getObject('FiletCAs'+I)
            FiletCA=FiletCascadeA.Points
            FiletCascadeE=App.ActiveDocument.getObject('FiletCAe'+I)
            FiletCE=FiletCascadeE.Points
            FiletCascadeI=App.ActiveDocument.getObject('FiletCAi'+I)
            FiletCI=FiletCascadeI.Points
            debug('$$$$$$$$$Calcul des points du voile')
            debug(I)
            debug('FiletM= '+str(FiletM))
            debug('FiletCA= '+str(FiletCA))
            debug('FiletCI= '+str(FiletCI))
            debug('FiletCE= '+str(FiletCE))
            Voile3DDiscretization.calcul(fpVA, FiletM, FiletCA, fp.Npts)
            Voile3DDiscretization.calcul(fpVI, FiletM, FiletCI, fp.Npts)
            Voile3DDiscretization.calcul(fpVE, FiletM, FiletCE, fp.Npts)
            debug('fpVA')
            debug(fpVA.Points)
        for i in  range(fp.preNfilets,fp.Nfilets):
            debug('Création des voiles ajoutés')
            I=str(i+1)
            debug(I)
            fpVA = App.ActiveDocument.addObject("Part::FeaturePython","Voile3Da"+I)
            fpVA.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points")
            fpVA.addProperty("App::PropertyInteger",   "Number",    "Discretization",   "Number").Number=fp.Npts
            ViewProviderDisc(fpVA.ViewObject)
            fpVA.ViewObject.PointSize = 3
            if fp.preNfilets > 0 :fpVA.Visibility=App.ActiveDocument.getObject('Voile3Da'+str(i)).Visibility
            docVoile3Da.addObject(fpVA)
            fpVE = App.ActiveDocument.addObject("Part::FeaturePython","Voile3De"+I)
            fpVE.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points")
            fpVE.addProperty("App::PropertyInteger",   "Number",    "Discretization",   "Number").Number=fp.Npts
            ViewProviderDisc(fpVE.ViewObject)
            fpVE.ViewObject.PointSize = 3
            if fp.preNfilets > 0 :fpVE.Visibility=App.ActiveDocument.getObject('Voile3De'+str(i)).Visibility
            docVoile3De.addObject(fpVE)
            fpVI = App.ActiveDocument.addObject("Part::FeaturePython","Voile3Di"+I)
            fpVI.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points")
            fpVI.addProperty("App::PropertyInteger",   "Number",    "Discretization",   "Number").Number=fp.Npts
            ViewProviderDisc(fpVI.ViewObject)
            fpVI.ViewObject.PointSize = 3
            if fp.preNfilets > 0 :fpVI.Visibility=App.ActiveDocument.getObject('Voile3Di'+str(i)).Visibility
            docVoile3Di.addObject(fpVI)
        #   Calcul des 3 voiles A, E, I      
            FiletMeridien=App.ActiveDocument.getObject('FiletM'+I)
            FiletM=FiletMeridien.Points
            FiletCascadeA=App.ActiveDocument.getObject('FiletCAs'+I)
            FiletCA=FiletCascadeA.Points
            FiletCascadeE=App.ActiveDocument.getObject('FiletCAe'+I)
            FiletCE=FiletCascadeE.Points
            FiletCascadeI=App.ActiveDocument.getObject('FiletCAi'+I)
            FiletCI=FiletCascadeI.Points
            debug('$$$$$$$$$Calcul des points du voile')
            debug(I)
            debug('FiletM= '+str(FiletM))
            debug('FiletCA= '+str(FiletCA))
            debug('FiletCI= '+str(FiletCI))
            debug('FiletCE= '+str(FiletCE))
            Voile3DDiscretization.calcul(fpVA, FiletM, FiletCA, fp.Npts)
            Voile3DDiscretization.calcul(fpVI, FiletM, FiletCI, fp.Npts)
            Voile3DDiscretization.calcul(fpVE, FiletM, FiletCE, fp.Npts)
        App.ActiveDocument.recompute()
        debug('modifVoile - fin '+str(App.ActiveDocument.Objects.__len__()))
        return
      




class Voile3DDiscretization(Discretize.Discretization):
    def getTarget( self, obj, typ):
        try:
            o = obj.Edge[0]
            e = obj.Edge[1][0]
            n = eval(e.lstrip('Edge'))
            edge = o.Shape.Edges[n-1]
            obj.setEditorMode("Target", 2)
            for w in o.Shape.Wires:
                for e in w.Edges:
                    if edge.isSame(e):
                        debug("found matching edge")
                        debug("wire has %d edges"%len(w.Edges))
                        obj.setEditorMode("Target", 0)
                        if typ:
                            return w
            return edge
        except:
            return None
    def calcul(fp, FiletM, FiletC, Npts):
        debug('Voile3DDiscretization.calcul')
        debug('FiletM')
        debug(FiletM)
        debug('FileC')
        debug(FiletC)
        i=0
        fp.Number=Npts
        listePt=[]
        for ptM in FiletM:
            ptC=FiletC[i]
            r=ptM.x
            z=ptM.z
    #   L'angle calculé est inversé par rapport à la définition de la cascade où le bord d'attaque était l'origine
    #   alors qu'en 3D, c'est le centre de la roue qui est l'origine 
            theta=ptC.z/1000. # puisqu'on avait multiplié l'échelle par 1000 dans Cascade
            x=r*math.cos(theta)
            y=r*math.sin(theta)
            debug(str(x)+',  '+str(y)+',  '+str(z))
            listePt.append(App.Vector(x,y,z)) 
            i+=1
        fp.Points=listePt
        fp.Shape = Part.Compound([Part.Vertex(k) for k in fp.Points])
        debug('Voile3DDiscretization.calcul - fin')
        return    


class  ViewProviderDisc(Discretize.ViewProviderDisc):
    def __init__(self,vobj):
        vobj.Proxy = self
    def __getstate__(self):
        return #{"name": self.Object.Name}
    def __setstate__(self,state):
#        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None
    def claimChildren(self):
        try:
            edge=self.Object.Edge[0]
        except Exception:
            edge=None
        return [edge]

class Disc_s:
    def extractionPoints(self,ListePoints):
        debug('extractionPoints')
        x=[]
        y=[]
        z=[]
        debug(ListePoints)
        for point in ListePoints:
            x.append(point.x)
            y.append(point.y)
            z.append(point.z)
        debug(x)
        debug(y)
        debug(z)
        debug('extractionPoints - fin')
        return (x,y,z)
    def insertionPoints(self,x,y,z):
        debug('insertionPoints')
        debug(x)
        debug(y)
        debug(z)
        n=x.__len__()
        ListePoints=[]
        for i in range(n) : 
            point=App.Vector(x[i],y[i],z[i])
            ListePoints.append(point)
        debug(ListePoints)
        debug('insertionPoints - fin')
        return ListePoints

class DiscEp_s(Disc_s):
    # sert à interpoler les épaisseurs pour correspondre au s du plan méridien.
    def __init__(self, fpEp_s, fpEp, Npts, Last):
        fpEp_s.addProperty("App::PropertyLink", "fp_origine",      "Discretization",   "Courbe discrétisée d'origine").fp_origine = fpEp
        fpEp_s.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points").Points
        fpEp_s.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpEp_s.addProperty("App::PropertyFloat", "Last", "Parameter", "Coor. curv. dernier point").Last =Last
        fpEp_s.Proxy=self
        self.execute(fpEp_s)
        return
    def onChanged(self, fpEp_s, prop):
        debug('DiscEp_s.onChanged propriété changée: '+prop)
        if (prop == "Npts" or prop == "Last"):
            debug('on effectue le changement')
            self.execute(fpEp_s)
        return
    def execute(self, fpEp_s):
        debug('DiscEp_s.execute')
        ListePoints=fpEp_s.fp_origine.Points
        debug('ListePoints='+str(ListePoints))
        sX=[]
        for k in range (0,fpEp_s.Npts):sX.append(1000.*fpEp_s.Last*k/(fpEp_s.Npts-1))
        debug('sX='+str(sX))
        (X,Y,Z)=self.extractionPoints(ListePoints)
        debug(X)
        sY=np.interp(sX,X,Y)
        fpEp_s.Points=self.insertionPoints(sX,sY,Z)
        fpEp_s.Shape = Part.Compound([Part.Vertex(k) for k in fpEp_s.Points])
        debug('DiscEp_s.execute - fin')
        return

class DiscCa_s(Disc_s):
    def __init__(self, fpAs, fpAa, Npts, i):
        fpAs.addProperty("App::PropertyLink", "fp_origine",      "Discretization",   "Courbe discrétisée d'origine").fp_origine = fpAa
        fpAs.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points").Points
        fpAs.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpAs.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpAs.addProperty("App::PropertyFloatList", "r_s", "Discretization", "Coor. r(s)").r_s
        fpAs.addProperty("App::PropertyFloatList", "z_s", "Discretization", "Coor. z(s)").z_s
        fpAs.addProperty("App::PropertyFloatList", "m_s", "Discretization", "Coor. m(s)").m_s
        fpAs.addProperty("App::PropertyFloatList", "n_s", "Discretization", "Coor. n(s)").n_s
        fpAs.addProperty("App::PropertyFloatList", "u_s", "Discretization", "Coor. u(s)").u_s
        fpAs.addProperty("App::PropertyFloatList", "v_s", "Discretization", "Coor. v(s)").v_s
        fpAs.addProperty("App::PropertyFloatList", "Ee_s", "Discretization", "Loi épaisseur extrados").Ee_s
        fpAs.addProperty("App::PropertyFloatList", "Ei_s", "Discretization", "Loi épaisseur intrados").Ei_s
        fpAs.Proxy=self
        self.execute(fpAs)
        return
    def execute(self, fpAs):
        debug('DiscCa_s.execute')
#        if(fpAs.State=="Touched"): return
    #   Synchronisation des u,v avec l'abscisse s du plan meridien
        (t,u_q,v_q)=self.extractionPoints(fpAs.fp_origine.Points)  #fpAa.Points a été discretisé à égale distance en u-v
        I=str(fpAs.i+1)
        FiletMeridien=App.ActiveDocument.getObject('FiletM'+I)
        nseg=FiletMeridien.Number-1
        pj=FiletMeridien.Points[0]
    #   l'indice _s correspond à la coordonnée curviligne dans le plan méridien
        m_n=App.ActiveDocument.getObject("IsoCurve").Shape.Edges[fpAs.i].Length
        dm=m_n/nseg
        m_s=[]
        m=0
        m_s.append(m)
        u_s=[]
        u=0
        u_s.append(u)
        r_s=[]
        r_s.append(pj.x)
        z_s=[]
        z_s.append(pj.z)
        debug('r,m,u ='+str(pj.x)+', '+str(m)+', '+str(u))
        for pj in FiletMeridien.Points[1:]:
            r_s.append(pj.x)
            z_s.append(pj.z)
            m+=dm
            u+=1000.*dm/pj.x
            m_s.append(m)
            u_s.append(u)       #u_s est ainsi calculé à partir d'un m fonction de s dans le plan méridien
        v_s=np.interp(u_s,u_q,v_q)  #v_s est maintenant associé à u_s 
        debug('v_s= '+str(v_s))
        n_s=[]
        n=v_s[0]*r_s[0]/1000.
        n_s.append(n)
        #   Calcul de la longueur limite Lmn (dans le plan de l'épaisseur)qui sera utilisée pour mettre à l'échelle l'épaisseur
        #
        #   n_s est l'ordonnée (r*theta ou r*v) du plan des longueurs m-n exprimée par rapport à s
        #   Lmn est la longueur du filet dans le plan m-n des longueurs qui est égale à la longueur du filet dans le domaine 3D
        #   Lmns est la longueur cumulée du filet a chacune des coordonnées s 
        #   Lmne est le facteur d'échelle entre la longueur (3D ou m-n) extrados et la corde du profil dans le plan de l'épaisseur  
        #   Lmni pour l'intrados
        Lmn=0       #Longueur dans le plan mn
        Lmns=[]
        Lmns.append(Lmn)
        j=1
        for j in range(1,fpAs.Npts):  
            dn_s=(v_s[j]-v_s[j-1])*r_s[j]/1000.
            n_s.append(n_s[j-1]+dn_s)
            dr=r_s[j]-r_s[j-1]
            dz=z_s[j]-z_s[j-1]
            dy=n_s[j]-n_s[j-1]
            Lmn+= math.sqrt(dr*dr+dz*dz+dy*dy)
            Lmns.append(Lmn)    #abcisse curviligne de l'âme dans le plan m-n
        debug('Lmns= '+str(Lmns))
        debug('n_s= '+str(n_s))
    #
    #   Récupération des fp LoiEpaisseurs
    #
        LoiEpaisseurIe=App.ActiveDocument.getObject('LoiEpaisseur'+I+'es').Points
        LoiEpaisseurIi=App.ActiveDocument.getObject('LoiEpaisseur'+I+'is').Points 
        debug('LoiEpaisseurIe= '+str(LoiEpaisseurIe))
        Lmne=Lmn/LoiEpaisseurIe[nseg].x	    #corde de l'extrados
        Lmni=Lmn/LoiEpaisseurIi[nseg].x     #corde de l'intrados  
        debug('Lmne= '+str(Lmne))
        debug('Lmni= '+str(Lmne))
        #   Calcul des épaisseurs en fonction de la coordonnées s dans le plan meridien
        Eex=[]
        Eey=[]
        Eix=[]
        Eiy=[]
        for j in range(fpAs.Npts):
            Eey.append(LoiEpaisseurIe[j].y*Lmne)    #l'épaisseur est corrigée en fonction de la longueur curviligne
            Eiy.append(LoiEpaisseurIi[j].y*Lmni)
            Eex.append(LoiEpaisseurIe[j].x*Lmne)   
            Eix.append(LoiEpaisseurIi[j].x*Lmni)
    #   stockage dans fpAs
        debug('Eey= '+str(Eey))
        debug('Eiy= '+str(Eiy))
        debug('Eex= '+str(Eex))
        debug('Eix= '+str(Eix))
        fpAs.r_s=r_s
        fpAs.z_s=z_s
        fpAs.m_s=m_s
        fpAs.n_s=n_s
        fpAs.u_s=u_s
        Ee_s=[]
        Ee_ss=[]
        Ee_s=np.interp(Lmns,Eex,Eey)
        Ei_s=[]
        Ei_ss=[]
        v_ss=[]
        Ei_s=np.interp(Lmns,Eix,Eiy)
        for j in range(fpAs.Npts):
            Ee_ss.append(Ee_s[j])
            Ei_ss.append(Ei_s[j])
            v_ss.append(v_s[j])
        fpAs.v_s=v_ss
        fpAs.Ee_s=Ee_ss
        fpAs.Ei_s=Ei_ss
        fpAs.Points=self.insertionPoints(t,u_s,v_s)
        fpAs.Shape = Part.Compound([Part.Vertex(k) for k in fpAs.Points]) 
        debug('DiscCa_s.execute - fin')
        return
    def onChanged(self, fpAs, prop):
        debug('DiscAs_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
            debug('on effectue le changement')
            self.execute(fpAs)
        return

class DiscCl_s:
    def __init__(self, fpLa, fpAs, Npts, i):
        fpLa.addProperty("App::PropertyLink", "fp_origine",      "Discretization",   "Courbe discrétisée d'origine").fp_origine = fpAs
        fpLa.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpLa.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpLa.Proxy=self
        self.execute(fpLa)
        return
    def execute(self,fpLa):
        m_s=fpLa.fp_origine.m_s
        n_s=fpLa.fp_origine.n_s
        Npts=fpLa.Npts
        nseg=Npts-1
        LoiLongueursa=[]
        pLa=App.Vector(0,m_s[0],n_s[0])
        LoiLongueursa.append(pLa)
        signe_face=-1
        if (n_s[nseg]-n_s[0])>0:signe_face=1
        for j in range(1,Npts):
            pLa=App.Vector(0,m_s[j],n_s[j])
            LoiLongueursa.append(pLa)
        fpLa.addProperty("App::PropertyVectorList",   "Points",    "Points âme",   "Points").Points=LoiLongueursa
        fpLa.Shape = Part.Compound([Part.Vertex(k) for k in fpLa.Points])
        return
    def onChanged(self, fpLa, prop):
        debug('DiscCl_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
            debug('on effectue le changement')
            self.execute(fpLa)
        return
        
class DiscCli_s:
    def __init__(self, fpLi, fpAs, Npts, Sens, i):
        debug('DiscCli_s.init')
        fpLi.addProperty("App::PropertyLink", "fp_origine",      "Discretization",   "Courbe discrétisée d'origine").fp_origine = fpAs
        fpLi.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpLi.addProperty("App::PropertyIntegerConstraint","Sens","Parameter","Rotation(1:anti-horaire, -1:horaire)").Sens=Sens
        fpLi.addProperty("App::PropertyFloatList", "ni_j", "Discretization", "Loi épaisseur intrados").ni_j
        fpLi.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpLi.Proxy=self
        self.execute(fpLi)
        debug('DiscCli_s.init - fin')
        return
    def execute(self,fpLi):
        debug('DiscCli_s.execute')
        debug('fpLi.Npts = '+str(fpLi.Npts))
        debug('fpLi.Sens = '+str(fpLi.Sens))
        nseg=fpLi.Npts-1
        m_s=fpLi.fp_origine.m_s
        n_s=fpLi.fp_origine.n_s
        Ei_s=fpLi.fp_origine.Ei_s
        debug('m_s = '+str(m_s))
        debug('n_s = '+str(n_s))
        debug('Ei_s = '+str(Ei_s))
        LoiLongueursi=[]
        ni_j=[]
        j=0
        ni_j.append(n_s[j])
        pLi=App.Vector(0,m_s[j],n_s[j])            
        LoiLongueursi.append(pLi)
    #
    #   Calcul de la faces intrados dans le plan cascade L
    #   
        for j in range(1,fpLi.Npts):
        #   execute de la géométrie dans le plan de cascade L
            nij=n_s[j] + fpLi.Sens * Ei_s[j]
            ni_j.append(nij)
            pLi=App.Vector(0,m_s[j],nij)
            LoiLongueursi.append(pLi)
        fpLi.ni_j=ni_j
        fpLi.addProperty("App::PropertyVectorList",   "Points",    "Points extrados",   "Points").Points=LoiLongueursi
        fpLi.Shape = Part.Compound([Part.Vertex(k) for k in fpLi.Points])
        debug('DiscCli_s.execute - fin')
        return
    def onChanged(self, fpLi, prop):
        debug('DiscCli_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
            debug('on effectue le changement')
            self.execute(fpLi)
        debug('DiscCli_s.onChanged - fin')
        return
        
class DiscCle_s:
    def __init__(self, fpLe, fpAs, Npts, Sens,i):
        fpLe.addProperty("App::PropertyLink", "fp_origine",      "Discretization",   "Courbe discrétisée d'origine").fp_origine = fpAs
        fpLe.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpLe.addProperty("App::PropertyIntegerConstraint","Sens","Parameter","Rotation(1:anti-horaire, -1:horaire)").Sens=Sens
        fpLe.addProperty("App::PropertyFloatList", "ne_j", "Discretization", "Loi épaisseur extrados").ne_j
        fpLe.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpLe.Proxy=self
        self.execute(fpLe)
        return
    def execute(self,fpLe):
        debug('DiscCle_s.execute')
        nseg=fpLe.Npts-1
        m_s=fpLe.fp_origine.m_s
        n_s=fpLe.fp_origine.n_s
        Ee_s=fpLe.fp_origine.Ee_s
        debug('m_s = '+str(m_s))
        debug('n_s = '+str(n_s))
        debug('Ee_s = '+str(Ee_s))
        LoiLongueurse=[]
        ne_j=[]
        j=0
        ne_j.append(n_s[j])
        pLe=App.Vector(0,m_s[j],n_s[j])
        LoiLongueurse.append(pLe)
    #
    #   Calcul de la face extrados dans le plan cascade L
    #   
        for j in range(1,fpLe.Npts):
            nej=n_s[j] + fpLe.Sens*Ee_s[j]
            ne_j.append(nej)
            pLe=App.Vector(0.,m_s[j],nej)
            LoiLongueurse.append(pLe)
        fpLe.ne_j=ne_j
        fpLe.addProperty("App::PropertyVectorList",   "Points",    "Points extrados",   "Points").Points=LoiLongueurse
        fpLe.Shape = Part.Compound([Part.Vertex(k) for k in fpLe.Points])
        debug('DiscCle_s.execute - fin')
        return
    def onChanged(self, fpLe, prop):
        debug('DiscCle_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
            debug('on effectue le changement')
            self.execute(fpLe)
        return
        

class DiscCe_s:
    def __init__(self, fpAe, fpAs, fpLe, Npts, i):
        fpAe.addProperty("App::PropertyLink", "fp_origine1",      "Discretization",   "Courbe discrétisée d'origine").fp_origine1 = fpAs
        fpAe.addProperty("App::PropertyLink", "fp_origine2",      "Discretization",   "Courbe discrétisée d'origine").fp_origine2 = fpLe
        fpAe.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpAe.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpAe.Proxy=self
        self.execute(fpAe)
        return
    def execute(self,fpAe):
        debug('DiscCe_s.execute')
        r_s=fpAe.fp_origine1.r_s
        n_s=fpAe.fp_origine1.n_s
        u_s=fpAe.fp_origine1.u_s
        v_s=fpAe.fp_origine1.v_s
        ne_j=fpAe.fp_origine2.ne_j
        debug('r_s = '+str(r_s))
        debug('n_s = '+str(n_s))
        debug('u_s = '+str(u_s))
        debug('v_s = '+str(v_s))
        debug('ne_j = '+str(ne_j))
        j=0
        ve_j=[]
        ve_j.append(v_s[j])
        LoiCascadee=[]
        pAe=App.Vector(0,u_s[j],v_s[j])
        LoiCascadee.append(pAe)
        for j in range(1,fpAe.Npts):
            ve_j.append(v_s[j]+(ne_j[j]-n_s[j])*1000./r_s[j])
            pAe=App.Vector(0,u_s[j],ve_j[j])
            LoiCascadee.append(pAe)
        fpAe.addProperty("App::PropertyVectorList",   "Points",    "Points extrados",   "Points").Points=LoiCascadee
        fpAe.Shape = Part.Compound([Part.Vertex(k) for k in fpAe.Points])
        debug('DiscCe_s.execute - fin')
        return
    def onChanged(self, fpAe, prop):
        debug('DiscCe_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
            debug('on effectue le changement')
            self.execute(fpAe)
        return
        
class DiscCi_s:
    def __init__(self, fpAi, fpAs, fpLi, Npts, i):
        fpAi.addProperty("App::PropertyLink", "fp_origine1",      "Discretization",   "Courbe discrétisée d'origine").fp_origine1 = fpAs
        fpAi.addProperty("App::PropertyLink", "fp_origine2",      "Discretization",   "Courbe discrétisée d'origine").fp_origine2 = fpLi
        fpAi.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpAi.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpAi.Proxy=self
        self.execute(fpAi)
        return
    def execute(self,fpAi):
        r_s=fpAi.fp_origine1.r_s
        n_s=fpAi.fp_origine1.n_s
        u_s=fpAi.fp_origine1.u_s
        v_s=fpAi.fp_origine1.v_s
        ni_j=fpAi.fp_origine2.ni_j
        j=0
        vi_j=[]
        vi_j.append(v_s[j])
        LoiCascadei=[]
        pAi=App.Vector(0,u_s[j],v_s[j])            
        LoiCascadei.append(pAi)
        for j in range(1,fpAi.Npts):
            vi_j.append(v_s[j]+(ni_j[j]-n_s[j])*1000./r_s[j])
            pAi=App.Vector(0,u_s[j],vi_j[j])
            LoiCascadei.append(pAi)
        fpAi.addProperty("App::PropertyVectorList",   "Points",    "Points intrados",   "Points").Points=LoiCascadei
        fpAi.Shape = Part.Compound([Part.Vertex(k) for k in fpAi.Points])
        return
    def onChanged(self, fpAe, prop):
        debug('DiscCe_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
            debug('on effectue le changement')
            self.execute(fpAe)
        return