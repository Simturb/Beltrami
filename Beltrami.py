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
from scipy.interpolate import CubicSpline
from freecad.Curves import IsoCurve as iso
from freecad.Curves import Discretize
from freecad.Curves import approximate
from freecad.Curves import interpolate
   
#Gui.activateWorkbench("SketcherWorkbench")

class beltrami:
    def __init__(self, fp): # Ordre coldStart
    #
    #   Initialisation du FeaturePython Parametres
    #
        fp.addProperty("App::PropertyString","Version","Base","Numéro de version").Version="1.0.8"
        fp.addProperty("App::PropertyInteger","Naubes","Base","Nombre d'aubes").Naubes=13
        fp.addProperty("App::PropertyIntegerConstraint","Nfilets","Base","Nombre de filets").Nfilets=(6,2,65,1)
        fp.addProperty("App::PropertyIntegerConstraint","preNfilets","Base","Nombre de filets précédents").preNfilets=0
        fp.addProperty("App::PropertyIntegerConstraint","Npts","Base","Nombre de points par filet").Npts=(9,9,1025,8)
        fp.addProperty("App::PropertyIntegerConstraint","Sens","Base","Rotation(1:anti-horaire, -1:horaire)").Sens=(1,-1,1,2)
        fp.addProperty("App::PropertyIntegerConstraint","CascadeRotation","Base","Rotation(1:rotation, -1:fixe)").CascadeRotation=(1,-1,1,2)
        fp.addProperty("App::PropertyIntegerConstraint","SensCascade","Base","Rotation(1:anti-horaire, -1:horaire)").SensCascade=(1,-1,1,2)
        fp.addProperty("App::PropertyBool","Modifiable","Base","Vrai pour modification").Modifiable=False
        fp.addProperty("App::PropertyBool","Init","Base","Vrai pour modification").Init=True
        fp.addProperty("App::PropertyInteger","Def_t","Base","Nombre de poles en t").Def_t=4
        fp.Proxy=self
        fp.setEditorMode("Version",1)
        fp.setEditorMode("Label",1)
        fp.setEditorMode("Modifiable",2)
        fp.setEditorMode("SensCascade",2)
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
        self.modifEpaisseur(fp)
#        self.sauveMeridien(fp)
        self.modifCascade(fp)
        self.modifVoile(fp)
        return
    def initPilote(self,fp):
#       print('initPilote')
        self.initTableur(fp)
    #   création et stokage des sketch de pilotage de la géométrie 
        docPilote = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Pilote")
        self.initCascade(fp)
        self.initEpaisseur(fp)
        self.initMeridien(fp)
        fp.Init=False
        App.ActiveDocument.recompute()
#       print('initPilote - fin')
        return
#
#
#       Routines système FreeCAD
#
#
    def onChanged(self, fp, prop):
#        print('onChanged propriété changée: '+prop)
#        print('Modifiable = '+str(fp.Modifiable))
        if fp.Init : return
        if (prop == "Init") : return
        if not fp.Modifiable :
            if('Up-to-date' in fp.State): 
                fp.Modifiable=True
        #       print('Statut modifiable changé = '+str(fp.Modifiable))
        if not fp.Modifiable : return
#       print('Modifiable = '+str(fp.Modifiable))
        if (prop == "ExpressionEngine" or prop == "Proxy" or prop =="Visibility" or prop=="Label" or prop=="Shape" or prop=="Points" or prop=="Naubes"):
    #       print('Avec ExpressionEngine,Proxy, Visibility, Label, Shape, Points: pas de calcul ')
            return
        if (prop == "Sens"):
    #       print('Beltrami.onChanged '+prop)
            fp.SensCascade=fp.Sens*fp.CascadeRotation
#            App.ActiveDocument.Volume.purgeTouched()
            self.modifCascade(fp) 
            self.modifVoile(fp)
            App.ActiveDocument.recompute()
    #       print('onChanged - fin')
            return
        if (prop == "CascadeRotation"):
    #       print('Beltrami.onChanged '+prop)
            fp.SensCascade=fp.Sens*fp.CascadeRotation
            self.modifCascade(fp) 
            self.modifVoile(fp)
            fp.recompute()
    #       print('onChanged - fin')
            return
        if(prop == "Npts"):
#            print('Beltrami.onChanged Npts')
#            print(prop)
            self.onChangedNpts( fp)
#            print('Beltrami.onChanged Npts - fin')
            return
        if(prop == "Nfilets"):
            self.onChangedNfilets(fp)
    #       print('onChanged - fin')
            return
#        print('onChanged - fin')
        return 
    def onChangedNpts(self, fp):
#        print("onChangedNpts")
        for i in range(fp.Nfilets):
            I=str(i+1)
    #       print('Pour le filet '+str(i))
            FiletMi=App.ActiveDocument.getObject("FiletM"+I)
            FiletMi.Number=fp.Npts
            FiletMi.recompute()
    #       print('Filet méridien traité')
            fpe=App.ActiveDocument.getObject("LoiEpaisseur"+I+"e")
            fpe.Number=fp.Npts
            fpe.recompute()
    #       print("LoiEpaisseur"+I+"e traité")
            fpi=App.ActiveDocument.getObject("LoiEpaisseur"+I+"i")
            fpi.Number=fp.Npts
            fpi.recompute()
    #       print("LoiEpaisseur"+I+"i traité")
            fpes=App.ActiveDocument.getObject("LoiEpaisseur"+I+"es")
            fpes.Npts=fp.Npts
            fpes.recompute()
    #       print("LoiEpaisseur"+I+"es traité")
            fpis=App.ActiveDocument.getObject("LoiEpaisseur"+I+"is")
            fpis.Npts=fp.Npts
            fpis.recompute()
    #       print("LoiEpaisseur"+I+"is traité")
            Ts=App.ActiveDocument.getObject("Theta_sortie")
            Usmax=self.CascadeUsmax(i)
            sketchA=App.ActiveDocument.getObject('Cascade'+I)
            sketchA.setDatum(24,App.Units.Quantity(str(Usmax)))
    #       print('Usmax= '+str(Usmax))
            fpAa=App.ActiveDocument.getObject("FiletCAa"+I)
            fpAa.a3=App.Vector(Usmax,fp.SensCascade*1000.*math.radians(Ts.Points[i].z),0)
            fpAa.Number=fp.Npts
            fpAa.recompute()
    #       print("FiletCAa"+I+" traité")
            fpAs=App.ActiveDocument.getObject("FiletCAs"+I)
            fpAs.Npts=fp.Npts
            fpAs.recompute()
    #       print("FiletCAs"+I+" traité")
            fpLa=App.ActiveDocument.getObject("FiletCLa"+I)
            fpLa.Npts=fp.Npts
            fpLa.recompute()
    #       print("FiletCLa"+I+" traité")
            fpLe=App.ActiveDocument.getObject("FiletCLe"+I)
            fpLe.Npts=fp.Npts
            fpLe.recompute()
    #       print("FiletCLe"+I+" traité")
            fpLi=App.ActiveDocument.getObject("FiletCLi"+I)
            fpLi.Npts=fp.Npts
            fpLi.recompute()
    #       print("FiletCLi"+I+" traité")
            fpAe=App.ActiveDocument.getObject("FiletCAe"+I)
            fpAe.Npts=fp.Npts
            fpAe.recompute()
    #       print("FiletCAe"+I+" traité")
            fpAi=App.ActiveDocument.getObject("FiletCAi"+I)
            fpAi.Npts=fp.Npts
            fpAi.recompute()
    #
            fpVA=App.ActiveDocument.getObject("Points3Da"+I)
            fpVA.Number=fp.Npts
            fpVA.recompute()
    #
            fpVE=App.ActiveDocument.getObject("Points3De"+I)
            fpVE.Number=fp.Npts
            fpVE.recompute()
    #
            fpVI=App.ActiveDocument.getObject("Points3Di"+I)
            fpVI.Number=fp.Npts
            fpVI.recompute()
    #
            fpVIE=App.ActiveDocument.getObject("Points3Die"+I)
            fpVIE.Number=2*fp.Npts-1
            fpVIE.recompute()
#            App.ActiveDocument.recompute()
    #       print("FiletCAi"+I+" traité")
        self.modifVoile(fp)
#        self.modifSurf(fp)
#        print("onChangedNpts - fin")
        return
    def onChangedNfilets(self, fp):
#        Gui.Selection.clearSelection()
#        print('onChangedNfilets')
        if(fp.Nfilets ==fp.preNfilets):
    #       print('onChangedNfilets - fin')
            return
    #   Plan méridien
        docPlanMeridien=App.ActiveDocument.getObject('Plan_Meridien')
        IsoCurve=App.ActiveDocument.getObject('IsoCurve')
        IsoCurve.NumberU=fp.Nfilets
        IsoCurve.recompute()
    #   Traitement du plan des épaisseurs
        EpEx1X = App.ActiveDocument.getObject( "EpEx1X") 
        EpEx1X.Number=fp.Nfilets
        EpEx1X.recompute()
        EpEx2X = App.ActiveDocument.getObject( "EpEx2X") 
        EpEx2X.Number=fp.Nfilets
        EpEx2X.recompute()
        EpEx3X = App.ActiveDocument.getObject( "EpEx3X") 
        EpEx3X.Number=fp.Nfilets
        EpEx3X.recompute()
        EpEx4X = App.ActiveDocument.getObject( "EpEx4X") 
        EpEx4X.Number=fp.Nfilets
        EpEx4X.recompute()
        EpEx5X = App.ActiveDocument.getObject( "EpEx5X") 
        EpEx5X.Number=fp.Nfilets
        EpEx5X.recompute()
        EpEx1Y = App.ActiveDocument.getObject( "EpEx1Y") 
        EpEx1Y.Number=fp.Nfilets
        EpEx1Y.recompute()
        EpEx2Y = App.ActiveDocument.getObject( "EpEx2Y") 
        EpEx2Y.Number=fp.Nfilets
        EpEx2Y.recompute()
        EpEx3Y = App.ActiveDocument.getObject( "EpEx3Y") 
        EpEx3Y.Number=fp.Nfilets
        EpEx3Y.recompute()
        EpEx4Y = App.ActiveDocument.getObject( "EpEx4Y") 
        EpEx4Y.Number=fp.Nfilets
        EpEx4Y.recompute()
        EpEx5Y = App.ActiveDocument.getObject( "EpEx5Y") 
        EpEx5Y.Number=fp.Nfilets
        EpEx5Y.recompute()
        EpExLast = App.ActiveDocument.getObject( "EpExLast") 
        EpExLast.Number=fp.Nfilets
        EpExLast.recompute()
        EpIn1X = App.ActiveDocument.getObject( "EpIn1X") 
        EpIn1X.Number=fp.Nfilets
        EpIn1X.recompute()
        EpIn2X = App.ActiveDocument.getObject( "EpIn2X") 
        EpIn2X.Number=fp.Nfilets
        EpIn2X.recompute()
        EpIn3X = App.ActiveDocument.getObject( "EpIn3X") 
        EpIn3X.Number=fp.Nfilets
        EpIn3X.recompute()
        EpIn4X = App.ActiveDocument.getObject( "EpIn4X") 
        EpIn4X.Number=fp.Nfilets
        EpIn4X.recompute()
        EpIn5X = App.ActiveDocument.getObject( "EpIn5X") 
        EpIn5X.Number=fp.Nfilets
        EpIn5X.recompute()
        EpIn1Y = App.ActiveDocument.getObject( "EpIn1Y") 
        EpIn1Y.Number=fp.Nfilets
        EpIn1Y.recompute()
        EpIn2Y = App.ActiveDocument.getObject( "EpIn2Y") 
        EpIn2Y.Number=fp.Nfilets
        EpIn2Y.recompute()
        EpIn3Y = App.ActiveDocument.getObject( "EpIn3Y") 
        EpIn3Y.Number=fp.Nfilets
        EpIn3Y.recompute()
        EpIn4Y = App.ActiveDocument.getObject( "EpIn4Y") 
        EpIn4Y.Number=fp.Nfilets
        EpIn4Y.recompute()
        EpIn5Y = App.ActiveDocument.getObject( "EpIn5Y") 
        EpIn5Y.Number=fp.Nfilets
        EpIn5Y.recompute()
        EpInLast = App.ActiveDocument.getObject( "EpInLast") 
        EpInLast.Number=fp.Nfilets
        EpInLast.recompute()
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
#        print("fin recompute Pilote")
    #
    #   pour fp.Nfilets > fp.preNfilets
    #
        if (fp.Nfilets > fp.preNfilets):
        #   Plan méridien
#            print("if (fp.Nfilets > fp.preNfilets) fp.Nfilets,fp.preNfilets=",fp.Nfilets,fp.preNfilets)
            for i in range (fp.preNfilets):
                I=str(i+1)
                App.ActiveDocument.getObject("FiletM"+I).recompute()
            for i in range(fp.preNfilets,fp.Nfilets):
                I=str(i+1)
                fpM = App.ActiveDocument.addObject("Part::FeaturePython","FiletM"+I)
                docPlanMeridien.addObject(fpM)
                Discretize.Discretization(fpM, (App.ActiveDocument.getObject("IsoCurve"),"Edge"+I))
                fpM.Number=fp.Npts
                Discretize.ViewProviderDisc(fpM.ViewObject)
                fpM.ViewObject.PointSize = 3
                if fp.preNfilets > 0 :fpM.Visibility=App.ActiveDocument.getObject('FiletM'+str(i)).Visibility
                fpM.recompute()
            #   Plan épaisseurs
            self.sketchDiscEpaisseur(fp, EpEx1X, EpEx2X, EpEx3X, EpEx4X, EpEx5X, EpEx1Y, EpEx2Y, EpEx3Y, EpEx4Y, EpEx5Y, EpExLast, EpIn1X, EpIn2X, EpIn3X, EpIn4X, EpIn5X, EpIn1Y, EpIn2Y, EpIn3Y, EpIn4Y, EpIn5Y, EpInLast)    
            self.modifEpaisseur(fp)
        #   Plans des longueurs et de la cascade
            self.sketchDiscCascade(fp, Te, Ts, Ae, As, We, Ws, Le, Ls)
            self.modifCascade(fp)
    #
    #   pour Nfilets < preNfilets
    #
        else: 
#            print("pour Nfilets < preNfilets")
        #   plan méridien
            for i in range (fp.Nfilets):
                I=str(i+1)
        #       print(I)
                App.ActiveDocument.getObject("FiletM"+I).recompute()
            for i in range (fp.Nfilets,fp.preNfilets):
                I=str(i+1)
                App.ActiveDocument.removeObject("FiletM"+I)
#            print("fin recompute méridien")
        #   plan des épaisseurs
            for i in range (fp.Nfilets):
        #       print("for i in range (fp.Nfilets):")
                I=str(i+1)
        #       print(I)
                App.ActiveDocument.getObject('LoiEpaisseur'+I+'e').recompute()
                App.ActiveDocument.getObject("LoiEpaisseur"+I+"es").recompute()
                App.ActiveDocument.getObject('LoiEpaisseur'+I+'i').recompute()
                App.ActiveDocument.getObject("LoiEpaisseur"+I+"is").recompute()
            for i in range (fp.Nfilets,fp.preNfilets):
        #       print("for i in range (fp.Nfilets,fp.preNfilets)")
                I=str(i+1)
        #       print(I)
                App.ActiveDocument.removeObject("skLoiEpaisseur"+I+"e")
                App.ActiveDocument.removeObject("LoiEpaisseur"+I+"e")
                App.ActiveDocument.removeObject("LoiEpaisseur"+I+"es")
                App.ActiveDocument.removeObject("skLoiEpaisseur"+I+"i")
                App.ActiveDocument.removeObject("LoiEpaisseur"+I+"i")
                App.ActiveDocument.removeObject("LoiEpaisseur"+I+"is")
            self.modifEpaisseur(fp)
#            print("fin recompute Épaisseurs")
        #   Plans des longueurs et de la cascade
            self.modifCascade(fp)
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
                App.ActiveDocument.removeObject("Points3Da"+I)
                App.ActiveDocument.removeObject("Points3De"+I)
                App.ActiveDocument.removeObject("Points3Di"+I)
                App.ActiveDocument.removeObject("Points3Die"+I)
                App.ActiveDocument.removeObject("Filet3Da"+I)
                App.ActiveDocument.removeObject("Filet3De"+I)
                App.ActiveDocument.removeObject("Filet3Di"+I)
                App.ActiveDocument.removeObject("Filet3Die"+I)
        #   Voile 3D
        self.modifVoile(fp)
#       print('calcul des surfaces des voiles')
    #   Voile 3D
        fp.preNfilets=fp.Nfilets
#       print('onChangedNfilets - fin')
        return
    def __setstate__(self, state):
#       print('setstate')
        fp=App.ActiveDocument.getObject('Parametres')
        fp.Modifiable=False
#       print('Modifiable = '+str(fp.Modifiable))
#       print('setstate - fin')
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
        Feuil.set("C1", "33.3333333333")
        Feuil.set("D1", "66.6666666666")
        Feuil.set("E1", "100.0")
#       Cambrure et position
        Feuil.set("B2", "deg")
        Feuil.set("C2", "deg")
        Feuil.set("D2", "deg")
        Feuil.set("E2", "deg")
        L="3"
        Feuil.set("A"+L, "Theta_entree")
        Feuil.set("B"+L, "0.0")
        Feuil.set("C"+L, "-1.33")
        Feuil.set("D"+L, "-2.66")
        Feuil.set("E"+L, "-4.0")
        Feuil.setAlias("B"+L, "ThE1")
        Feuil.setAlias("C"+L, "ThE2")
        Feuil.setAlias("D"+L, "ThE3")
        Feuil.setAlias("E"+L, "ThE4")
        L="4"
        Feuil.set("A"+L, "Theta_sortie")
        Feuil.set("B"+L, "-30.0")
        Feuil.set("C"+L, "-40.0")
        Feuil.set("D"+L, "-50.0")
        Feuil.set("E"+L, "-60.0")
        Feuil.setAlias("B"+L, "ThS1")
        Feuil.setAlias("C"+L, "ThS2")
        Feuil.setAlias("D"+L, "ThS3")
        Feuil.setAlias("E"+L, "ThS4")
        L="5"
        Feuil.set("A"+L, "Alpha_entree")
        Feuil.set("B"+L, "-56.77")
        Feuil.set("C"+L, "-51.72")
        Feuil.set("D"+L, "-49.32")
        Feuil.set("E"+L, "-48.34")
        Feuil.setAlias("B"+L, "AlE1")
        Feuil.setAlias("C"+L, "AlE2")
        Feuil.setAlias("D"+L, "AlE3")
        Feuil.setAlias("E"+L, "AlE4")
        L="6"
        Feuil.set("A"+L, "Alpha_sortie")
        Feuil.set("B"+L, "-56.77")
        Feuil.set("C"+L, "-51.72")
        Feuil.set("D"+L, "-49.32")
        Feuil.set("E"+L, "-48.34")
        Feuil.setAlias("B"+L, "AlS1")
        Feuil.setAlias("C"+L, "AlS2")
        Feuil.setAlias("D"+L, "AlS3")
        Feuil.setAlias("E"+L, "AlS4")
        L="7"
        Feuil.set("B7", "mm")
        Feuil.set("C7", "mm")
        Feuil.set("D7", "mm")
        Feuil.set("E7", "mm")
        L="8"
        Feuil.set("A"+L, "Poids_entree")
        Feuil.set("B"+L, "100.0")
        Feuil.set("C"+L, "100.0")
        Feuil.set("D"+L, "100.0")
        Feuil.set("E"+L, "100.0")
        Feuil.setAlias("B"+L, "PoE1")
        Feuil.setAlias("C"+L, "PoE2")
        Feuil.setAlias("D"+L, "PoE3")
        Feuil.setAlias("E"+L, "PoE4")
        L="9"
        Feuil.set("A"+L, "Poids_sortie")
        Feuil.set("B"+L, "100.0")
        Feuil.set("C"+L, "100.0")
        Feuil.set("D"+L, "100.0")
        Feuil.set("E"+L, "100.0")
        Feuil.setAlias("B"+L, "PoS1")
        Feuil.setAlias("C"+L, "PoS2")
        Feuil.setAlias("D"+L, "PoS3")
        Feuil.setAlias("E"+L, "PoS4")
        L="10"
        Feuil.set("A"+L, "Long_entree")
        Feuil.set("B"+L, "208.67")
        Feuil.set("C"+L, "286.6")
        Feuil.set("D"+L, "363.13")
        Feuil.set("E"+L, "436.06")
        Feuil.setAlias("B"+L, "LoE1")
        Feuil.setAlias("C"+L, "LoE2")
        Feuil.setAlias("D"+L, "LoE3")
        Feuil.setAlias("E"+L, "LoE4")
        L="11"
        Feuil.set("A"+L, "Long_sortie")
        Feuil.set("B"+L, "208.67")
        Feuil.set("C"+L, "286.6")
        Feuil.set("D"+L, "363.13")
        Feuil.set("E"+L, "436.06")
        Feuil.setAlias("B"+L, "LoS1")
        Feuil.setAlias("C"+L, "LoS2")
        Feuil.setAlias("D"+L, "LoS3")
        Feuil.setAlias("E"+L, "LoS4")
#       Loi d'épaisseur 6 noeuds, le premier fixe à (0,0)
#       Extrados
        L="12"
        Feuil.set("A"+L, "EpEx1X")
        Feuil.set("B"+L, "0.0")
        Feuil.set("C"+L, "0.0")
        Feuil.set("D"+L, "0.0")
        Feuil.set("E"+L, "0.0")
        Feuil.setAlias("B"+L, "EpEx1X1")
        Feuil.setAlias("C"+L, "EpEx1X2")
        Feuil.setAlias("D"+L, "EpEx1X3")
        Feuil.setAlias("E"+L, "EpEx1X4")
        L="13"
        Feuil.set("A"+L, "EpEx2X")
        Feuil.set("B"+L, "300.0")
        Feuil.set("C"+L, "300.0")
        Feuil.set("D"+L, "300.0")
        Feuil.set("E"+L, "300.0")
        Feuil.setAlias("B"+L, "EpEx2X1")
        Feuil.setAlias("C"+L, "EpEx2X2")
        Feuil.setAlias("D"+L, "EpEx2X3")
        Feuil.setAlias("E"+L, "EpEx2X4")
        L="14"
        Feuil.set("A"+L, "EpEx3X")
        Feuil.set("B"+L, "750.0")
        Feuil.set("C"+L, "750.0")
        Feuil.set("D"+L, "750.0")
        Feuil.set("E"+L, "750.0")
        Feuil.setAlias("B"+L, "EpEx3X1")
        Feuil.setAlias("C"+L, "EpEx3X2")
        Feuil.setAlias("D"+L, "EpEx3X3")
        Feuil.setAlias("E"+L, "EpEx3X4")
        L="15"
        Feuil.set("A"+L, "EpEx4X")
        Feuil.set("B"+L, "1000.0")
        Feuil.set("C"+L, "1000.0")
        Feuil.set("D"+L, "1000.0")
        Feuil.set("E"+L, "1000.0")
        Feuil.setAlias("B"+L, "EpEx4X1")
        Feuil.setAlias("C"+L, "EpEx4X2")
        Feuil.setAlias("D"+L, "EpEx4X3")
        Feuil.setAlias("E"+L, "EpEx4X4")
        L="16"
        Feuil.set("A"+L, "EpEx5X") #ne peut être modifié
        Feuil.set("B"+L, "1000.0")
        Feuil.set("C"+L, "1000.0")
        Feuil.set("D"+L, "1000.0")
        Feuil.set("E"+L, "1000.0")
        Feuil.setAlias("B"+L, "EpEx5X1")
        Feuil.setAlias("C"+L, "EpEx5X2")
        Feuil.setAlias("D"+L, "EpEx5X3")
        Feuil.setAlias("E"+L, "EpEx5X4")

        L="17"
        Feuil.set("A"+L, "EpEx1Y")
        Feuil.set("B"+L, "50.0")
        Feuil.set("C"+L, "50.0")
        Feuil.set("D"+L, "50.0")
        Feuil.set("E"+L, "50.0")
        Feuil.setAlias("B"+L, "EpEx1Y1")
        Feuil.setAlias("C"+L, "EpEx1Y2")
        Feuil.setAlias("D"+L, "EpEx1Y3")
        Feuil.setAlias("E"+L, "EpEx1Y4")
        L="18"
        Feuil.set("A"+L, "EpEx2Y")
        Feuil.set("B"+L, "50.0")
        Feuil.set("C"+L, "50.0")
        Feuil.set("D"+L, "50.0")
        Feuil.set("E"+L, "50.0")
        Feuil.setAlias("B"+L, "EpEx2Y1")
        Feuil.setAlias("C"+L, "EpEx2Y2")
        Feuil.setAlias("D"+L, "EpEx2Y3")
        Feuil.setAlias("E"+L, "EpEx2Y4")
        L="19"
        Feuil.set("A"+L, "EpEx3Y")
        Feuil.set("B"+L, "0.0")
        Feuil.set("C"+L, "0.0")
        Feuil.set("D"+L, "0.0")
        Feuil.set("E"+L, "0.0")
        Feuil.setAlias("B"+L, "EpEx3Y1")
        Feuil.setAlias("C"+L, "EpEx3Y2")
        Feuil.setAlias("D"+L, "EpEx3Y3")
        Feuil.setAlias("E"+L, "EpEx3Y4")
        L="20"
        Feuil.set("A"+L, "EpEx4Y")
        Feuil.set("B"+L, "0.0")
        Feuil.set("C"+L, "0.0")
        Feuil.set("D"+L, "0.0")
        Feuil.set("E"+L, "0.0")
        Feuil.setAlias("B"+L, "EpEx4Y1")
        Feuil.setAlias("C"+L, "EpEx4Y2")
        Feuil.setAlias("D"+L, "EpEx4Y3")
        Feuil.setAlias("E"+L, "EpEx4Y4")
        L="21"
        Feuil.set("A"+L, "EpEx5Y")
        Feuil.set("B"+L, "0.0")
        Feuil.set("C"+L, "0.0")
        Feuil.set("D"+L, "0.0")
        Feuil.set("E"+L, "0.0")
        Feuil.setAlias("B"+L, "EpEx5Y1")
        Feuil.setAlias("C"+L, "EpEx5Y2")
        Feuil.setAlias("D"+L, "EpEx5Y3")
        Feuil.setAlias("E"+L, "EpEx5Y4")
        L="22"
        Feuil.set("A"+L, "EpExLast")
        Feuil.set("B"+L, "0.85")
        Feuil.set("C"+L, "0.85")
        Feuil.set("D"+L, "0.85")
        Feuil.set("E"+L, "0.85")
        Feuil.setAlias("B"+L, "EpExLast1")
        Feuil.setAlias("C"+L, "EpExLast2")
        Feuil.setAlias("D"+L, "EpExLast3")
        Feuil.setAlias("E"+L, "EpExLast4")
#       Intrados
        L="23"
        Feuil.set("A"+L, "EpIn1X")
        Feuil.set("B"+L, "0.0")
        Feuil.set("C"+L, "0.0")
        Feuil.set("D"+L, "0.0")
        Feuil.set("E"+L, "0.0")
        Feuil.setAlias("B"+L, "EpIn1X1")
        Feuil.setAlias("C"+L, "EpIn1X2")
        Feuil.setAlias("D"+L, "EpIn1X3")
        Feuil.setAlias("E"+L, "EpIn1X4")
        L="24"
        Feuil.set("A"+L, "EpIn2X")
        Feuil.set("B"+L, "300.0")
        Feuil.set("C"+L, "300.0")
        Feuil.set("D"+L, "300.0")
        Feuil.set("E"+L, "300.0")
        Feuil.setAlias("B"+L, "EpIn2X1")
        Feuil.setAlias("C"+L, "EpIn2X2")
        Feuil.setAlias("D"+L, "EpIn2X3")
        Feuil.setAlias("E"+L, "EpIn2X4")
        L="25"
        Feuil.set("A"+L, "EpIn3X")
        Feuil.set("B"+L, "750.0")
        Feuil.set("C"+L, "750.0")
        Feuil.set("D"+L, "750.0")
        Feuil.set("E"+L, "750.0")
        Feuil.setAlias("B"+L, "EpIn3X1")
        Feuil.setAlias("C"+L, "EpIn3X2")
        Feuil.setAlias("D"+L, "EpIn3X3")
        Feuil.setAlias("E"+L, "EpIn3X4")
        L="26"
        Feuil.set("A"+L, "EpIn4X")
        Feuil.set("B"+L, "1000.0")
        Feuil.set("C"+L, "1000.0")
        Feuil.set("D"+L, "1000.0")
        Feuil.set("E"+L, "1000.0")
        Feuil.setAlias("B"+L, "EpIn4X1")
        Feuil.setAlias("C"+L, "EpIn4X2")
        Feuil.setAlias("D"+L, "EpIn4X3")
        Feuil.setAlias("E"+L, "EpIn4X4")
        L="27"
        Feuil.set("A"+L, "EpIn5X") #ne peut être modifié
        Feuil.set("B"+L, "1000.0")
        Feuil.set("C"+L, "1000.0")
        Feuil.set("D"+L, "1000.0")
        Feuil.set("E"+L, "1000.0")
        Feuil.setAlias("B"+L, "EpIn5X1")
        Feuil.setAlias("C"+L, "EpIn5X2")
        Feuil.setAlias("D"+L, "EpIn5X3")
        Feuil.setAlias("E"+L, "EpIn5X4")
        L="28"
        Feuil.set("A"+L, "EpIn1Y")
        Feuil.set("B"+L, "50.0")
        Feuil.set("C"+L, "50.0")
        Feuil.set("D"+L, "50.0")
        Feuil.set("E"+L, "50.0")
        Feuil.setAlias("B"+L, "EpIn1Y1")
        Feuil.setAlias("C"+L, "EpIn1Y2")
        Feuil.setAlias("D"+L, "EpIn1Y3")
        Feuil.setAlias("E"+L, "EpIn1Y4")
        L="29"
        Feuil.set("A"+L, "EpIn2Y")
        Feuil.set("B"+L, "50.0")
        Feuil.set("C"+L, "50.0")
        Feuil.set("D"+L, "50.0")
        Feuil.set("E"+L, "50.0")
        Feuil.setAlias("B"+L, "EpIn2Y1")
        Feuil.setAlias("C"+L, "EpIn2Y2")
        Feuil.setAlias("D"+L, "EpIn2Y3")
        Feuil.setAlias("E"+L, "EpIn2Y4")
        L="30"
        Feuil.set("A"+L, "EpIn3Y")
        Feuil.set("B"+L, "0.0")
        Feuil.set("C"+L, "0.0")
        Feuil.set("D"+L, "0.0")
        Feuil.set("E"+L, "0.0")
        Feuil.setAlias("B"+L, "EpIn3Y1")
        Feuil.setAlias("C"+L, "EpIn3Y2")
        Feuil.setAlias("D"+L, "EpIn3Y3")
        Feuil.setAlias("E"+L, "EpIn3Y4")
        L="31"
        Feuil.set("A"+L, "EpIn4Y")
        Feuil.set("B"+L, "0.0")
        Feuil.set("C"+L, "0.0")
        Feuil.set("D"+L, "0.0")
        Feuil.set("E"+L, "0.0")
        Feuil.setAlias("B"+L, "EpIn4Y1")
        Feuil.setAlias("C"+L, "EpIn4Y2")
        Feuil.setAlias("D"+L, "EpIn4Y3")
        Feuil.setAlias("E"+L, "EpIn4Y4")
        L="32"
        Feuil.set("A"+L, "EpIn5Y")
        Feuil.set("B"+L, "0.0")
        Feuil.set("C"+L, "0.0")
        Feuil.set("D"+L, "0.0")
        Feuil.set("E"+L, "0.0")
        Feuil.setAlias("B"+L, "EpIn5Y1")
        Feuil.setAlias("C"+L, "EpIn5Y2")
        Feuil.setAlias("D"+L, "EpIn5Y3")
        Feuil.setAlias("E"+L, "EpIn5Y4")
        L="33"
        Feuil.set("A"+L, "EpInLast")
        Feuil.set("B"+L, "0.85")
        Feuil.set("C"+L, "0.85")
        Feuil.set("D"+L, "0.85")
        Feuil.set("E"+L, "0.85")
        Feuil.setAlias("B"+L, "EpInLast1")
        Feuil.setAlias("C"+L, "EpInLast2")
        Feuil.setAlias("D"+L, "EpInLast3")
        Feuil.setAlias("E"+L, "EpInLast4")
#
        Feuil.setAlignment('B1:E33', 'center', 'keep')
        Feuil.setBackground('B1:E1', (1.000000,1.000000,0.498039))
        Feuil.setBackground('B3:E6', (0.666667,1.000000,0.498039))
        Feuil.setBackground('B8:E11', (0.666667,1.000000,0.498039))
        Feuil.setBackground('B12:E33', (0.666667,1.000000,1.000000))
        Feuil.setBackground('B2:E2', (0.752941,0.752941,0.752941))
        Feuil.setBackground('A2:A33', (0.752941,0.752941,0.752941))
        Feuil.setBackground('B7:E7', (0.752941,0.752941,0.752941))
        Feuil.setStyle('B2:E2', 'bold', 'add')
        Feuil.setStyle('B7:E7', 'bold', 'add')
        Feuil.setStyle('A1:A33', 'bold', 'add')
        Feuil.recompute()
        return
    def sauveTableur(self,fp):
    #   Met à jour les pilotes à partir des cellules du tableur
#       print('sauveTableur')
        Feuil=App.ActiveDocument.getObject('Tableau_pilote')
        sketchTheta_entree=App.ActiveDocument.getObject('skTheta_entree')
        sketchTheta_sortie=App.ActiveDocument.getObject('skTheta_sortie')
        sketchAlpha_entree=App.ActiveDocument.getObject('skAlpha_entree')
        sketchAlpha_sortie=App.ActiveDocument.getObject('skAlpha_sortie')
        sketchPoids_entree=App.ActiveDocument.getObject('skPoids_entree')
        sketchPoids_sortie=App.ActiveDocument.getObject('skPoids_sortie')
        sketchLong_entree=App.ActiveDocument.getObject('skLong_entree')
        sketchLong_sortie=App.ActiveDocument.getObject('skLong_sortie')
        sketchEpEx1X=App.ActiveDocument.getObject("skEpEx1X")
        sketchEpEx2X=App.ActiveDocument.getObject("skEpEx2X")
        sketchEpEx3X=App.ActiveDocument.getObject("skEpEx3X")
        sketchEpEx4X=App.ActiveDocument.getObject("skEpEx4X")
        sketchEpEx5X=App.ActiveDocument.getObject("skEpEx5X")
        sketchEpEx1Y=App.ActiveDocument.getObject("skEpEx1Y")
        sketchEpEx2Y=App.ActiveDocument.getObject("skEpEx2Y")
        sketchEpEx3Y=App.ActiveDocument.getObject("skEpEx3Y")
        sketchEpEx4Y=App.ActiveDocument.getObject("skEpEx4Y")
        sketchEpEx5Y=App.ActiveDocument.getObject("skEpEx5Y")
        sketchEpExLast=App.ActiveDocument.getObject("skEpExLast")
        sketchEpIn1X=App.ActiveDocument.getObject("skEpIn1X")
        sketchEpIn2X=App.ActiveDocument.getObject("skEpIn2X")
        sketchEpIn3X=App.ActiveDocument.getObject("skEpIn3X")
        sketchEpIn4X=App.ActiveDocument.getObject("skEpIn4X")
        sketchEpIn5X=App.ActiveDocument.getObject("skEpIn5X")
        sketchEpIn1Y=App.ActiveDocument.getObject("skEpIn1Y")
        sketchEpIn2Y=App.ActiveDocument.getObject("skEpIn2Y")
        sketchEpIn3Y=App.ActiveDocument.getObject("skEpIn3Y")
        sketchEpIn4Y=App.ActiveDocument.getObject("skEpIn4Y")
        sketchEpIn5Y=App.ActiveDocument.getObject("skEpIn5Y")
        sketchEpInLast=App.ActiveDocument.getObject("skEpInLast")
        t0=str(Feuil.B1)+' mm'
        t1=str(Feuil.C1)+' mm'
        t2=str(Feuil.D1)+' mm'
        t3=str(Feuil.E1)+' mm'

        sketchTheta_entree.setDatum(0,App.Units.Quantity(t0))
#       print('0= '+ str(t0))
        sketchTheta_entree.setDatum(1,App.Units.Quantity(str(Feuil.ThE1)+' mm'))
#       print('1= '+str(Feuil.ThE1)+' mm'  )
        sketchTheta_entree.setDatum(2,App.Units.Quantity(t1))
#       print('2= '+ str(t1))
        sketchTheta_entree.setDatum(3,App.Units.Quantity(str(Feuil.ThE2)+' mm'))
#       print('3= '+str(Feuil.ThE2)+' mm'  )
        sketchTheta_entree.setDatum(4,App.Units.Quantity(t2))
#       print('4= '+ str(t2))
        sketchTheta_entree.setDatum(5,App.Units.Quantity(str(Feuil.ThE3)+' mm'))
#       print('5= '+str(Feuil.ThE3)+' mm'  )
        sketchTheta_entree.setDatum(6,App.Units.Quantity(t3))
        sketchTheta_entree.setDatum(7,App.Units.Quantity(str(Feuil.ThE4)+' mm'))
        sketchTheta_sortie.setDatum(0,App.Units.Quantity(t0))
        sketchTheta_sortie.setDatum(1,App.Units.Quantity(str(Feuil.ThS1)+' mm'))
        sketchTheta_sortie.setDatum(2,App.Units.Quantity(t1))
        sketchTheta_sortie.setDatum(3,App.Units.Quantity(str(Feuil.ThS2)+' mm'))
        sketchTheta_sortie.setDatum(4,App.Units.Quantity(t2))
        sketchTheta_sortie.setDatum(5,App.Units.Quantity(str(Feuil.ThS3)+' mm'))
        sketchTheta_sortie.setDatum(6,App.Units.Quantity(t3))
        sketchTheta_sortie.setDatum(7,App.Units.Quantity(str(Feuil.ThS4)+' mm'))
        sketchAlpha_entree.setDatum(0,App.Units.Quantity(t0))
        sketchAlpha_entree.setDatum(1,App.Units.Quantity(str(Feuil.AlE1)+' mm'))
        sketchAlpha_entree.setDatum(2,App.Units.Quantity(t1))
        sketchAlpha_entree.setDatum(3,App.Units.Quantity(str(Feuil.AlE2)+' mm'))
        sketchAlpha_entree.setDatum(4,App.Units.Quantity(t2))
        sketchAlpha_entree.setDatum(5,App.Units.Quantity(str(Feuil.AlE3)+' mm'))
        sketchAlpha_entree.setDatum(6,App.Units.Quantity(t3))
        sketchAlpha_entree.setDatum(7,App.Units.Quantity(str(Feuil.AlE4)+' mm'))
        sketchAlpha_sortie.setDatum(0,App.Units.Quantity(t0))
        sketchAlpha_sortie.setDatum(1,App.Units.Quantity(str(Feuil.AlS1)+' mm'))
        sketchAlpha_sortie.setDatum(2,App.Units.Quantity(t1))
        sketchAlpha_sortie.setDatum(3,App.Units.Quantity(str(Feuil.AlS2)+' mm'))
        sketchAlpha_sortie.setDatum(4,App.Units.Quantity(t2))
        sketchAlpha_sortie.setDatum(5,App.Units.Quantity(str(Feuil.AlS3)+' mm'))
        sketchAlpha_sortie.setDatum(6,App.Units.Quantity(t3))
        sketchAlpha_sortie.setDatum(7,App.Units.Quantity(str(Feuil.AlS4)+' mm'))
        sketchPoids_entree.setDatum(0,App.Units.Quantity(t0))
        sketchPoids_entree.setDatum(1,App.Units.Quantity(str(Feuil.PoE1)+' mm'))
        sketchPoids_entree.setDatum(2,App.Units.Quantity(t1))
        sketchPoids_entree.setDatum(3,App.Units.Quantity(str(Feuil.PoE2)+' mm'))
        sketchPoids_entree.setDatum(4,App.Units.Quantity(t2))
        sketchPoids_entree.setDatum(5,App.Units.Quantity(str(Feuil.PoE3)+' mm'))
        sketchPoids_entree.setDatum(6,App.Units.Quantity(t3))
        sketchPoids_entree.setDatum(7,App.Units.Quantity(str(Feuil.PoE4)+' mm'))
        sketchPoids_sortie.setDatum(0,App.Units.Quantity(t0))
        sketchPoids_sortie.setDatum(1,App.Units.Quantity(str(Feuil.PoS1)+' mm'))
        sketchPoids_sortie.setDatum(2,App.Units.Quantity(t1))
        sketchPoids_sortie.setDatum(3,App.Units.Quantity(str(Feuil.PoS2)+' mm'))
        sketchPoids_sortie.setDatum(4,App.Units.Quantity(t2))
        sketchPoids_sortie.setDatum(5,App.Units.Quantity(str(Feuil.PoS3)+' mm'))
        sketchPoids_sortie.setDatum(6,App.Units.Quantity(t3))
        sketchPoids_sortie.setDatum(7,App.Units.Quantity(str(Feuil.PoS4)+' mm'))
        sketchLong_entree.setDatum(0,App.Units.Quantity(t0))
        sketchLong_entree.setDatum(1,App.Units.Quantity(str(Feuil.LoE1)+' mm'))
        sketchLong_entree.setDatum(2,App.Units.Quantity(t1))
        sketchLong_entree.setDatum(3,App.Units.Quantity(str(Feuil.LoE2)+' mm'))
        sketchLong_entree.setDatum(4,App.Units.Quantity(t2))
        sketchLong_entree.setDatum(5,App.Units.Quantity(str(Feuil.LoE3)+' mm'))
        sketchLong_entree.setDatum(6,App.Units.Quantity(t3))
        sketchLong_entree.setDatum(7,App.Units.Quantity(str(Feuil.LoE4)+' mm'))
        sketchLong_sortie.setDatum(0,App.Units.Quantity(t0))
        sketchLong_sortie.setDatum(1,App.Units.Quantity(str(Feuil.LoS1)+' mm'))
        sketchLong_sortie.setDatum(2,App.Units.Quantity(t1))
        sketchLong_sortie.setDatum(3,App.Units.Quantity(str(Feuil.LoS2)+' mm'))
        sketchLong_sortie.setDatum(4,App.Units.Quantity(t2))
        sketchLong_sortie.setDatum(5,App.Units.Quantity(str(Feuil.LoS3)+' mm'))
        sketchLong_sortie.setDatum(6,App.Units.Quantity(t3))
        sketchLong_sortie.setDatum(7,App.Units.Quantity(str(Feuil.LoS4)+' mm'))
#       Epaisseur extrados
#       X
        sketchEpEx1X.setDatum(0,App.Units.Quantity(t0))
        sketchEpEx1X.setDatum(1,App.Units.Quantity(str(Feuil.EpEx1X1)+' mm'))
        sketchEpEx1X.setDatum(2,App.Units.Quantity(t1))
        sketchEpEx1X.setDatum(3,App.Units.Quantity(str(Feuil.EpEx1X2)+' mm'))
        sketchEpEx1X.setDatum(4,App.Units.Quantity(t2))
        sketchEpEx1X.setDatum(5,App.Units.Quantity(str(Feuil.EpEx1X3)+' mm'))
        sketchEpEx1X.setDatum(6,App.Units.Quantity(t3))
        sketchEpEx1X.setDatum(7,App.Units.Quantity(str(Feuil.EpEx1X4)+' mm'))
        sketchEpEx2X.setDatum(0,App.Units.Quantity(t0))
        sketchEpEx2X.setDatum(1,App.Units.Quantity(str(Feuil.EpEx2X1)+' mm'))
        sketchEpEx2X.setDatum(2,App.Units.Quantity(t1))
        sketchEpEx2X.setDatum(3,App.Units.Quantity(str(Feuil.EpEx2X2)+' mm'))
        sketchEpEx2X.setDatum(4,App.Units.Quantity(t2))
        sketchEpEx2X.setDatum(5,App.Units.Quantity(str(Feuil.EpEx2X3)+' mm'))
        sketchEpEx2X.setDatum(6,App.Units.Quantity(t3))
        sketchEpEx2X.setDatum(7,App.Units.Quantity(str(Feuil.EpEx2X4)+' mm'))
        sketchEpEx3X.setDatum(0,App.Units.Quantity(t0))
        sketchEpEx3X.setDatum(1,App.Units.Quantity(str(Feuil.EpEx3X1)+' mm'))
        sketchEpEx3X.setDatum(2,App.Units.Quantity(t1))
        sketchEpEx3X.setDatum(3,App.Units.Quantity(str(Feuil.EpEx3X2)+' mm'))
        sketchEpEx3X.setDatum(4,App.Units.Quantity(t2))
        sketchEpEx3X.setDatum(5,App.Units.Quantity(str(Feuil.EpEx3X3)+' mm'))
        sketchEpEx3X.setDatum(6,App.Units.Quantity(t3))
        sketchEpEx3X.setDatum(7,App.Units.Quantity(str(Feuil.EpEx3X4)+' mm'))
        sketchEpEx4X.setDatum(0,App.Units.Quantity(t0))
        sketchEpEx4X.setDatum(1,App.Units.Quantity(str(Feuil.EpEx4X1)+' mm'))
        sketchEpEx4X.setDatum(2,App.Units.Quantity(t1))
        sketchEpEx4X.setDatum(3,App.Units.Quantity(str(Feuil.EpEx4X2)+' mm'))
        sketchEpEx4X.setDatum(4,App.Units.Quantity(t2))
        sketchEpEx4X.setDatum(5,App.Units.Quantity(str(Feuil.EpEx4X3)+' mm'))
        sketchEpEx4X.setDatum(6,App.Units.Quantity(t3))
        sketchEpEx4X.setDatum(7,App.Units.Quantity(str(Feuil.EpEx4X4)+' mm'))
        sketchEpEx5X.setDatum(0,App.Units.Quantity(t0))
        sketchEpEx5X.setDatum(1,App.Units.Quantity(str(Feuil.EpEx5X1)+' mm'))
        sketchEpEx5X.setDatum(2,App.Units.Quantity(t1))
        sketchEpEx5X.setDatum(3,App.Units.Quantity(str(Feuil.EpEx5X2)+' mm'))
        sketchEpEx5X.setDatum(4,App.Units.Quantity(t2))
        sketchEpEx5X.setDatum(5,App.Units.Quantity(str(Feuil.EpEx5X3)+' mm'))
        sketchEpEx5X.setDatum(6,App.Units.Quantity(t3))
        sketchEpEx5X.setDatum(7,App.Units.Quantity(str(Feuil.EpEx5X4)+' mm'))
#       Y
        sketchEpEx1Y.setDatum(0,App.Units.Quantity(t0))
        sketchEpEx1Y.setDatum(1,App.Units.Quantity(str(Feuil.EpEx1Y1)+' mm'))
        sketchEpEx1Y.setDatum(2,App.Units.Quantity(t1))
        sketchEpEx1Y.setDatum(3,App.Units.Quantity(str(Feuil.EpEx1Y2)+' mm'))
        sketchEpEx1Y.setDatum(4,App.Units.Quantity(t2))
        sketchEpEx1Y.setDatum(5,App.Units.Quantity(str(Feuil.EpEx1Y3)+' mm'))
        sketchEpEx1Y.setDatum(6,App.Units.Quantity(t3))
        sketchEpEx1Y.setDatum(7,App.Units.Quantity(str(Feuil.EpEx1Y4)+' mm'))
        sketchEpEx2Y.setDatum(0,App.Units.Quantity(t0))
        sketchEpEx2Y.setDatum(1,App.Units.Quantity(str(Feuil.EpEx2Y1)+' mm'))
        sketchEpEx2Y.setDatum(2,App.Units.Quantity(t1))
        sketchEpEx2Y.setDatum(3,App.Units.Quantity(str(Feuil.EpEx2Y2)+' mm'))
        sketchEpEx2Y.setDatum(4,App.Units.Quantity(t2))
        sketchEpEx2Y.setDatum(5,App.Units.Quantity(str(Feuil.EpEx2Y3)+' mm'))
        sketchEpEx2Y.setDatum(6,App.Units.Quantity(t3))
        sketchEpEx2Y.setDatum(7,App.Units.Quantity(str(Feuil.EpEx2Y4)+' mm'))
        sketchEpEx3Y.setDatum(0,App.Units.Quantity(t0))
        sketchEpEx3Y.setDatum(1,App.Units.Quantity(str(Feuil.EpEx3Y1)+' mm'))
        sketchEpEx3Y.setDatum(2,App.Units.Quantity(t1))
        sketchEpEx3Y.setDatum(3,App.Units.Quantity(str(Feuil.EpEx3Y2)+' mm'))
        sketchEpEx3Y.setDatum(4,App.Units.Quantity(t2))
        sketchEpEx3Y.setDatum(5,App.Units.Quantity(str(Feuil.EpEx3Y3)+' mm'))
        sketchEpEx3Y.setDatum(6,App.Units.Quantity(t3))
        sketchEpEx3Y.setDatum(7,App.Units.Quantity(str(Feuil.EpEx3Y4)+' mm'))
        sketchEpEx4Y.setDatum(0,App.Units.Quantity(t0))
        sketchEpEx4Y.setDatum(1,App.Units.Quantity(str(Feuil.EpEx4Y1)+' mm'))
        sketchEpEx4Y.setDatum(2,App.Units.Quantity(t1))
        sketchEpEx4Y.setDatum(3,App.Units.Quantity(str(Feuil.EpEx4Y2)+' mm'))
        sketchEpEx4Y.setDatum(4,App.Units.Quantity(t2))
        sketchEpEx4Y.setDatum(5,App.Units.Quantity(str(Feuil.EpEx4Y3)+' mm'))
        sketchEpEx4Y.setDatum(6,App.Units.Quantity(t3))
        sketchEpEx4Y.setDatum(7,App.Units.Quantity(str(Feuil.EpEx4Y4)+' mm'))
        sketchEpEx5Y.setDatum(0,App.Units.Quantity(t0))
        sketchEpEx5Y.setDatum(1,App.Units.Quantity(str(Feuil.EpEx5Y1)+' mm'))
        sketchEpEx5Y.setDatum(2,App.Units.Quantity(t1))
        sketchEpEx5Y.setDatum(3,App.Units.Quantity(str(Feuil.EpEx5Y2)+' mm'))
        sketchEpEx5Y.setDatum(4,App.Units.Quantity(t2))
        sketchEpEx5Y.setDatum(5,App.Units.Quantity(str(Feuil.EpEx5Y3)+' mm'))
        sketchEpEx5Y.setDatum(6,App.Units.Quantity(t3))
        sketchEpEx5Y.setDatum(7,App.Units.Quantity(str(Feuil.EpEx5Y4)+' mm'))        
        sketchEpExLast.setDatum(0,App.Units.Quantity(t0))
        sketchEpExLast.setDatum(1,App.Units.Quantity(str(Feuil.EpExLast1)+' mm'))
        sketchEpExLast.setDatum(2,App.Units.Quantity(t1))
        sketchEpExLast.setDatum(3,App.Units.Quantity(str(Feuil.EpExLast2)+' mm'))
        sketchEpExLast.setDatum(4,App.Units.Quantity(t2))
        sketchEpExLast.setDatum(5,App.Units.Quantity(str(Feuil.EpExLast3)+' mm'))
        sketchEpExLast.setDatum(6,App.Units.Quantity(t3))
        sketchEpExLast.setDatum(7,App.Units.Quantity(str(Feuil.EpExLast4)+' mm'))
#       Epaisseur intrados
#       X
        sketchEpIn1X.setDatum(0,App.Units.Quantity(t0))
        sketchEpIn1X.setDatum(1,App.Units.Quantity(str(Feuil.EpIn1X1)+' mm'))
        sketchEpIn1X.setDatum(2,App.Units.Quantity(t1))
        sketchEpIn1X.setDatum(3,App.Units.Quantity(str(Feuil.EpIn1X2)+' mm'))
        sketchEpIn1X.setDatum(4,App.Units.Quantity(t2))
        sketchEpIn1X.setDatum(5,App.Units.Quantity(str(Feuil.EpIn1X3)+' mm'))
        sketchEpIn1X.setDatum(6,App.Units.Quantity(t3))
        sketchEpIn1X.setDatum(7,App.Units.Quantity(str(Feuil.EpIn1X4)+' mm'))
        sketchEpIn2X.setDatum(0,App.Units.Quantity(t0))
        sketchEpIn2X.setDatum(1,App.Units.Quantity(str(Feuil.EpIn2X1)+' mm'))
        sketchEpIn2X.setDatum(2,App.Units.Quantity(t1))
        sketchEpIn2X.setDatum(3,App.Units.Quantity(str(Feuil.EpIn2X2)+' mm'))
        sketchEpIn2X.setDatum(4,App.Units.Quantity(t2))
        sketchEpIn2X.setDatum(5,App.Units.Quantity(str(Feuil.EpIn2X3)+' mm'))
        sketchEpIn2X.setDatum(6,App.Units.Quantity(t3))
        sketchEpIn2X.setDatum(7,App.Units.Quantity(str(Feuil.EpIn2X4)+' mm'))
        sketchEpIn3X.setDatum(0,App.Units.Quantity(t0))
        sketchEpIn3X.setDatum(1,App.Units.Quantity(str(Feuil.EpIn3X1)+' mm'))
        sketchEpIn3X.setDatum(2,App.Units.Quantity(t1))
        sketchEpIn3X.setDatum(3,App.Units.Quantity(str(Feuil.EpIn3X2)+' mm'))
        sketchEpIn3X.setDatum(4,App.Units.Quantity(t2))
        sketchEpIn3X.setDatum(5,App.Units.Quantity(str(Feuil.EpIn3X3)+' mm'))
        sketchEpIn3X.setDatum(6,App.Units.Quantity(t3))
        sketchEpIn3X.setDatum(7,App.Units.Quantity(str(Feuil.EpIn3X4)+' mm'))
        sketchEpIn4X.setDatum(0,App.Units.Quantity(t0))
        sketchEpIn4X.setDatum(1,App.Units.Quantity(str(Feuil.EpIn4X1)+' mm'))
        sketchEpIn4X.setDatum(2,App.Units.Quantity(t1))
        sketchEpIn4X.setDatum(3,App.Units.Quantity(str(Feuil.EpIn4X2)+' mm'))
        sketchEpIn4X.setDatum(4,App.Units.Quantity(t2))
        sketchEpIn4X.setDatum(5,App.Units.Quantity(str(Feuil.EpIn4X3)+' mm'))
        sketchEpIn4X.setDatum(6,App.Units.Quantity(t3))
        sketchEpIn4X.setDatum(7,App.Units.Quantity(str(Feuil.EpIn4X4)+' mm'))
        sketchEpIn5X.setDatum(0,App.Units.Quantity(t0))
        sketchEpIn5X.setDatum(1,App.Units.Quantity(str(Feuil.EpIn5X1)+' mm'))
        sketchEpIn5X.setDatum(2,App.Units.Quantity(t1))
        sketchEpIn5X.setDatum(3,App.Units.Quantity(str(Feuil.EpIn5X2)+' mm'))
        sketchEpIn5X.setDatum(4,App.Units.Quantity(t2))
        sketchEpIn5X.setDatum(5,App.Units.Quantity(str(Feuil.EpIn5X3)+' mm'))
        sketchEpIn5X.setDatum(6,App.Units.Quantity(t3))
        sketchEpIn5X.setDatum(7,App.Units.Quantity(str(Feuil.EpIn5X4)+' mm'))
#       Y
        sketchEpIn1Y.setDatum(0,App.Units.Quantity(t0))
        sketchEpIn1Y.setDatum(1,App.Units.Quantity(str(Feuil.EpIn1Y1)+' mm'))
        sketchEpIn1Y.setDatum(2,App.Units.Quantity(t1))
        sketchEpIn1Y.setDatum(3,App.Units.Quantity(str(Feuil.EpIn1Y2)+' mm'))
        sketchEpIn1Y.setDatum(4,App.Units.Quantity(t2))
        sketchEpIn1Y.setDatum(5,App.Units.Quantity(str(Feuil.EpIn1Y3)+' mm'))
        sketchEpIn1Y.setDatum(6,App.Units.Quantity(t3))
        sketchEpIn1Y.setDatum(7,App.Units.Quantity(str(Feuil.EpIn1Y4)+' mm'))
        sketchEpIn2Y.setDatum(0,App.Units.Quantity(t0))
        sketchEpIn2Y.setDatum(1,App.Units.Quantity(str(Feuil.EpIn2Y1)+' mm'))
        sketchEpIn2Y.setDatum(2,App.Units.Quantity(t1))
        sketchEpIn2Y.setDatum(3,App.Units.Quantity(str(Feuil.EpIn2Y2)+' mm'))
        sketchEpIn2Y.setDatum(4,App.Units.Quantity(t2))
        sketchEpIn2Y.setDatum(5,App.Units.Quantity(str(Feuil.EpIn2Y3)+' mm'))
        sketchEpIn2Y.setDatum(6,App.Units.Quantity(t3))
        sketchEpIn2Y.setDatum(7,App.Units.Quantity(str(Feuil.EpIn2Y4)+' mm'))
        sketchEpIn3Y.setDatum(0,App.Units.Quantity(t0))
        sketchEpIn3Y.setDatum(1,App.Units.Quantity(str(Feuil.EpIn3Y1)+' mm'))
        sketchEpIn3Y.setDatum(2,App.Units.Quantity(t1))
        sketchEpIn3Y.setDatum(3,App.Units.Quantity(str(Feuil.EpIn3Y2)+' mm'))
        sketchEpIn3Y.setDatum(4,App.Units.Quantity(t2))
        sketchEpIn3Y.setDatum(5,App.Units.Quantity(str(Feuil.EpIn3Y3)+' mm'))
        sketchEpIn3Y.setDatum(6,App.Units.Quantity(t3))
        sketchEpIn3Y.setDatum(7,App.Units.Quantity(str(Feuil.EpIn3Y4)+' mm'))
        sketchEpIn4Y.setDatum(0,App.Units.Quantity(t0))
        sketchEpIn4Y.setDatum(1,App.Units.Quantity(str(Feuil.EpIn4Y1)+' mm'))
        sketchEpIn4Y.setDatum(2,App.Units.Quantity(t1))
        sketchEpIn4Y.setDatum(3,App.Units.Quantity(str(Feuil.EpIn4Y2)+' mm'))
        sketchEpIn4Y.setDatum(4,App.Units.Quantity(t2))
        sketchEpIn4Y.setDatum(5,App.Units.Quantity(str(Feuil.EpIn4Y3)+' mm'))
        sketchEpIn4Y.setDatum(6,App.Units.Quantity(t3))
        sketchEpIn4Y.setDatum(7,App.Units.Quantity(str(Feuil.EpIn4Y4)+' mm'))
        sketchEpIn5Y.setDatum(0,App.Units.Quantity(t0))
        sketchEpIn5Y.setDatum(1,App.Units.Quantity(str(Feuil.EpIn5Y1)+' mm'))
        sketchEpIn5Y.setDatum(2,App.Units.Quantity(t1))
        sketchEpIn5Y.setDatum(3,App.Units.Quantity(str(Feuil.EpIn5Y2)+' mm'))
        sketchEpIn5Y.setDatum(4,App.Units.Quantity(t2))
        sketchEpIn5Y.setDatum(5,App.Units.Quantity(str(Feuil.EpIn5Y3)+' mm'))
        sketchEpIn5Y.setDatum(6,App.Units.Quantity(t3))
        sketchEpIn5Y.setDatum(7,App.Units.Quantity(str(Feuil.EpIn5Y4)+' mm'))        
        sketchEpInLast.setDatum(0,App.Units.Quantity(t0))
        sketchEpInLast.setDatum(1,App.Units.Quantity(str(Feuil.EpInLast1)+' mm'))
        sketchEpInLast.setDatum(2,App.Units.Quantity(t1))
        sketchEpInLast.setDatum(3,App.Units.Quantity(str(Feuil.EpInLast2)+' mm'))
        sketchEpInLast.setDatum(4,App.Units.Quantity(t2))
        sketchEpInLast.setDatum(5,App.Units.Quantity(str(Feuil.EpInLast3)+' mm'))
        sketchEpInLast.setDatum(6,App.Units.Quantity(t3))
        sketchEpInLast.setDatum(7,App.Units.Quantity(str(Feuil.EpInLast4)+' mm'))
        App.ActiveDocument.recompute()
#       print("sauveTableur - fin")
        return
#
#
#       Plan méridien
#
#
    def initMeridien(self,fp):
#       print("initMeridien")
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
#       print('Plan méridien : ')
#       print(sketch.Name)
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
#       print("initMeridien-fin")
        return
    def traceMeridien(self,fp):
#       print('traceMeridien')
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
#       print('fpCiso créé vide')
        docPlanMeridien.addObject(fpCiso)
#       print('mis dans le groupe Plan_Meridien')
        fpCiso.Label='IsoCurve'
        fpCiso.Face=(surfMeridien,['Face1',])
#       print('fpCiso attribut Face1')
        fpCiso.NumberU=fp.Nfilets
        fpCiso.NumberV=0
#        fpCiso.recompute()
    #
    #   Discretisation des filets
    #
        i=0
        for edge in fpCiso.Shape.Edges:
            I=str(i+1)
    #       print(I)
            fpM = App.ActiveDocument.addObject("Part::FeaturePython","FiletM"+I)
            docPlanMeridien.addObject(fpM)
            Discretize.Discretization(fpM, (App.ActiveDocument.getObject("IsoCurve"),"Edge"+I))
            fpM.Number=fp.Npts
            Discretize.ViewProviderDisc(fpM.ViewObject)
            fpM.ViewObject.PointSize = 3
#            fpM.recompute()
            i+=1
        App.ActiveDocument.recompute()
#       print('traceMeridien - fin')
        return  
    def sauveMeridien(self,fp):
        # Sauve dans Parametres les points du sketch Meridien après une modification par l'usager
#       print('sauveMeridien')
        fp.Init=False
        sketch=App.ActiveDocument.Meridien
        LoiMeridien=[]
        for i in range(0,24,2) : LoiMeridien.append(App.Vector(sketch.Constraints[i].Value,sketch.Constraints[i+1].Value,0))
        fp.Meridien=LoiMeridien
        App.ActiveDocument.recompute()
#       print('sauveMeridien - fin')
        return

#
#
#       Plan des épaisseurs
#
#
    def initEpaisseur(self,fp):
#       print("initEpaisseur")
    #
    #   Routine pour créer les splines à 6 points(0,1,2,3,4,5) qui pilotent les variables:
    #
    
    #   EpEx1X -> position en x du point 1 qui contrôle l'épaisseur l'extrados
    #   EpIn2X -> ....   ....   pour l'intrados
    #   ...
    #   ...
    #   EpExLast -> position en x de la troncature du profil au bord de fuite pour l'extrados
    #   EpInLast -> ....   ....   pour l'intrados
    #   Extrados
        docPilote = App.ActiveDocument.getObject("Pilote")
        Feuil= App.ActiveDocument.getObject("Tableau_pilote")
        sketchEpEx1X=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpEx1X')
        docPilote.addObject(sketchEpEx1X)
        sketchEpEx2X=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpEx2X')
        docPilote.addObject(sketchEpEx2X)
        sketchEpEx3X=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpEx3X')
        docPilote.addObject(sketchEpEx3X)
        sketchEpEx4X=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpEx4X')
        docPilote.addObject(sketchEpEx4X)
        sketchEpEx5X=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpEx5X')
        docPilote.addObject(sketchEpEx5X)        
        sketchEpEx1Y=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpEx1Y')
        docPilote.addObject(sketchEpEx1Y)
        sketchEpEx2Y=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpEx2Y')
        docPilote.addObject(sketchEpEx2Y)
        sketchEpEx3Y=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpEx3Y')
        docPilote.addObject(sketchEpEx3Y)
        sketchEpEx4Y=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpEx4Y')
        docPilote.addObject(sketchEpEx4Y)
        sketchEpEx5Y=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpEx5Y')
        docPilote.addObject(sketchEpEx5Y)
        sketchEpExLast=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpExLast')
        docPilote.addObject(sketchEpExLast)
 #      Intrados
        sketchEpIn1X=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpIn1X')
        docPilote.addObject(sketchEpIn1X)
        sketchEpIn2X=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpIn2X')
        docPilote.addObject(sketchEpIn2X)
        sketchEpIn3X=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpIn3X')
        docPilote.addObject(sketchEpIn3X)
        sketchEpIn4X=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpIn4X')
        docPilote.addObject(sketchEpIn4X)
        sketchEpIn5X=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpIn5X')
        docPilote.addObject(sketchEpIn5X)        
        sketchEpIn1Y=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpIn1Y')
        docPilote.addObject(sketchEpIn1Y)
        sketchEpIn2Y=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpIn2Y')
        docPilote.addObject(sketchEpIn2Y)
        sketchEpIn3Y=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpIn3Y')
        docPilote.addObject(sketchEpIn3Y)
        sketchEpIn4Y=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpIn4Y')
        docPilote.addObject(sketchEpIn4Y)
        sketchEpIn5Y=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpIn5Y')
        docPilote.addObject(sketchEpIn5Y)
        sketchEpInLast=App.ActiveDocument.addObject('Sketcher::SketchObject','skEpInLast')
        docPilote.addObject(sketchEpInLast)     
     #   les abscisses des esquisses sont fonction de t, t variant de 0 à 100 mm dans FreeCAD
        t1=Feuil.B1
        t2=Feuil.C1
        t3=Feuil.D1
        t4=Feuil.E1
    #
    #   Initialisation des variables
    #
    #   Loi déterminant l'épaisseur dans les sketch
    # 
    #   Extrados
        Pt0=sketchEpEx1X.addGeometry(Part.Point(App.Vector(t1, Feuil.EpEx1X1, 0)))
        Pt1=sketchEpEx1X.addGeometry(Part.Point(App.Vector(t2, Feuil.EpEx1X2, 0)))
        Pt2=sketchEpEx1X.addGeometry(Part.Point(App.Vector(t3, Feuil.EpEx1X3, 0)))
        Pt3=sketchEpEx1X.addGeometry(Part.Point(App.Vector(t4, Feuil.EpEx1X4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpEx1X, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpEx1X, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpEx1X, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpEx1X, Pt3, "PtEx3")
        self.planBS(sketchEpEx1X,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpEx2X.addGeometry(Part.Point(App.Vector(t1, Feuil.EpEx2X1, 0)))
        Pt1=sketchEpEx2X.addGeometry(Part.Point(App.Vector(t2, Feuil.EpEx2X2, 0)))
        Pt2=sketchEpEx2X.addGeometry(Part.Point(App.Vector(t3, Feuil.EpEx2X3, 0)))
        Pt3=sketchEpEx2X.addGeometry(Part.Point(App.Vector(t4, Feuil.EpEx2X4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpEx2X, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpEx2X, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpEx2X, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpEx2X, Pt3, "PtEx3")
        self.planBS(sketchEpEx2X,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpEx3X.addGeometry(Part.Point(App.Vector(t1, Feuil.EpEx3X1, 0)))
        Pt1=sketchEpEx3X.addGeometry(Part.Point(App.Vector(t2, Feuil.EpEx3X2, 0)))
        Pt2=sketchEpEx3X.addGeometry(Part.Point(App.Vector(t3, Feuil.EpEx3X3, 0)))
        Pt3=sketchEpEx3X.addGeometry(Part.Point(App.Vector(t4, Feuil.EpEx3X4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpEx3X, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpEx3X, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpEx3X, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpEx3X, Pt3, "PtEx3")
        self.planBS(sketchEpEx3X,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpEx4X.addGeometry(Part.Point(App.Vector(t1, Feuil.EpEx4X1, 0)))
        Pt1=sketchEpEx4X.addGeometry(Part.Point(App.Vector(t2, Feuil.EpEx4X2, 0)))
        Pt2=sketchEpEx4X.addGeometry(Part.Point(App.Vector(t3, Feuil.EpEx4X3, 0)))
        Pt3=sketchEpEx4X.addGeometry(Part.Point(App.Vector(t4, Feuil.EpEx4X4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpEx4X, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpEx4X, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpEx4X, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpEx4X, Pt3, "PtEx3")
        self.planBS(sketchEpEx4X,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpEx5X.addGeometry(Part.Point(App.Vector(t1, Feuil.EpEx5X1, 0)))
        Pt1=sketchEpEx5X.addGeometry(Part.Point(App.Vector(t2, Feuil.EpEx5X2, 0)))
        Pt2=sketchEpEx5X.addGeometry(Part.Point(App.Vector(t3, Feuil.EpEx5X3, 0)))
        Pt3=sketchEpEx5X.addGeometry(Part.Point(App.Vector(t4, Feuil.EpEx5X4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpEx5X, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpEx5X, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpEx5X, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpEx5X, Pt3, "PtEx3")
        self.planBS(sketchEpEx5X,Pt0, Pt1, Pt2, Pt3)
#
        Pt0=sketchEpEx1Y.addGeometry(Part.Point(App.Vector(t1, Feuil.EpEx1Y1, 0)))
        Pt1=sketchEpEx1Y.addGeometry(Part.Point(App.Vector(t2, Feuil.EpEx1Y2, 0)))
        Pt2=sketchEpEx1Y.addGeometry(Part.Point(App.Vector(t3, Feuil.EpEx1Y3, 0)))
        Pt3=sketchEpEx1Y.addGeometry(Part.Point(App.Vector(t4, Feuil.EpEx1Y4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpEx1Y, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpEx1Y, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpEx1Y, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpEx1Y, Pt3, "PtEx3")
        self.planBS(sketchEpEx1Y,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpEx2Y.addGeometry(Part.Point(App.Vector(t1, Feuil.EpEx2Y1, 0)))
        Pt1=sketchEpEx2Y.addGeometry(Part.Point(App.Vector(t2, Feuil.EpEx2Y2, 0)))
        Pt2=sketchEpEx2Y.addGeometry(Part.Point(App.Vector(t3, Feuil.EpEx2Y3, 0)))
        Pt3=sketchEpEx2Y.addGeometry(Part.Point(App.Vector(t4, Feuil.EpEx2Y4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpEx2Y, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpEx2Y, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpEx2Y, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpEx2Y, Pt3, "PtEx3")
        self.planBS(sketchEpEx2Y,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpEx3Y.addGeometry(Part.Point(App.Vector(t1, Feuil.EpEx3Y1, 0)))
        Pt1=sketchEpEx3Y.addGeometry(Part.Point(App.Vector(t2, Feuil.EpEx3Y2, 0)))
        Pt2=sketchEpEx3Y.addGeometry(Part.Point(App.Vector(t3, Feuil.EpEx3Y3, 0)))
        Pt3=sketchEpEx3Y.addGeometry(Part.Point(App.Vector(t4, Feuil.EpEx3Y4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpEx3Y, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpEx3Y, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpEx3Y, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpEx3Y, Pt3, "PtEx3")
        self.planBS(sketchEpEx3Y,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpEx4Y.addGeometry(Part.Point(App.Vector(t1, Feuil.EpEx4Y1, 0)))
        Pt1=sketchEpEx4Y.addGeometry(Part.Point(App.Vector(t2, Feuil.EpEx4Y2, 0)))
        Pt2=sketchEpEx4Y.addGeometry(Part.Point(App.Vector(t3, Feuil.EpEx4Y3, 0)))
        Pt3=sketchEpEx4Y.addGeometry(Part.Point(App.Vector(t4, Feuil.EpEx4Y4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpEx4Y, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpEx4Y, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpEx4Y, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpEx4Y, Pt3, "PtEx3")
        self.planBS(sketchEpEx4Y,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpEx5Y.addGeometry(Part.Point(App.Vector(t1, Feuil.EpEx5Y1, 0)))
        Pt1=sketchEpEx5Y.addGeometry(Part.Point(App.Vector(t2, Feuil.EpEx5Y2, 0)))
        Pt2=sketchEpEx5Y.addGeometry(Part.Point(App.Vector(t3, Feuil.EpEx5Y3, 0)))
        Pt3=sketchEpEx5Y.addGeometry(Part.Point(App.Vector(t4, Feuil.EpEx5Y4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpEx5Y, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpEx5Y, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpEx5Y, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpEx5Y, Pt3, "PtEx3")
        self.planBS(sketchEpEx5Y,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpExLast.addGeometry(Part.Point(App.Vector(t1, Feuil.EpExLast1, 0)))
        Pt1=sketchEpExLast.addGeometry(Part.Point(App.Vector(t2, Feuil.EpExLast2, 0)))
        Pt2=sketchEpExLast.addGeometry(Part.Point(App.Vector(t3, Feuil.EpExLast3, 0)))
        Pt3=sketchEpExLast.addGeometry(Part.Point(App.Vector(t4, Feuil.EpExLast4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpExLast, Pt0, "PtEx0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpExLast, Pt1, "PtEx1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpExLast, Pt2, "PtEx2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpExLast, Pt3, "PtEx3")
        self.planBS(sketchEpExLast,Pt0, Pt1, Pt2, Pt3)
#
#   Intrados
        Pt0=sketchEpIn1X.addGeometry(Part.Point(App.Vector(t1, Feuil.EpIn1X1, 0)))
        Pt1=sketchEpIn1X.addGeometry(Part.Point(App.Vector(t2, Feuil.EpIn1X2, 0)))
        Pt2=sketchEpIn1X.addGeometry(Part.Point(App.Vector(t3, Feuil.EpIn1X3, 0)))
        Pt3=sketchEpIn1X.addGeometry(Part.Point(App.Vector(t4, Feuil.EpIn1X4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpIn1X, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpIn1X, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpIn1X, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpIn1X, Pt3, "PtIn3")
        self.planBS(sketchEpIn1X,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpIn2X.addGeometry(Part.Point(App.Vector(t1, Feuil.EpIn2X1, 0)))
        Pt1=sketchEpIn2X.addGeometry(Part.Point(App.Vector(t2, Feuil.EpIn2X2, 0)))
        Pt2=sketchEpIn2X.addGeometry(Part.Point(App.Vector(t3, Feuil.EpIn2X3, 0)))
        Pt3=sketchEpIn2X.addGeometry(Part.Point(App.Vector(t4, Feuil.EpIn2X4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpIn2X, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpIn2X, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpIn2X, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpIn2X, Pt3, "PtIn3")
        self.planBS(sketchEpIn2X,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpIn3X.addGeometry(Part.Point(App.Vector(t1, Feuil.EpIn3X1, 0)))
        Pt1=sketchEpIn3X.addGeometry(Part.Point(App.Vector(t2, Feuil.EpIn3X2, 0)))
        Pt2=sketchEpIn3X.addGeometry(Part.Point(App.Vector(t3, Feuil.EpIn3X3, 0)))
        Pt3=sketchEpIn3X.addGeometry(Part.Point(App.Vector(t4, Feuil.EpIn3X4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpIn3X, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpIn3X, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpIn3X, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpIn3X, Pt3, "PtIn3")
        self.planBS(sketchEpIn3X,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpIn4X.addGeometry(Part.Point(App.Vector(t1, Feuil.EpIn4X1, 0)))
        Pt1=sketchEpIn4X.addGeometry(Part.Point(App.Vector(t2, Feuil.EpIn4X2, 0)))
        Pt2=sketchEpIn4X.addGeometry(Part.Point(App.Vector(t3, Feuil.EpIn4X3, 0)))
        Pt3=sketchEpIn4X.addGeometry(Part.Point(App.Vector(t4, Feuil.EpIn4X4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpIn4X, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpIn4X, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpIn4X, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpIn4X, Pt3, "PtIn3")
        self.planBS(sketchEpIn4X,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpIn5X.addGeometry(Part.Point(App.Vector(t1, Feuil.EpIn5X1, 0)))
        Pt1=sketchEpIn5X.addGeometry(Part.Point(App.Vector(t2, Feuil.EpIn5X2, 0)))
        Pt2=sketchEpIn5X.addGeometry(Part.Point(App.Vector(t3, Feuil.EpIn5X3, 0)))
        Pt3=sketchEpIn5X.addGeometry(Part.Point(App.Vector(t4, Feuil.EpIn5X4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpIn5X, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpIn5X, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpIn5X, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpIn5X, Pt3, "PtIn3")
        self.planBS(sketchEpIn5X,Pt0, Pt1, Pt2, Pt3)
#
        Pt0=sketchEpIn1Y.addGeometry(Part.Point(App.Vector(t1, Feuil.EpIn1Y1, 0)))
        Pt1=sketchEpIn1Y.addGeometry(Part.Point(App.Vector(t2, Feuil.EpIn1Y2, 0)))
        Pt2=sketchEpIn1Y.addGeometry(Part.Point(App.Vector(t3, Feuil.EpIn1Y3, 0)))
        Pt3=sketchEpIn1Y.addGeometry(Part.Point(App.Vector(t4, Feuil.EpIn1Y4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpIn1Y, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpIn1Y, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpIn1Y, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpIn1Y, Pt3, "PtIn3")
        self.planBS(sketchEpIn1Y,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpIn2Y.addGeometry(Part.Point(App.Vector(t1, Feuil.EpIn2Y1, 0)))
        Pt1=sketchEpIn2Y.addGeometry(Part.Point(App.Vector(t2, Feuil.EpIn2Y2, 0)))
        Pt2=sketchEpIn2Y.addGeometry(Part.Point(App.Vector(t3, Feuil.EpIn2Y3, 0)))
        Pt3=sketchEpIn2Y.addGeometry(Part.Point(App.Vector(t4, Feuil.EpIn2Y4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpIn2Y, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpIn2Y, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpIn2Y, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpIn2Y, Pt3, "PtIn3")
        self.planBS(sketchEpIn2Y,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpIn3Y.addGeometry(Part.Point(App.Vector(t1, Feuil.EpIn3Y1, 0)))
        Pt1=sketchEpIn3Y.addGeometry(Part.Point(App.Vector(t2, Feuil.EpIn3Y2, 0)))
        Pt2=sketchEpIn3Y.addGeometry(Part.Point(App.Vector(t3, Feuil.EpIn3Y3, 0)))
        Pt3=sketchEpIn3Y.addGeometry(Part.Point(App.Vector(t4, Feuil.EpIn3Y4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpIn3Y, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpIn3Y, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpIn3Y, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpIn3Y, Pt3, "PtIn3")
        self.planBS(sketchEpIn3Y,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpIn4Y.addGeometry(Part.Point(App.Vector(t1, Feuil.EpIn4Y1, 0)))
        Pt1=sketchEpIn4Y.addGeometry(Part.Point(App.Vector(t2, Feuil.EpIn4Y2, 0)))
        Pt2=sketchEpIn4Y.addGeometry(Part.Point(App.Vector(t3, Feuil.EpIn4Y3, 0)))
        Pt3=sketchEpIn4Y.addGeometry(Part.Point(App.Vector(t4, Feuil.EpIn4Y4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpIn4Y, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpIn4Y, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpIn4Y, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpIn4Y, Pt3, "PtIn3")
        self.planBS(sketchEpIn4Y,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpIn5Y.addGeometry(Part.Point(App.Vector(t1, Feuil.EpIn5Y1, 0)))
        Pt1=sketchEpIn5Y.addGeometry(Part.Point(App.Vector(t2, Feuil.EpIn5Y2, 0)))
        Pt2=sketchEpIn5Y.addGeometry(Part.Point(App.Vector(t3, Feuil.EpIn5Y3, 0)))
        Pt3=sketchEpIn5Y.addGeometry(Part.Point(App.Vector(t4, Feuil.EpIn5Y4, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpIn5Y, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpIn5Y, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpIn5Y, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpIn5Y, Pt3, "PtIn3")
        self.planBS(sketchEpIn5Y,Pt0, Pt1, Pt2, Pt3)
        Pt0=sketchEpInLast.addGeometry(Part.Point(App.Vector(t1, Feuil.EpInLast1, 0)))
        Pt1=sketchEpInLast.addGeometry(Part.Point(App.Vector(t2, Feuil.EpInLast1, 0)))
        Pt2=sketchEpInLast.addGeometry(Part.Point(App.Vector(t3, Feuil.EpInLast1, 0)))
        Pt3=sketchEpInLast.addGeometry(Part.Point(App.Vector(t4, Feuil.EpInLast1, 0)))
        (Pt0x,Pt0y)=self.immobilisePoint(sketchEpInLast, Pt0, "PtIn0")
        (Pt1x,Pt1y)=self.immobilisePoint(sketchEpInLast, Pt1, "PtIn1")
        (Pt2x,Pt2y)=self.immobilisePoint(sketchEpInLast, Pt2, "PtIn2")
        (Pt3x,Pt3y)=self.immobilisePoint(sketchEpInLast, Pt3, "PtIn3")
        self.planBS(sketchEpInLast,Pt0, Pt1, Pt2, Pt3)
#
#       print("initEpaisseur - fin")
        return
    def traceEpaisseur(self,fp):
    #    
    #   Creation des lois d'épaisseur en 2D pour éventuellement transférer sur chacun des filets Cascade
    #    
#       print("traceEpaisseur")
    # #
    # #   Stokage pour sauvegarde de l'information dans Epaisseur
    # #   
        docPlanEpaisseur = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Plan_Epaisseurs")
        docPilote = App.ActiveDocument.getObject("Pilote")
    #
    #   Discretisation des pilotes des variables 
    #
    #   Extrados
        EpEx1X = App.ActiveDocument.addObject("Part::FeaturePython", "EpEx1X")
        docPilote.addObject(EpEx1X)
        Discretize.Discretization(EpEx1X, (App.ActiveDocument.getObject("skEpEx1X"),"Edge1"))
        EpEx1X.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpEx1X.ViewObject)
        EpEx1X.ViewObject.PointSize = 3
        EpEx2X = App.ActiveDocument.addObject("Part::FeaturePython", "EpEx2X")
        docPilote.addObject(EpEx2X)
        Discretize.Discretization(EpEx2X, (App.ActiveDocument.getObject("skEpEx2X"),"Edge1"))
        EpEx2X.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpEx2X.ViewObject)
        EpEx2X.ViewObject.PointSize = 3
        EpEx3X = App.ActiveDocument.addObject("Part::FeaturePython", "EpEx3X")
        docPilote.addObject(EpEx3X)
        Discretize.Discretization(EpEx3X, (App.ActiveDocument.getObject("skEpEx3X"),"Edge1"))
        EpEx3X.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpEx3X.ViewObject)
        EpEx3X.ViewObject.PointSize = 3
        EpEx4X = App.ActiveDocument.addObject("Part::FeaturePython", "EpEx4X")
        docPilote.addObject(EpEx4X)
        Discretize.Discretization(EpEx4X, (App.ActiveDocument.getObject("skEpEx4X"),"Edge1"))
        EpEx4X.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpEx4X.ViewObject)
        EpEx4X.ViewObject.PointSize = 3
        EpEx5X = App.ActiveDocument.addObject("Part::FeaturePython", "EpEx5X")
        docPilote.addObject(EpEx5X)
        Discretize.Discretization(EpEx5X, (App.ActiveDocument.getObject("skEpEx5X"),"Edge1"))
        EpEx5X.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpEx5X.ViewObject)
        EpEx5X.ViewObject.PointSize = 3
        
        EpEx1Y = App.ActiveDocument.addObject("Part::FeaturePython", "EpEx1Y")
        docPilote.addObject(EpEx1Y)
        Discretize.Discretization(EpEx1Y, (App.ActiveDocument.getObject("skEpEx1Y"),"Edge1"))
        EpEx1Y.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpEx1Y.ViewObject)
        EpEx1Y.ViewObject.PointSize = 3
        EpEx2Y = App.ActiveDocument.addObject("Part::FeaturePython", "EpEx2Y")
        docPilote.addObject(EpEx2Y)
        Discretize.Discretization(EpEx2Y, (App.ActiveDocument.getObject("skEpEx2Y"),"Edge1"))
        EpEx2Y.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpEx2Y.ViewObject)
        EpEx2Y.ViewObject.PointSize = 3
        EpEx3Y = App.ActiveDocument.addObject("Part::FeaturePython", "EpEx3Y")
        docPilote.addObject(EpEx3Y)
        Discretize.Discretization(EpEx3Y, (App.ActiveDocument.getObject("skEpEx3Y"),"Edge1"))
        EpEx3Y.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpEx3Y.ViewObject)
        EpEx3Y.ViewObject.PointSize = 3
        EpEx4Y = App.ActiveDocument.addObject("Part::FeaturePython", "EpEx4Y")
        docPilote.addObject(EpEx4Y)
        Discretize.Discretization(EpEx4Y, (App.ActiveDocument.getObject("skEpEx4Y"),"Edge1"))
        EpEx4Y.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpEx4Y.ViewObject)
        EpEx4Y.ViewObject.PointSize = 3
        EpEx5Y = App.ActiveDocument.addObject("Part::FeaturePython", "EpEx5Y")
        docPilote.addObject(EpEx5Y)
        Discretize.Discretization(EpEx5Y, (App.ActiveDocument.getObject("skEpEx5Y"),"Edge1"))
        EpEx5Y.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpEx5Y.ViewObject)
        EpEx5Y.ViewObject.PointSize = 3
        EpExLast = App.ActiveDocument.addObject("Part::FeaturePython", "EpExLast")
        docPilote.addObject(EpExLast)
        Discretize.Discretization(EpExLast, (App.ActiveDocument.getObject("skEpExLast"),"Edge1"))
        EpExLast.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpExLast.ViewObject)
        EpExLast.ViewObject.PointSize = 3
        
    #   Intrados
        EpIn1X = App.ActiveDocument.addObject("Part::FeaturePython", "EpIn1X")
        docPilote.addObject(EpIn1X)
        Discretize.Discretization(EpIn1X, (App.ActiveDocument.getObject("skEpIn1X"),"Edge1"))
        EpIn1X.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpIn1X.ViewObject)
        EpIn1X.ViewObject.PointSize = 3
        EpIn2X = App.ActiveDocument.addObject("Part::FeaturePython", "EpIn2X")
        docPilote.addObject(EpIn2X)
        Discretize.Discretization(EpIn2X, (App.ActiveDocument.getObject("skEpIn2X"),"Edge1"))
        EpIn2X.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpIn2X.ViewObject)
        EpIn2X.ViewObject.PointSize = 3
        EpIn3X = App.ActiveDocument.addObject("Part::FeaturePython", "EpIn3X")
        docPilote.addObject(EpIn3X)
        Discretize.Discretization(EpIn3X, (App.ActiveDocument.getObject("skEpIn3X"),"Edge1"))
        EpIn3X.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpIn3X.ViewObject)
        EpIn3X.ViewObject.PointSize = 3
        EpIn4X = App.ActiveDocument.addObject("Part::FeaturePython", "EpIn4X")
        docPilote.addObject(EpIn4X)
        Discretize.Discretization(EpIn4X, (App.ActiveDocument.getObject("skEpIn4X"),"Edge1"))
        EpIn4X.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpIn4X.ViewObject)
        EpIn4X.ViewObject.PointSize = 3
        EpIn5X = App.ActiveDocument.addObject("Part::FeaturePython", "EpIn5X")
        docPilote.addObject(EpIn5X)
        Discretize.Discretization(EpIn5X, (App.ActiveDocument.getObject("skEpIn5X"),"Edge1"))
        EpIn5X.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpIn5X.ViewObject)
        EpIn5X.ViewObject.PointSize = 3
        
        EpIn1Y = App.ActiveDocument.addObject("Part::FeaturePython", "EpIn1Y")
        docPilote.addObject(EpIn1Y)
        Discretize.Discretization(EpIn1Y, (App.ActiveDocument.getObject("skEpIn1Y"),"Edge1"))
        EpIn1Y.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpIn1Y.ViewObject)
        EpIn1Y.ViewObject.PointSize = 3
        EpIn2Y = App.ActiveDocument.addObject("Part::FeaturePython", "EpIn2Y")
        docPilote.addObject(EpIn2Y)
        Discretize.Discretization(EpIn2Y, (App.ActiveDocument.getObject("skEpIn2Y"),"Edge1"))
        EpIn2Y.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpIn2Y.ViewObject)
        EpIn2Y.ViewObject.PointSize = 3
        EpIn3Y = App.ActiveDocument.addObject("Part::FeaturePython", "EpIn3Y")
        docPilote.addObject(EpIn3Y)
        Discretize.Discretization(EpIn3Y, (App.ActiveDocument.getObject("skEpIn3Y"),"Edge1"))
        EpIn3Y.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpIn3Y.ViewObject)
        EpIn3Y.ViewObject.PointSize = 3
        EpIn4Y = App.ActiveDocument.addObject("Part::FeaturePython", "EpIn4Y")
        docPilote.addObject(EpIn4Y)
        Discretize.Discretization(EpIn4Y, (App.ActiveDocument.getObject("skEpIn4Y"),"Edge1"))
        EpIn4Y.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpIn4Y.ViewObject)
        EpIn4Y.ViewObject.PointSize = 3
        EpIn5Y = App.ActiveDocument.addObject("Part::FeaturePython", "EpIn5Y")
        docPilote.addObject(EpIn5Y)
        Discretize.Discretization(EpIn5Y, (App.ActiveDocument.getObject("skEpIn5Y"),"Edge1"))
        EpIn5Y.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpIn5Y.ViewObject)
        EpIn5Y.ViewObject.PointSize = 3
        EpInLast = App.ActiveDocument.addObject("Part::FeaturePython", "EpInLast")
        docPilote.addObject(EpInLast)
        Discretize.Discretization(EpInLast, (App.ActiveDocument.getObject("skEpInLast"),"Edge1"))
        EpInLast.Number=fp.Nfilets
        Discretize.ViewProviderDisc(EpInLast.ViewObject)
        EpInLast.ViewObject.PointSize = 3         
    #   création du sketch en x-y, x représentant la corde du profil et y son épaisseur pour chacun des filets
        self.sketchDiscEpaisseur(fp, EpEx1X, EpEx2X, EpEx3X, EpEx4X, EpEx5X, EpEx1Y, EpEx2Y, EpEx3Y, EpEx4Y, EpEx5Y, EpExLast, EpIn1X, EpIn2X, EpIn3X, EpIn4X, EpIn5X, EpIn1Y, EpIn2Y, EpIn3Y, EpIn4Y, EpIn5Y,       EpInLast)
        App.ActiveDocument.recompute()
#       print("traceEpaisseur - fin")
        return
    def sketchDiscEpaisseur(self,fp, EpEx1X, EpEx2X, EpEx3X, EpEx4X, EpEx5X, EpEx1Y, EpEx2Y, EpEx3Y, EpEx4Y, EpEx5Y, EpExLast, EpIn1X, EpIn2X, EpIn3X, EpIn4X, EpIn5X, EpIn1Y, EpIn2Y, EpIn3Y, EpIn4Y, EpIn5Y,       EpInLast):
#       print('sketchDiscEpaisseur')
        docPlanEpaisseur=App.ActiveDocument.getObject('Plan_Epaisseurs')
#       print('fp.preNfilets= '+str(fp.preNfilets))
        for i in range (fp.preNfilets):
    #       print("for i in range (fp.preNfilets):")
            I=str(i+1)
    #       print(I)
            App.ActiveDocument.getObject('LoiEpaisseur'+I+'e').recompute()
            App.ActiveDocument.getObject("LoiEpaisseur"+I+"es").recompute()
            App.ActiveDocument.getObject('LoiEpaisseur'+I+'i').recompute()
            App.ActiveDocument.getObject("LoiEpaisseur"+I+"is").recompute()
#       print('fp.Nfilets= '+str(fp.Nfilets))
        for i in range(fp.preNfilets,fp.Nfilets):
    #       print("for i in range(fp.preNfilets,fp.Nfilets):")
            I=str(i+1)
    #       print(I)
    #   Création du sketch extrados
            sketch_e=App.ActiveDocument.addObject('Sketcher::SketchObject','skLoiEpaisseur'+I+'e')
            if fp.preNfilets > 0 :sketch_e.Visibility=App.ActiveDocument.getObject('skLoiEpaisseur'+str(i)+'e').Visibility
            docPlanEpaisseur.addObject(sketch_e)            
            fpe = App.ActiveDocument.addObject("Part::FeaturePython",'LoiEpaisseur'+I+'e')
            fpe.Visibility=False
            docPlanEpaisseur.addObject(fpe)
    #       print(I)
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
            Pt01=sketch_e.addGeometry(Part.Point(App.Vector(EpEx1X.Points[i].y, EpEx1Y.Points[i].y, r01 )))
    #       point 2 extrados
            r02=100.
            Pt02=sketch_e.addGeometry(Part.Point(App.Vector(EpEx2X.Points[i].y, EpEx2Y.Points[i].y, r02)))
    #       point 3 extrados            
            r03=100.
            Pt03=sketch_e.addGeometry(Part.Point(App.Vector(EpEx3X.Points[i].y, EpEx3Y.Points[i].y, r03)))
    #       point 4 extrados  
            r04=100.
            Pt04=sketch_e.addGeometry(Part.Point(App.Vector(EpEx4X.Points[i].y, EpEx4Y.Points[i].y, r04)))
    #       point 5 extrados  
            r05=100.
            Pt05=sketch_e.addGeometry(Part.Point(App.Vector(EpEx5X.Points[i].y, EpEx5Y.Points[i].y, r05)))
    #       Création du BSpline extrados
    #       print('Geo sketch_e ='+str(sketch_e.Geometry))
            BSe=self.epaisseurBS(sketch_e,Pt00,Pt01,Pt02,Pt03,Pt04,Pt05)
            sketch_e.recompute()
    #       on immobilise tous les points
            (Ddl00x,Ddl00y)=self.immobilisePoint(sketch_e, Pt00, "Ep"+I+"e0") #18
            (Ddl01x,Ddl01y)=self.immobilisePoint(sketch_e, Pt01, "Ep"+I+"e1") #20
            (Ddl02x,Ddl02y)=self.immobilisePoint(sketch_e, Pt02, "Ep"+I+"e2") #22
            (Ddl03x,Ddl03y)=self.immobilisePoint(sketch_e, Pt03, "Ep"+I+"e3") #24
            (Ddl04x,Ddl04y)=self.immobilisePoint(sketch_e, Pt04, "Ep"+I+"e4") #26
            (Ddl05x,Ddl05y)=self.immobilisePoint(sketch_e, Pt05, "Ep"+I+"e5") #28
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
            eLast=EpExLast.Points[i].y
            DiscEp_s(fpes, fpe, fp.Npts, eLast)
            ViewProviderDisc(fpes.ViewObject)
            fpes.ViewObject.PointSize = 3 
            if fp.preNfilets > 0 :fpes.Visibility=App.ActiveDocument.getObject('LoiEpaisseur'+str(i)+'es').Visibility
    #       print('fpes.Points')
    #       print(fpes.Points)
    #   Création du sketch intrados
            sketch_i=App.ActiveDocument.addObject('Sketcher::SketchObject','skLoiEpaisseur'+I+'i')
            if fp.preNfilets > 0 :sketch_i.Visibility=App.ActiveDocument.getObject('skLoiEpaisseur'+str(i)+'i').Visibility
            docPlanEpaisseur.addObject(sketch_i) 
            fpi = App.ActiveDocument.addObject("Part::FeaturePython",'LoiEpaisseur'+I+'i')
            fpi.Visibility=False
            docPlanEpaisseur.addObject(fpi)
    #   Création des 5 poles du spline intrados et du poids de chacun
    #       point 0 intrados
            r10=100.
            Pt10=sketch_i.addGeometry(Part.Point(App.Vector(0., 0., r10)))
    #       point 1 intrados
            r11=100.
            Pt11=sketch_i.addGeometry(Part.Point(App.Vector(EpIn1X.Points[i].y, -EpIn1Y.Points[i].y, r11 )))
    #       point 2 intrados
            r12=100.
            Pt12=sketch_i.addGeometry(Part.Point(App.Vector(EpIn2X.Points[i].y, -EpIn2Y.Points[i].y, r12)))
    #       point 3 intrados            
            r13=100.
            Pt13=sketch_i.addGeometry(Part.Point(App.Vector(EpIn3X.Points[i].y, -EpIn3Y.Points[i].y, r13)))
    #       point 4 intrados 
            r14=100.
            Pt14=sketch_i.addGeometry(Part.Point(App.Vector(EpIn4X.Points[i].y, -EpIn4Y.Points[i].y, r14)))
    #       point 5 intrados 
            r15=100.
            Pt15=sketch_i.addGeometry(Part.Point(App.Vector(EpIn5X.Points[i].y, -EpIn5Y.Points[i].y, r15)))
    #       Création du BSpline intrados
    #       print('Geo sketch_i ='+str(sketch_i.Geometry))
            BSi=self.epaisseurBS(sketch_i,Pt10,Pt11,Pt12,Pt13,Pt14,Pt15)
            sketch_i.recompute()
    #       on immobilise tous les points
            (Ddl10x,Ddl10y)=self.immobilisePoint(sketch_i, Pt10, "Ep"+I+"i0") #18
            (Ddl11x,Ddl11y)=self.immobilisePoint(sketch_i, Pt11, "Ep"+I+"i1") #20
            (Ddl12x,Ddl12y)=self.immobilisePoint(sketch_i, Pt12, "Ep"+I+"i2") #22
            (Ddl13x,Ddl13y)=self.immobilisePoint(sketch_i, Pt13, "Ep"+I+"i3") #24
            (Ddl14x,Ddl14y)=self.immobilisePoint(sketch_i, Pt14, "Ep"+I+"i4") #26
            (Ddl15x,Ddl15y)=self.immobilisePoint(sketch_i, Pt15, "Ep"+I+"i5") #28
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
            iLast=EpInLast.Points[i].y
            DiscEp_s(fpis,fpi, fp.Npts, iLast)
            ViewProviderDisc(fpis.ViewObject)
            fpis.ViewObject.PointSize = 3 
            if fp.preNfilets > 0 :fpis.Visibility=App.ActiveDocument.getObject('LoiEpaisseur'+str(i)+'is').Visibility
    #       print('fpis.Points')
    #       print(fpis.Points)
#       print('sketchDiscEpaisseur - fin')
        return
    def modifEpaisseur(self,fp):
    #
    #   Routine pour mettre à jours les sketchs LoisEpaisseurI à partir des points discrétisés sur les sketchs des pilotes
#        print("modifEpaisseur")
        EpEx1X=App.ActiveDocument.getObject("EpEx1X")
        EpEx2X=App.ActiveDocument.getObject("EpEx2X")
        EpEx3X=App.ActiveDocument.getObject("EpEx3X")
        EpEx4X=App.ActiveDocument.getObject("EpEx4X")
        EpEx5X=App.ActiveDocument.getObject("EpEx5X")
        EpEx1Y=App.ActiveDocument.getObject("EpEx1Y")
        EpEx2Y=App.ActiveDocument.getObject("EpEx2Y")
        EpEx3Y=App.ActiveDocument.getObject("EpEx3Y")
        EpEx4Y=App.ActiveDocument.getObject("EpEx4Y")
        EpEx5Y=App.ActiveDocument.getObject("EpEx5Y")
        EpExLast=App.ActiveDocument.getObject("EpExLast")
        EpIn1X=App.ActiveDocument.getObject("EpIn1X")
        EpIn2X=App.ActiveDocument.getObject("EpIn2X")
        EpIn3X=App.ActiveDocument.getObject("EpIn3X")
        EpIn4X=App.ActiveDocument.getObject("EpIn4X")
        EpIn5X=App.ActiveDocument.getObject("EpIn5X")
        EpIn1Y=App.ActiveDocument.getObject("EpIn1Y")
        EpIn2Y=App.ActiveDocument.getObject("EpIn2Y")
        EpIn3Y=App.ActiveDocument.getObject("EpIn3Y")
        EpIn4Y=App.ActiveDocument.getObject("EpIn4Y")
        EpIn5Y=App.ActiveDocument.getObject("EpIn5Y")
        EpInLast=App.ActiveDocument.getObject("EpInLast")
        for i in range(fp.Nfilets):
    #       print("for i in range(fp.Nfilets)")
            I=str(i+1)
    #       print(I)
            sketch_e=App.ActiveDocument.getObject("skLoiEpaisseur"+I+"e")
            sketch_i=App.ActiveDocument.getObject("skLoiEpaisseur"+I+"i")
            fpes=App.ActiveDocument.getObject("LoiEpaisseur"+I+"es")
            fpis=App.ActiveDocument.getObject("LoiEpaisseur"+I+"is")
#
            sketch_e.setDatum(22,App.Units.Quantity("0.0"))
            sketch_e.setDatum(23,App.Units.Quantity("0.0"))
            sketch_e.setDatum(24,App.Units.Quantity(str(EpEx1X.Points[i].y)))
            sketch_e.setDatum(25,App.Units.Quantity(str(EpEx1Y.Points[i].y))) 
            sketch_e.setDatum(26,App.Units.Quantity(str(EpEx2X.Points[i].y)))
            sketch_e.setDatum(27,App.Units.Quantity(str(EpEx2Y.Points[i].y)))
            sketch_e.setDatum(28,App.Units.Quantity(str(EpEx3X.Points[i].y)))
            sketch_e.setDatum(29,App.Units.Quantity(str(EpEx3Y.Points[i].y)))
            sketch_e.setDatum(30,App.Units.Quantity(str(EpEx4X.Points[i].y)))
            sketch_e.setDatum(31,App.Units.Quantity(str(EpEx4Y.Points[i].y)))
            sketch_e.setDatum(32,App.Units.Quantity(str(EpEx5X.Points[i].y)))
            sketch_e.setDatum(33,App.Units.Quantity(str(EpEx5Y.Points[i].y)))
#
            sketch_i.setDatum(22,App.Units.Quantity("0.0"))
            sketch_i.setDatum(23,App.Units.Quantity("0.0"))
            sketch_i.setDatum(24,App.Units.Quantity(str(EpIn1X.Points[i].y)))
            sketch_i.setDatum(25,App.Units.Quantity(str(-EpIn1Y.Points[i].y)))
            sketch_i.setDatum(26,App.Units.Quantity(str(EpIn2X.Points[i].y)))
            sketch_i.setDatum(27,App.Units.Quantity(str(-EpIn2Y.Points[i].y)))
            sketch_i.setDatum(28,App.Units.Quantity(str(EpIn3X.Points[i].y)))
            sketch_i.setDatum(29,App.Units.Quantity(str(-EpIn3Y.Points[i].y)))
            sketch_i.setDatum(30,App.Units.Quantity(str(EpIn4X.Points[i].y)))
            sketch_i.setDatum(31,App.Units.Quantity(str(-EpIn4Y.Points[i].y)))
            sketch_i.setDatum(32,App.Units.Quantity(str(EpIn5X.Points[i].y)))
            sketch_i.setDatum(33,App.Units.Quantity(str(-EpIn5Y.Points[i].y)))
            fpes.Last=EpExLast.Points[i].y
            fpis.Last=EpInLast.Points[i].y
            fpes.recompute()
            fpis.recompute()
#       Boucle de vérification pour Warnings        
        for i in range(fp.Nfilets):
            I=str(i+1)
            # Cascade
            fpe=App.ActiveDocument.getObject("LoiEpaisseur"+I+"e")
            fpi=App.ActiveDocument.getObject("LoiEpaisseur"+I+"i")
            x=[]
            for point in fpe.Points: x.append(point.x)
            if (not np.all(np.diff(x) > 0)): App.Console.PrintWarning("*** x is not monotonically increasing (Loiepaisseur" +I +"e) *** \n")
            x=[]
            for point in fpi.Points: x.append(point.x)
            if (not np.all(np.diff(x) > 0)): App.Console.PrintWarning("*** x is not monotonically increasing (Loiepaisseur" +I +"i) *** \n")
#        print("modifEpaisseur - fin")
        return

    def epaisseurBS(self,sketch,Pt0,Pt1,Pt2,Pt3,Pt4,Pt5):
    #
    #   Création d'une BSpline de degré 3 dans le plan Epaisseur
    #   Chaque point est défini par sa géométrie dans le sketch à l'indice Vx
    #
    #   Coordonnées des extrémités
#       print("epaisseurBS")
        Geo=sketch.Geometry
        v0=App.Vector(Geo[Pt0].X,Geo[Pt0].Y,0)
        v1=App.Vector(Geo[Pt1].X,Geo[Pt1].Y,0)
        v2=App.Vector(Geo[Pt2].X,Geo[Pt2].Y,0)
        v3=App.Vector(Geo[Pt3].X,Geo[Pt3].Y,0)
        v4=App.Vector(Geo[Pt4].X,Geo[Pt4].Y,0)
        v5=App.Vector(Geo[Pt5].X,Geo[Pt5].Y,0)
        r0=100.
        r1=100.
        r2=100.
        r3=100.
        r4=100.
        r5=100.
#       print('v0= '+str(v0))
#       print('v1= '+str(v1))
#       print('v2= '+str(v2))
#       print('v3= '+str(v3))
#       print('v4= '+str(v4))
#       print('v5= '+str(v4))
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
        C5=sketch.addGeometry(Part.Circle(v5,App.Vector(0,0,1),r5),True)
        sketch.addConstraint(Sketcher.Constraint('Coincident',C5,3,Pt5,1))
        sketch.addConstraint(Sketcher.Constraint('Radius',C5,r5))
    #
        BS=sketch.addGeometry(Part.BSplineCurve([v0,v1,v2,v3,v4,v5],None,None,False,3,None,False),False)
       
    #
        conList1 = []
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C0,4,BS,0))
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C1,4,BS,1))
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C2,4,BS,2))
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C3,4,BS,3))
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C4,4,BS,4))
        conList1.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',C5,4,BS,5))
        sketch.addConstraint(conList1)
        sketch.exposeInternalGeometry(BS)
    #    
#       print("epaisseurBS - fin")
        
        return (BS)
#
#
#       Plan de la cascade
#
#
    def initCascade(self,fp):
#       print("initCascade") 
    #
    #   Routine pour créer les splines à 4 pôles(0,1,2,3) qui pilotent pour l'âme
    #   les variables évolutant selon la coordonnée normalisée t de la ceinture au plafond :
    #  
    #   sketchTheta : position angulaire à l'entrée et à la sortie
    #   sketchAlpha : angle d'incidence à l'entrée et à la sortie
    #   sketchPoids : poids (rayon) d'influence des pôles à l'entrée et à la sortie
    #   sketchLong  : longueur entre les pôles d'entrée et de sortie ( coord. norm. s)

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
        t0=Feuil.B1
        t1=Feuil.C1
        t2=Feuil.D1
        t3=Feuil.E1
    #   Alpha (angle incident) contient les lois selon t qui définissent les pôles de la cascade indépendamment du nombbre de filet.
    #   Il y a 4 Bspline du bord d'attaque au bord de fuite selon s eux-mêmes définis chacun par 4 poles. Donc 16 poles.
    #   Ces splines sont définis dans l'espace (t,Alpha) par les deux points d'extrémité entrée et sortie. 
    #   Pour la ceinture (t=0) et le plafond (t=100) on a 2 vecteurs  (alpha1, w1, L1) et (alpha2, w2, L2)  
    #   1 indice pour entree
    #   2 indice pour sortie
        nseg=fp.Npts-1
    #
    #
    #   Construction des sketchs et des bsplines entrée et sortie pour tous les pilotes.
    #
    #
    #   Loi de theta 
    #
    #   au bord d'attaque (t,theta,0)
        Te0=sketchTheta_entree.addGeometry(Part.Point(App.Vector(t0,Feuil.ThE1,0)))
        Te1=sketchTheta_entree.addGeometry(Part.Point(App.Vector(t1,Feuil.ThE2,0)))
        Te2=sketchTheta_entree.addGeometry(Part.Point(App.Vector(t2,Feuil.ThE3,0)))
        Te3=sketchTheta_entree.addGeometry(Part.Point(App.Vector(t3,Feuil.ThE4,0)))
        (Te0x,Te0y)=self.immobilisePoint(sketchTheta_entree, Te0, "Te0")
        (Te1x,Te1y)=self.immobilisePoint(sketchTheta_entree, Te1, "Te1")
        (Te2x,Te2y)=self.immobilisePoint(sketchTheta_entree, Te2, "Te2")
        (Te3x,Te3y)=self.immobilisePoint(sketchTheta_entree, Te3, "Te3")
    #   au bord de fuite
        Ts0=sketchTheta_sortie.addGeometry(Part.Point(App.Vector(t0,Feuil.ThS1,0)))
        Ts1=sketchTheta_sortie.addGeometry(Part.Point(App.Vector(t1,Feuil.ThS2,0)))
        Ts2=sketchTheta_sortie.addGeometry(Part.Point(App.Vector(t2,Feuil.ThS3,0)))
        Ts3=sketchTheta_sortie.addGeometry(Part.Point(App.Vector(t3,Feuil.ThS4,0)))
        (Ts0x,Ts0y)=self.immobilisePoint(sketchTheta_sortie, Ts0, "Ts0")
        (Ts1x,Ts1y)=self.immobilisePoint(sketchTheta_sortie, Ts1, "Ts1")
        (Ts2x,Ts2y)=self.immobilisePoint(sketchTheta_sortie, Ts2, "Ts2")
        (Ts3x,Ts3y)=self.immobilisePoint(sketchTheta_sortie, Ts3, "Ts3")
    #   Construction des Bspline
        (BSte,ceinte,plfte)=self.planBS(sketchTheta_entree,Te0,Te1,Te2,Te3)   # BORD D'ATTAQUE
        (BSts,ceints,plfts)=self.planBS(sketchTheta_sortie,Ts0,Ts1,Ts2,Ts3)   # BORD DE FUITE                                  
    #
    #   Loi d'alpha 
    #
    #   au bord d'attaque
        Ae0=sketchAlpha_entree.addGeometry(Part.Point(App.Vector(t0,Feuil.AlE1,0)))
        Ae1=sketchAlpha_entree.addGeometry(Part.Point(App.Vector(t1,Feuil.AlE2,0)))
        Ae2=sketchAlpha_entree.addGeometry(Part.Point(App.Vector(t2,Feuil.AlE3,0)))
        Ae3=sketchAlpha_entree.addGeometry(Part.Point(App.Vector(t3,Feuil.AlE4,0)))
        (Ae0x,Ae0y)=self.immobilisePoint(sketchAlpha_entree, Ae0, "Ae0")
        (Ae1x,Ae1y)=self.immobilisePoint(sketchAlpha_entree, Ae1, "Ae1")
        (Ae2x,Ae2y)=self.immobilisePoint(sketchAlpha_entree, Ae2, "Ae2")
        (Ae3x,Ae3y)=self.immobilisePoint(sketchAlpha_entree, Ae3, "Ae3")
    #   au bord de fuite
        As0=sketchAlpha_sortie.addGeometry(Part.Point(App.Vector(t0,Feuil.AlS1,0)))
        As1=sketchAlpha_sortie.addGeometry(Part.Point(App.Vector(t1,Feuil.AlS2,0)))
        As2=sketchAlpha_sortie.addGeometry(Part.Point(App.Vector(t2,Feuil.AlS3,0)))
        As3=sketchAlpha_sortie.addGeometry(Part.Point(App.Vector(t3,Feuil.AlS4,0)))
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
        We0=sketchPoids_entree.addGeometry(Part.Point(App.Vector(t0,Feuil.PoE1,0)))
        We1=sketchPoids_entree.addGeometry(Part.Point(App.Vector(t1,Feuil.PoE2,0)))
        We2=sketchPoids_entree.addGeometry(Part.Point(App.Vector(t2,Feuil.PoE3,0)))
        We3=sketchPoids_entree.addGeometry(Part.Point(App.Vector(t3,Feuil.PoE4,0)))
        (We0x,We0y)=self.immobilisePoint(sketchPoids_entree, We0, "We0")
        (We1x,We1y)=self.immobilisePoint(sketchPoids_entree, We1, "We1")
        (We2x,We2y)=self.immobilisePoint(sketchPoids_entree, We2, "We2")
        (We3x,We3y)=self.immobilisePoint(sketchPoids_entree, We3, "We3")
    #   au bord de fuite 
        Ws0=sketchPoids_sortie.addGeometry(Part.Point(App.Vector(t0,Feuil.PoS1,0)))
        Ws1=sketchPoids_sortie.addGeometry(Part.Point(App.Vector(t1,Feuil.PoS2,0)))
        Ws2=sketchPoids_sortie.addGeometry(Part.Point(App.Vector(t2,Feuil.PoS3,0)))
        Ws3=sketchPoids_sortie.addGeometry(Part.Point(App.Vector(t3,Feuil.PoS4,0)))
        (Ws0x,Ws0y)=self.immobilisePoint(sketchPoids_sortie, Ws0, "Ws0")
        (Ws1x,Ws1y)=self.immobilisePoint(sketchPoids_sortie, Ws1, "Ws1")
        (Ws2x,Ws2y)=self.immobilisePoint(sketchPoids_sortie, Ws2, "Ws2")
        (Ws3x,Ws3y)=self.immobilisePoint(sketchPoids_sortie, Ws3, "Ws3")
    #   Construction des Bspline
        (BSWe,ceinwe,plfwe)=self.planBS(sketchPoids_entree,We0,We1,We2,We3)   # BORD D'ATTAQUE
        (BSWs,ceinws,plfws)=self.planBS(sketchPoids_sortie,Ws0,Ws1,Ws2,Ws3)   # BORD DE FUITE       
        App.ActiveDocument.recompute()
    #
    #   Loi des Longueurs 
    #
    #   au bord d'attaque
        Le0=sketchLong_entree.addGeometry(Part.Point(App.Vector(t0,Feuil.LoE1,0)))
        Le1=sketchLong_entree.addGeometry(Part.Point(App.Vector(t1,Feuil.LoE2,0)))
        Le2=sketchLong_entree.addGeometry(Part.Point(App.Vector(t2,Feuil.LoE3,0)))
        Le3=sketchLong_entree.addGeometry(Part.Point(App.Vector(t3,Feuil.LoE4,0)))
        (Le0x,Le0y)=self.immobilisePoint(sketchLong_entree, Le0, "Le0")
        (Le1x,Le1y)=self.immobilisePoint(sketchLong_entree, Le1, "Le1")
        (Le2x,Le2y)=self.immobilisePoint(sketchLong_entree, Le2, "Le2")
        (Le3x,Le3y)=self.immobilisePoint(sketchLong_entree, Le3, "Le3")
    #   au bord de fuite 
        Ls0=sketchLong_sortie.addGeometry(Part.Point(App.Vector(t0,Feuil.LoS1,0)))
        Ls1=sketchLong_sortie.addGeometry(Part.Point(App.Vector(t1,Feuil.LoS2,0)))
        Ls2=sketchLong_sortie.addGeometry(Part.Point(App.Vector(t2,Feuil.LoS3,0)))
        Ls3=sketchLong_sortie.addGeometry(Part.Point(App.Vector(t3,Feuil.LoS4,0)))
        (Ls0x,Ls0y)=self.immobilisePoint(sketchLong_sortie, Ls0, "Ls0")
        (Ls1x,Ls1y)=self.immobilisePoint(sketchLong_sortie, Ls1, "Ls1")
        (Ls2x,Ls2y)=self.immobilisePoint(sketchLong_sortie, Ls2, "Ls2")
        (Ls3x,Ls3y)=self.immobilisePoint(sketchLong_sortie, Ls3, "Ls3")
    #   Construction des Bspline
        (BSLe,ceinle,plfle)=self.planBS(sketchLong_entree,Le0,Le1,Le2,Le3)   # BORD D'ATTAQUE
        (BSLs,ceinls,plfls)=self.planBS(sketchLong_sortie,Ls0,Ls1,Ls2,Ls3)   # BORD DE FUITE       
        App.ActiveDocument.recompute()
#       print('initCascade - fin')
        return
    def traceCascade(self,fp):
#       print('traceCascade')
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
#       print('traceCascade - fin')
        return
    def sketchDiscCascade(self,fp, Te, Ts, Ae, As, We, Ws, Le, Ls):
#       print("sketchDiscCascade")
        docPlanCascade = App.ActiveDocument.getObject("Plan_Cascade")
        docPlanLongueurs = App.ActiveDocument.getObject("Plan_Longueurs")
    #
    #       Creation de la géométrie incluant un sketch pour chaque filet de Cascade
    #
#       print('fp.preNfilets= '+str(fp.preNfilets))
#        self.modifCascade(fp)
#       print('fp.Nfilets= '+str(fp.Nfilets))
        for i in range(fp.preNfilets,fp.Nfilets):   #FiletMeridien in FiletsMeridien:   
            I=str(i+1)
    #       print("for i in range(fp.preNfilets,fp.Nfilets)",I)
        #
        #   Création fp fpAa qui contient l'information du Discretized_Edge du voile 2D
        #
            fpAa = App.ActiveDocument.addObject("Part::FeaturePython","FiletCAa"+I)
            docPlanCascade.addObject(fpAa)
        #   Calcul de Usmax pour chaque filet qui dépend de Npts    
            Usmax=self.CascadeUsmax(i)
    #       print('Usmax= '+str(Usmax))
        # Les informations pour les points du BSpline pour Cascade
            fpAa.addProperty("App::PropertyVector","a0","Contraintes","Position(u,v)").a0=App.Vector(0,fp.SensCascade*1000.*math.radians(Te.Points[i].z),0)
            fpAa.addProperty("App::PropertyVector","a1","Contraintes","Position(alpha,poids,long)").a1=App.Vector(fp.SensCascade*Ae.Points[i].z, We.Points[i].z, Le.Points[i].z)
            fpAa.addProperty("App::PropertyVector","a2","Contraintes","Position(alpha,poids,long)").a2=App.Vector(fp.SensCascade*As.Points[i].z, Ws.Points[i].z, Ls.Points[i].z)
            fpAa.addProperty("App::PropertyVector","a3","Contraintes","Position(u,v)").a3=App.Vector(Usmax,fp.SensCascade*1000.*math.radians(Ts.Points[i].z),0)
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
            DiscCle_s(fpLe, fpAs, fp.Npts, fp.SensCascade, i)
            ViewProviderDisc(fpLe.ViewObject)
            fpLe.ViewObject.PointSize = 3
            if fp.preNfilets > 0 :fpLe.Visibility=App.ActiveDocument.getObject('FiletCLe'+str(i)).Visibility
                #       intrados
            fpLi = App.ActiveDocument.addObject("Part::FeaturePython",'FiletCLi'+I)
            docPlanLongueurs.addObject(fpLi)
            DiscCli_s(fpLi, fpAs, fp.Npts, fp.SensCascade, i)
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
        App.ActiveDocument.recompute()
#       print("sketchDiscCascade - fin")
        return   
    def modifCascade(self,fp):
#        print('modifCascade')
        Theta_entree = App.ActiveDocument.getObject("Theta_entree")
        Theta_sortie = App.ActiveDocument.getObject("Theta_sortie")
        Alpha_entree = App.ActiveDocument.getObject("Alpha_entree")
        Alpha_sortie = App.ActiveDocument.getObject("Alpha_sortie")
        Poids_entree = App.ActiveDocument.getObject("Poids_entree")
        Poids_sortie = App.ActiveDocument.getObject("Poids_sortie")
        Long_entree = App.ActiveDocument.getObject("Long_entree")
        Long_sortie = App.ActiveDocument.getObject("Long_sortie")
        for i in range(fp.Nfilets):     #FiletMeridien in FiletsMeridien:
            I=str(i+1)
    #       print("for i in range(fp.Nfilets): I=",I)
            FiletMeridien=App.ActiveDocument.getObject('FiletM'+I)
    #       print(FiletMeridien.Name)
            #   Calcul de Usmax pour chaque filet qui dépend de Npts    
            Usmax=self.CascadeUsmax(i)
            #   m-à-j des données de "FiletCAa"+I
            fpAa = App.ActiveDocument.getObject("FiletCAa"+I)
            fpAa.a0=App.Vector(0,fp.Sens*1000.*math.radians(Theta_entree.Points[i].z),0)
    #       print('fpAs.a..      *******')
    #       print(Theta_entree.Points)
    #       print(fpAa.a0)
            fpAa.a1=App.Vector(fp.SensCascade*Alpha_entree.Points[i].z, Poids_entree.Points[i].z, Long_entree.Points[i].z)
    #       print(fpAa.a1)
            fpAa.a2=App.Vector(fp.SensCascade*Alpha_sortie.Points[i].z, Poids_sortie.Points[i].z, Long_sortie.Points[i].z)
    #       print(fpAa.a2)
            fpAa.a3=App.Vector(Usmax,fp.Sens*1000.*math.radians(Theta_sortie.Points[i].z),0)
    #       print(fpAa.a3)
            fpAa.recompute()
        #   sketchA pour contenir la cascade 
            sketchA=App.ActiveDocument.getObject('Cascade'+I)
    #       print(sketchA.Name)
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
            fpLe.SensCascade=fp.SensCascade
            fpLe.recompute()
                #       intrados
            fpLi = App.ActiveDocument.getObject('FiletCLi'+I)
            fpLi.SensCascade=fp.SensCascade
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
#    #       print('fpAs.Shape.Compounds[0].Vertexes[k]')
#            for k in range(fpAs.Npts): debug(fpAs.Shape.Compounds[0].Vertexes[k].Point)
#       print('***recompute')
#        App.ActiveDocument.recompute()
#       Boucle de vérification pour Warnings        
        for i in range(fp.Nfilets):
            I=str(i+1)
            # Cascade
            fpAa = App.ActiveDocument.getObject("FiletCAa"+I)
            u_q=[]
            for point in fpAa.Points: u_q.append(point.y)
            if (not np.all(np.diff(u_q) > 0)): App.Console.PrintWarning("*** u is not monotonically increasing (Cascade" +I +") *** \n")
#        print('modifCascade- fin')
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
#       print('CascadeUsMax')
    #
    #   Calcul des coordonnées (m,n)à partir de (u,v) de la discretisation
    # 
    #
        I=str(i+1)
        FiletMeridien=App.ActiveDocument.getObject('FiletM'+I)
        nseg=FiletMeridien.Number-1
        pj=FiletMeridien.Points[0]
#       print("FiletMeridien.Points= "+str(FiletMeridien.Points))
    #   l'indice _s correspond à la coordonnée curviligne dans le plan méridien
        m_n=App.ActiveDocument.getObject("IsoCurve").Shape.Edges[i].Length
#       print("m_n= "+str(m_n))
        dm=m_n/nseg
        u=0
        for pj in FiletMeridien.Points[1:]:
            u+=1000.*dm/pj.x
#       print('CascadeUsMax - fin')
        return (u)
    def CascadeSketch(self,fpAa,I):
#       print('CascadeSketch')
        sketchA=App.ActiveDocument.addObject('Sketcher::SketchObject','Cascade'+I)
#       print('Cascade '+I)
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
#       print('CascadeSketch - fin')
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
        # FiletM.... ou FiletC.... contiennent les Discretize_Edge de chaque plan virtuel
        # Points3D... contiennent les séries de points du domaine 3D
        # Filet3D... contiennent les courbes interpolées sur les Points3D
        #
#       print('voile3D')
    #   Création des groupes pour classement
    #   Domaine3D
        docDomaine3D = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Domaine3D")
    #   a pour âme
    #   e pour extrados
    #   i pour intrados
    #   on crée les groupes
        docPoints3Da = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Points3Da")
        docDomaine3D.addObject(docPoints3Da)
        docPoints3De = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Points3De")
        docDomaine3D.addObject(docPoints3De)
        docPoints3Di = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Points3Di")
        docDomaine3D.addObject(docPoints3Di)
        docPoints3Die = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Points3Die")
        docDomaine3D.addObject(docPoints3Die)
        docFilet3Da = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Filet3Da")
        docDomaine3D.addObject(docFilet3Da)
        docFilet3De = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Filet3De")
        docDomaine3D.addObject(docFilet3De)
        docFilet3Di = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Filet3Di")
        docDomaine3D.addObject(docFilet3Di)
        docFilet3Die = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Filet3Die")
        docDomaine3D.addObject(docFilet3Die)
        #   Calcul des points pour générer les surfaces en 3D
        self.calculVoile(fp)
        self.calculSurf(fp)
#        self.calculVolume(fp)
#       print('voile3D - fin '+str(App.ActiveDocument.Objects.__len__()))
        return
    def calculVoile(self, fp):
#        print('calculVoile')
        docPoints3Da=App.ActiveDocument.getObject("Points3Da")
        docPoints3De=App.ActiveDocument.getObject("Points3De")
        docPoints3Di=App.ActiveDocument.getObject("Points3Di")
        docPoints3Die=App.ActiveDocument.getObject("Points3Die")
        docFilet3Da=App.ActiveDocument.getObject("Filet3Da")
        docFilet3De=App.ActiveDocument.getObject("Filet3De")
        docFilet3Di=App.ActiveDocument.getObject("Filet3Di")
        docFilet3Die=App.ActiveDocument.getObject("Filet3Die")
        docDomaine3D=App.ActiveDocument.getObject("Domaine3D")
        for i in range(fp.preNfilets,fp.Nfilets):   #FiletMeridien in FiletsMeridien:   
    #       Creation des séries de points et courbes 3D du voile
            I=str(i+1)
            fpVA = App.ActiveDocument.addObject("Part::FeaturePython",'Points3Da'+I)
            docPoints3Da.addObject(fpVA)
            fpFA=App.ActiveDocument.addObject("Part::FeaturePython","Filet3Da"+I)
            docFilet3Da.addObject(fpFA)
            fpVE = App.ActiveDocument.addObject("Part::FeaturePython",'Points3De'+I)
            docPoints3De.addObject(fpVE)
            fpFE=App.ActiveDocument.addObject("Part::FeaturePython","Filet3De"+I)
            docFilet3De.addObject(fpFE)
            fpVI = App.ActiveDocument.addObject("Part::FeaturePython",'Points3Di'+I)
            docPoints3Di.addObject(fpVI)
            fpFI=App.ActiveDocument.addObject("Part::FeaturePython","Filet3Di"+I)
            docFilet3Di.addObject(fpFI)
            fpVIE = App.ActiveDocument.addObject("Part::FeaturePython",'Points3Die'+I)
            docPoints3Die.addObject(fpVIE)
            fpFIE=App.ActiveDocument.addObject("Part::FeaturePython","Filet3Die"+I)
            docFilet3Die.addObject(fpFIE)
        #   préparation pour calculs
            fpM=App.ActiveDocument.getObject('FiletM'+I)
            fpCA=App.ActiveDocument.getObject('FiletCAs'+I)
            fpCE=App.ActiveDocument.getObject('FiletCAe'+I)
            fpCI=App.ActiveDocument.getObject('FiletCAi'+I)
        #   Voile A    
            DiscPoints3D(fpVA, fpM, fpCA, fp)
            ViewProviderDisc(fpVA.ViewObject)
            fpVA.ViewObject.PointSize = 3
            interpolate.Interpolate(fpFA,fpVA)
            interpolate.ViewProviderInterpolate(fpFA.ViewObject)
        #   Voile E    
            DiscPoints3D(fpVE, fpM, fpCE, fp)
            ViewProviderDisc(fpVE.ViewObject)
            fpVE.ViewObject.PointSize = 3
            interpolate.Interpolate(fpFE,fpVE)
            interpolate.ViewProviderInterpolate(fpFE.ViewObject)            
        #   Voile I    
            DiscPoints3D(fpVI, fpM, fpCI, fp)
            ViewProviderDisc(fpVI.ViewObject)
            fpVI.ViewObject.PointSize = 3
            interpolate.Interpolate(fpFI,fpVI)
            interpolate.ViewProviderInterpolate(fpFI.ViewObject)              
        #   Voile IE    
            DiscPoints3Die(fpVIE, fpM, fpCI, fpCE, fp)
            ViewProviderDisc(fpVIE.ViewObject)
            fpVIE.ViewObject.PointSize = 3
            interpolate.Interpolate(fpFIE,fpVIE)
            interpolate.ViewProviderInterpolate(fpFIE.ViewObject) 
            App.ActiveDocument.recompute()
            self.tanTransfer(fp, fpFIE, fpFI, fpFE)
#        print('calculVoile - fin')
        return
    def tanTransfer(self,fp,fpFIE,fpFI,fpFE):
        tanE=[]
        tanI=[]
        tanIE=fpFIE.Tangents
        for i in range(fp.Npts):
            j=fp.Npts-1-i
            x=-tanIE[j].x
            y=-tanIE[j].y
            z=-tanIE[j].z
            tanE.append(tanIE[i-1+fp.Npts])
            tanI.append(App.Vector(x,y,z))
        fpFI.Tangents=tanI
        fpFE.Tangents=tanE
        fpFI.CustomTangents=True
        fpFE.CustomTangents=True
        fpFI.recompute()
        fpFE.recompute()
        return
    def modifVoile(self, fp):
        #
        # Association des deux plans pour obtenir la géométrie en 3D
        #
        # Filets.... contient les Discretize_Edge de chaque plan
        #
#        print('modifVoile')
    #   Récupération des groupes pour classement
    #   Domaine3D
        docDomaine3D = App.ActiveDocument.getObject("Domaine3D")
        docPoints3Da = App.ActiveDocument.getObject("Points3Da")
        docPoints3De = App.ActiveDocument.getObject("Points3De")
        docPoints3Di = App.ActiveDocument.getObject("Points3Di")
        docPoints3Die = App.ActiveDocument.getObject("Points3Die")
        docFilet3Da = App.ActiveDocument.getObject("Filet3Da")
        docFilet3De = App.ActiveDocument.getObject("Filet3De")
        docFilet3Di = App.ActiveDocument.getObject("Filet3Di")
        docFilet3Die = App.ActiveDocument.getObject("Filet3Die")
        App.ActiveDocument.SurfA.NSections=[]
        App.ActiveDocument.SurfA.purgeTouched()
        App.ActiveDocument.SurfE.NSections=[]
        App.ActiveDocument.SurfE.purgeTouched()
        App.ActiveDocument.SurfI.NSections=[]
        App.ActiveDocument.SurfI.purgeTouched()
        App.ActiveDocument.SurfIE.NSections=[]
        App.ActiveDocument.SurfIE.purgeTouched()
        visi=App.ActiveDocument.getObject("Filet3Da1").Visibility
    #   Creation et initialisation des séries de points 3D du voile
#        print(fp.Nfilets, fp.preNfilets)
        for i in  range(fp.Nfilets):
#            print('Mise-à-jour des points des voiles existants')
            I=str(i+1)
#            print(I)
            if(int(I) > fp.preNfilets):
#                print("if(int(I) > fp.preNfilets)", I, fp.preNfilets)
                fpVA = App.ActiveDocument.addObject("Part::FeaturePython","Points3Da"+I)
                docPoints3Da.addObject(fpVA)
                fpVE = App.ActiveDocument.addObject("Part::FeaturePython","Points3De"+I)
                docPoints3De.addObject(fpVE)
                fpVI = App.ActiveDocument.addObject("Part::FeaturePython","Points3Di"+I)
                docPoints3Di.addObject(fpVI)
                fpVIE = App.ActiveDocument.addObject("Part::FeaturePython","Points3Die"+I)
                docPoints3Die.addObject(fpVIE)
            #   préparation pour calculs
                fpM=App.ActiveDocument.getObject('FiletM'+I)
                fpCA=App.ActiveDocument.getObject('FiletCAs'+I)
                fpCE=App.ActiveDocument.getObject('FiletCAe'+I)
                fpCI=App.ActiveDocument.getObject('FiletCAi'+I)
            #   Voile A    
                DiscPoints3D(fpVA, fpM, fpCA, fp)
                ViewProviderDisc(fpVA.ViewObject)
                fpVA.ViewObject.PointSize = 3
            #   Voile E    
                DiscPoints3D(fpVE, fpM, fpCE, fp)
                ViewProviderDisc(fpVE.ViewObject)
                fpVE.ViewObject.PointSize = 3          
            #   Voile I    
                DiscPoints3D(fpVI, fpM, fpCI, fp)
                ViewProviderDisc(fpVI.ViewObject)
                fpVI.ViewObject.PointSize = 3            
            #   Voile IE    
                DiscPoints3Die(fpVIE, fpM, fpCI, fpCE, fp)
                ViewProviderDisc(fpVIE.ViewObject)
                fpVIE.ViewObject.PointSize = 3
                App.ActiveDocument.recompute()
#            print("else")
            fpVA = App.ActiveDocument.getObject('Points3Da'+I)
            fpVE = App.ActiveDocument.getObject('Points3De'+I)
            fpVI = App.ActiveDocument.getObject('Points3Di'+I)
            fpVIE = App.ActiveDocument.getObject('Points3Die'+I)
            fpFE = App.ActiveDocument.getObject('Filet3De'+I)
            fpFI = App.ActiveDocument.getObject('Filet3Di'+I)
            fpFIE = App.ActiveDocument.getObject('Filet3Die'+I)
            if(i<fp.preNfilets):
                App.ActiveDocument.removeObject("Filet3Da"+I)
                App.ActiveDocument.removeObject("Filet3De"+I)
                App.ActiveDocument.removeObject("Filet3Di"+I)
                App.ActiveDocument.removeObject("Filet3Die"+I)
            fpFA=App.ActiveDocument.addObject("Part::FeaturePython","Filet3Da"+I)
            docFilet3Da.addObject(fpFA)
            fpFE=App.ActiveDocument.addObject("Part::FeaturePython","Filet3De"+I)
            docFilet3De.addObject(fpFE)
            fpFI=App.ActiveDocument.addObject("Part::FeaturePython","Filet3Di"+I)
            docFilet3Di.addObject(fpFI)
            fpFIE=App.ActiveDocument.addObject("Part::FeaturePython","Filet3Die"+I)
            docFilet3Die.addObject(fpFIE)
            fpVA.Visibility=visi
            fpVE.Visibility=visi
            fpVI.Visibility=visi
            fpVIE.Visibility=visi
            fpFA.Visibility=visi
            fpFE.Visibility=visi
            fpFI.Visibility=visi
            fpFIE.Visibility=visi
            fpVA.Number=fp.Npts
#            fpVA.recompute()
            interpolate.Interpolate(fpFA,fpVA)
            interpolate.ViewProviderInterpolate(fpFA.ViewObject)
            fpVE.Number=fp.Npts
#            fpVE.recompute()
            interpolate.Interpolate(fpFE,fpVE)
            interpolate.ViewProviderInterpolate(fpFE.ViewObject)
            fpVI.Number=fp.Npts
#            fpVI.recompute()
            interpolate.Interpolate(fpFI,fpVI)
            interpolate.ViewProviderInterpolate(fpFI.ViewObject)
            fpVIE.Number=2*fp.Npts - 1
#            fpVIE.recompute()
            interpolate.Interpolate(fpFIE,fpVIE)
            interpolate.ViewProviderInterpolate(fpFIE.ViewObject)
#            print("avant recalcul")
            App.ActiveDocument.recompute()
            self.tanTransfer(fp, fpFIE, fpFI, fpFE)
        self.modifSurf(fp)
#        print('modifVoile - fin '+str(App.ActiveDocument.Objects.__len__()))
        return
    def calculSurf(self,fp):
        #
        # Calcul des surfaces à partir des filets
        #
        docFilet3Da=App.ActiveDocument.getObject("Filet3Da")
        docFilet3De=App.ActiveDocument.getObject("Filet3De")
        docFilet3Di=App.ActiveDocument.getObject("Filet3Di")
        docFilet3Die=App.ActiveDocument.getObject("Filet3Die")
        docDomaine3D=App.ActiveDocument.getObject("Domaine3D")
        NSectionsA=[]
        NSectionsE=[]
        NSectionsI=[]
        NSectionsIE=[]
        for i in range(fp.Nfilets):
            I=str(i+1)
            NSectionsA.append((App.ActiveDocument.getObject("Filet3Da"+I),"Edge1"))
            NSectionsE.append((App.ActiveDocument.getObject("Filet3De"+I),"Edge1"))
            NSectionsI.append((App.ActiveDocument.getObject("Filet3Di"+I),"Edge1"))
            NSectionsIE.append((App.ActiveDocument.getObject("Filet3Die"+I),"Edge1"))
        SurfA = App.ActiveDocument.addObject("Surface::Sections", "SurfA")
#        Gui.ActiveDocument.SurfA.Deviation=0.01
        docDomaine3D.addObject(SurfA) 
        SurfA.NSections=NSectionsA 
        SurfE = App.ActiveDocument.addObject("Surface::Sections", "SurfE")
#        Gui.ActiveDocument.SurfE.Deviation=0.01
        docDomaine3D.addObject(SurfE) 
        SurfE.NSections=NSectionsE 
        SurfI = App.ActiveDocument.addObject("Surface::Sections", "SurfI")
#        Gui.ActiveDocument.SurfI.Deviation=0.01
        docDomaine3D.addObject(SurfI) 
        SurfI.NSections=NSectionsI 
        SurfIE = App.ActiveDocument.addObject("Surface::Sections", "SurfIE")
#        Gui.ActiveDocument.SurfIE.Deviation=0.01
        docDomaine3D.addObject(SurfIE) 
        SurfIE.NSections=NSectionsIE 
#        SurfIext=App.ActiveDocument.addObject("Surface::Extend", "SurfIext")
#        SurfIext.Face = [SurfI, "Face1"]
#        SurfIext.ExtendUPos=0.01
#        docDomaine3D.addObject(SurfIext)
        App.ActiveDocument.recompute() 
        return
    def modifSurf(self,fp):
        #
        # Calcul des surfaces à partir des filets
        #
        NSectionsA=[]
        NSectionsE=[]
        NSectionsI=[]
        NSectionsIE=[]
        for i in range(fp.Nfilets):
            I=str(i+1)
            NSectionsA.append((App.ActiveDocument.getObject("Filet3Da"+I),"Edge1"))
            NSectionsE.append((App.ActiveDocument.getObject("Filet3De"+I),"Edge1"))
            NSectionsI.append((App.ActiveDocument.getObject("Filet3Di"+I),"Edge1"))
            NSectionsIE.append((App.ActiveDocument.getObject("Filet3Die"+I),"Edge1"))
        SurfA = App.ActiveDocument.SurfA
        SurfA.NSections=NSectionsA 
        SurfE = App.ActiveDocument.SurfE
        SurfE.NSections=NSectionsE 
        SurfI = App.ActiveDocument.SurfI
        SurfI.NSections=NSectionsI 
        SurfIE = App.ActiveDocument.SurfIE
        SurfIE.NSections=NSectionsIE 
        SurfA.recompute() 
        SurfE.recompute()
        SurfI.recompute()
        SurfIE.recompute()
        return
    def calculVolume(self,fp):
        #
        # Calcul des volumes à partir des surface
        #
        RevIext=App.ActiveDocument.addObject("Part::Revolution","RevIext")
        RevIext.Source = App.ActiveDocument.SurfIext
        RevIext.Axis = (0.000000000000000,0.000000000000000,1.000000000000000)
        RevIext.Base = (0.000000000000000,0.000000000000000,0.000000000000000)
        RevIext.Angle = fp.Sens*360/fp.Naubes
        RevIext.Solid = False
        RevIext.AxisLink = None
        RevIext.Symmetric = False
        App.ActiveDocument.SurfIext.Visibility = False
        RevIext.ViewObject.ShapeColor=getattr(RevIext.getLinkedObject(True).ViewObject,'ShapeColor',RevIext.ViewObject.ShapeColor)
        RevIext.ViewObject.LineColor=getattr(App.ActiveDocument.SurfIext.getLinkedObject(True).ViewObject,'LineColor',RevIext.ViewObject.LineColor)
        RevIext.ViewObject.PointColor=getattr(App.ActiveDocument.SurfIext.getLinkedObject(True).ViewObject,'PointColor',RevIext.ViewObject.PointColor)
        RevIext.recompute()
        RevE=App.ActiveDocument.addObject("Part::Revolution","RevE")
        RevE.Source = App.ActiveDocument.SurfE
        RevE.Axis = (0.000000000000000,0.000000000000000,1.000000000000000)
        RevE.Base = (0.000000000000000,0.000000000000000,0.000000000000000)
        RevE.Angle = -fp.Sens*360/fp.Naubes
        RevE.Solid = False
        RevE.AxisLink = None
        RevE.Symmetric = False
        App.ActiveDocument.SurfE.Visibility = False
        RevE.ViewObject.ShapeColor=getattr(RevE.getLinkedObject(True).ViewObject,'ShapeColor',RevE.ViewObject.ShapeColor)
        RevE.ViewObject.LineColor=getattr(App.ActiveDocument.SurfE.getLinkedObject(True).ViewObject,'LineColor',RevE.ViewObject.LineColor)
        RevE.ViewObject.PointColor=getattr(App.ActiveDocument.SurfE.getLinkedObject(True).ViewObject,'PointColor',RevE.ViewObject.PointColor)
        RevE.recompute()
        Volume=App.activeDocument().addObject("Part::MultiCommon","Volume")
        Volume.Shapes = [RevIext,RevE]
        RevIext.Visibility=False
        RevE.Visibility=False
        Volume.ViewObject.ShapeColor=getattr(RevIext.getLinkedObject(True).ViewObject,'ShapeColor', Volume.ViewObject.ShapeColor)
        Volume.ViewObject.DisplayMode=getattr(RevIext.getLinkedObject(True).ViewObject,'DisplayMode',Volume.ViewObject.DisplayMode)
        App.ActiveDocument.Domaine3D.addObject(RevIext)
        App.ActiveDocument.Domaine3D.addObject(RevE)
        App.ActiveDocument.Domaine3D.addObject(Volume)
        App.ActiveDocument.recompute()
        return

class DiscPoints3D:
    def __init__(self, fpV, fpM, fpC, fp): 
#        print("DiscPoints3D.__init__")
        fpV.addProperty("App::PropertyLink", "fpM",      "Discretization",   "Courbe méridienne discrétisée d'origine").fpM = fpM
        fpV.addProperty("App::PropertyLink", "fpC",      "Discretization",   "Courbe cascade discrétisée d'origine").fpC = fpC
        fpV.addProperty("App::PropertyLink", "fp",      "Discretization",   "Parametres").fp = fp
        fpV.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points").Points
        fpV.addProperty("App::PropertyInteger",   "Number",    "Discretization",   "Number").Number=fp.Npts
#        print(fpV.PropertiesList)
        fpV.Proxy=self
        self.execute(fpV)
#        print("DiscPoints3D.__init__ - fin")
        return 
    def execute(self, fpV):
#        print("DiscPoints3D.execute")
#        print(fpV.fpM.Name)
#        print(fpV.fpC.Name)
        FiletM=fpV.fpM.Points
        FiletC=fpV.fpC.Points
        fp=fpV.fp
        i=0
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
            listePt.append(App.Vector(x,y,z)) 
            i+=1
        fpV.Points=listePt
        fpV.Shape = Part.Compound([Part.Vertex(k) for k in fpV.Points])
 #       print("DiscPoints3D.execute - fin")
        return 
    def onChanged(self, fpV, prop):
#        print('DiscPoint3D.onChanged propriété changée: '+prop)
        if (prop == "Number"):
 #           print('on effectue le changement')
            self.execute(fpV)
        return        

class DiscPoints3Die:
    def __init__(self, fpV, fpM, fpCI, fpCE, fp): 
#        print("DiscPoints3Die.__init__")
        fpV.addProperty("App::PropertyLink", "fpM",      "Discretization",   "Courbe méridienne discrétisée d'origine").fpM = fpM
        fpV.addProperty("App::PropertyLink", "fpCI",      "Discretization",   "Courbe cascade intrados discrétisée d'origine").fpCI = fpCI
        fpV.addProperty("App::PropertyLink", "fpCE",      "Discretization",   "Courbe cascade extrados discrétisée d'origine").fpCE = fpCE
        fpV.addProperty("App::PropertyLink", "fp",      "Discretization",   "Parametres").fp = fp
        fpV.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points").Points
        fpV.addProperty("App::PropertyInteger",   "Number",    "Discretization",   "Number").Number=fp.Npts
#        print(fpV.PropertiesList)
        fpV.Proxy=self
        self.execute(fpV)
 #       print("DiscPoints3Die.__init__ - fin")
        return 
    def execute(self, fpV):
 #       print("DiscPoints3Die.execute")
        FiletM=fpV.fpM.Points
        FiletCI=fpV.fpCI.Points
        FiletCE=fpV.fpCE.Points
        fp=fpV.fp
        listePt=[]
        Nptsm1=fp.Npts-1
        #Intrados en commençant par le bord de fuite
#        print(fpV.fpCI.Name)
        for i in range(fp.Npts):
            ptM=FiletM[Nptsm1-i]
            ptC=FiletCI[Nptsm1-i]
            r=ptM.x
            z=ptM.z
    #   L'angle calculé est inversé par rapport à la définition de la cascade où le bord d'attaque était l'origine
    #   alors qu'en 3D, c'est le centre de la roue qui est l'origine 
            theta=ptC.z/1000. # puisqu'on avait multiplié l'échelle par 1000 dans Cascade
            x=r*math.cos(theta)
            y=r*math.sin(theta)
            listePt.append(App.Vector(x,y,z)) 
            i+=1
        #Extrados en commençant par le point à i=1
#        print(fpV.fpCE.Name)
        for i in range(1,fp.Npts):
            ptM=FiletM[i]
            ptC=FiletCE[i]
            r=ptM.x
            z=ptM.z
    #   L'angle calculé est inversé par rapport à la définition de la cascade où le bord d'attaque était l'origine
    #   alors qu'en 3D, c'est le centre de la roue qui est l'origine 
            theta=ptC.z/1000. # puisqu'on avait multiplié l'échelle par 1000 dans Cascade
            x=r*math.cos(theta)
            y=r*math.sin(theta)
    #       print(str(x)+',  '+str(y)+',  '+str(z))
            listePt.append(App.Vector(x,y,z))
        fpV.Points=listePt
        fpV.Shape = Part.Compound([Part.Vertex(k) for k in fpV.Points])
 #       print("DiscPoints3Die.execute - fin")
        return 
    def onChanged(self, fpV, prop):
#        print('DiscPoint3Die.onChanged propriété changée: '+prop)
        if (prop == "Number"):
#            print('on effectue le changement')
            self.execute(fpV)
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
#       print('extractionPoints')
        x=[]
        y=[]
        z=[]
#       print(ListePoints)
        for point in ListePoints:
            x.append(point.x)
            y.append(point.y)
            z.append(point.z)
#       print(x)
#       print(y)
#       print(z)
#       print('extractionPoints - fin')
        return (x,y,z)
    def insertionPoints(self,x,y,z):
#       print('insertionPoints')
#       print(x)
#       print(y)
#       print(z)
        n=x.__len__()
        ListePoints=[]
        for i in range(n) : 
            point=App.Vector(x[i],y[i],z[i])
            ListePoints.append(point)
#       print(ListePoints)
#       print('insertionPoints - fin')
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
#       print('DiscEp_s.onChanged propriété changée: '+prop)
        if (prop == "Npts" or prop == "Last"):
    #       print('on effectue le changement')
            self.execute(fpEp_s)
        return
    def execute(self, fpEp_s):
#       print('DiscEp_s.execute')
        ListePoints=fpEp_s.fp_origine.Points
#       print('ListePoints='+str(ListePoints))
        sX=[]
        for k in range (0,fpEp_s.Npts):sX.append(1000.*fpEp_s.Last*k/(fpEp_s.Npts-1))
#       print('sX='+str(sX))
        (X,Y,Z)=self.extractionPoints(ListePoints)
#       print(X)
        cs=CubicSpline(X, Y)
        sY=cs(sX)
#        sY=np.interp(sX,X,Y)
        fpEp_s.Points=self.insertionPoints(sX,sY,Z)
        fpEp_s.Shape = Part.Compound([Part.Vertex(k) for k in fpEp_s.Points])
#       print('DiscEp_s.execute - fin')
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
#       print('DiscCa_s.execute')
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
#       print('r,m,u ='+str(pj.x)+', '+str(m)+', '+str(u))
        for pj in FiletMeridien.Points[1:]:
            r_s.append(pj.x)
            z_s.append(pj.z)
            m+=dm
            u+=1000.*dm/pj.x
            m_s.append(m)
            u_s.append(u)       #u_s est ainsi calculé à partir d'un m fonction de s dans le plan méridien
#       print('u_q= '+str(u_q))
#       print('v_q= '+str(v_q))
#       print('u_s= '+str(u_s))
        cs=CubicSpline(u_q, v_q)
        v_s=cs(u_s)
#        v_s=np.interp(u_s,u_q,v_q)  #v_s est maintenant associé à u_s 
#       print('v_s= '+str(v_s))
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
#       print('Lmns= '+str(Lmns))
#       print('n_s= '+str(n_s))
    #
    #   Récupération des fp LoiEpaisseurs
    #
        LoiEpaisseurIe=App.ActiveDocument.getObject('LoiEpaisseur'+I+'es').Points
        LoiEpaisseurIi=App.ActiveDocument.getObject('LoiEpaisseur'+I+'is').Points 
#       print('LoiEpaisseurIe= '+str(LoiEpaisseurIe))
        Lmne=Lmn/LoiEpaisseurIe[nseg].x	    #corde de l'extrados
        Lmni=Lmn/LoiEpaisseurIi[nseg].x     #corde de l'intrados  
#       print('Lmne= '+str(Lmne))
#       print('Lmni= '+str(Lmne))
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
#       print('Eey= '+str(Eey))
#       print('Eiy= '+str(Eiy))
#       print('Eex= '+str(Eex))
#       print('Eix= '+str(Eix))
        fpAs.r_s=r_s
        fpAs.z_s=z_s
        fpAs.m_s=m_s
        fpAs.n_s=n_s
        fpAs.u_s=u_s
        Ee_s=[]
        Ee_ss=[]
        if (not np.all(np.diff(Eex) > 0)): App.Console.PrintWarning("Eex is not monotonically increasing \n")
        cs=CubicSpline(Eex, Eey)
        Ee_s=cs(Lmns)
#        Ee_s=np.interp(Lmns,Eex,Eey)
        Ei_s=[]
        Ei_ss=[]
        v_ss=[]
        if (not np.all(np.diff(Eix) > 0)): App.Console.PrintWarning("Eix is not monotonically increasing \n")
        cs=CubicSpline(Eix, Eiy)
        Ei_s=cs(Lmns)
#        Ei_s=np.interp(Lmns,Eix,Eiy)
        for j in range(fpAs.Npts):
            Ee_ss.append(Ee_s[j])
            Ei_ss.append(Ei_s[j])
            v_ss.append(v_s[j])
        fpAs.v_s=v_ss
        fpAs.Ee_s=Ee_ss
        fpAs.Ei_s=Ei_ss
        fpAs.Points=self.insertionPoints(t,u_s,v_s)
        fpAs.Shape = Part.Compound([Part.Vertex(k) for k in fpAs.Points])
#       print('v_s')
#       print(v_s)
##       print('fpAs.Shape.Compounds[0].Vertexes[k]')
#        for k in range(fpAs.Npts): debug(fpAs.Shape.Compounds[0].Vertexes[k].Point)
#       print('DiscCa_s.execute - fin')
        return
    def onChanged(self, fpAs, prop):
#       print('DiscAs_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
    #       print('on effectue le changement')
            self.execute(fpAs)
        return

class DiscCl_s:
    def __init__(self, fpLa, fpAs, Npts, i):
        fpLa.addProperty("App::PropertyLink", "fp_origine",      "Discretization",   "Courbe discrétisée d'origine").fp_origine = fpAs
        fpLa.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpLa.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpLa.addProperty("App::PropertyVectorList",   "Points",    "Points âme",   "Points").Points
        fpLa.Proxy=self
        self.execute(fpLa)
        return
    def execute(self,fpLa):
#       print('DiscCl_s.execute')
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
        fpLa.Points=LoiLongueursa
        fpLa.Shape = Part.Compound([Part.Vertex(k) for k in fpLa.Points])
#       print('DiscCl_s.execute - fin')
        return
    def onChanged(self, fpLa, prop):
#       print('DiscCl_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
    #       print('on effectue le changement')
            self.execute(fpLa)
        return
        
class DiscCli_s:
    def __init__(self, fpLi, fpAs, Npts, SensCascade, i):
#       print('DiscCli_s.init')
        fpLi.addProperty("App::PropertyLink", "fp_origine",      "Discretization",   "Courbe discrétisée d'origine").fp_origine = fpAs
        fpLi.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpLi.addProperty("App::PropertyIntegerConstraint","SensCascade","Parameter","Rotation(1:anti-horaire, -1:horaire)").SensCascade=SensCascade
        fpLi.addProperty("App::PropertyFloatList", "ni_j", "Discretization", "Loi épaisseur intrados").ni_j
        fpLi.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpLi.addProperty("App::PropertyVectorList",   "Points",    "Points extrados",   "Points").Points
        fpLi.Proxy=self
        self.execute(fpLi)
#       print('DiscCli_s.init - fin')
        return
    def execute(self,fpLi):
#       print('DiscCli_s.execute')
#       print('fpLi.Npts = '+str(fpLi.Npts))
#       print('fpLi.SensCascade = '+str(fpLi.SensCascade))
        nseg=fpLi.Npts-1
        m_s=fpLi.fp_origine.m_s
        n_s=fpLi.fp_origine.n_s
        Ei_s=fpLi.fp_origine.Ei_s
#       print('m_s = '+str(m_s))
#       print('n_s = '+str(n_s))
#       print('Ei_s = '+str(Ei_s))
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
            nij=n_s[j] + fpLi.SensCascade * Ei_s[j]
            ni_j.append(nij)
            pLi=App.Vector(0,m_s[j],nij)
            LoiLongueursi.append(pLi)
        fpLi.ni_j=ni_j
        fpLi.Points=LoiLongueursi
        fpLi.Shape = Part.Compound([Part.Vertex(k) for k in fpLi.Points])
#       print('DiscCli_s.execute - fin')
        return
    def onChanged(self, fpLi, prop):
#       print('DiscCli_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
    #       print('on effectue le changement')
            self.execute(fpLi)
#       print('DiscCli_s.onChanged - fin')
        return
        
class DiscCle_s:
    def __init__(self, fpLe, fpAs, Npts, SensCascade,i):
        fpLe.addProperty("App::PropertyLink", "fp_origine",      "Discretization",   "Courbe discrétisée d'origine").fp_origine = fpAs
        fpLe.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpLe.addProperty("App::PropertyIntegerConstraint","SensCascade","Parameter","Rotation(1:anti-horaire, -1:horaire)").SensCascade=SensCascade
        fpLe.addProperty("App::PropertyFloatList", "ne_j", "Discretization", "Loi épaisseur extrados").ne_j
        fpLe.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpLe.addProperty("App::PropertyVectorList",   "Points",    "Points extrados",   "Points").Points
        fpLe.Proxy=self
        self.execute(fpLe)
        return
    def execute(self,fpLe):
#       print('DiscCle_s.execute')
        nseg=fpLe.Npts-1
        m_s=fpLe.fp_origine.m_s
        n_s=fpLe.fp_origine.n_s
        Ee_s=fpLe.fp_origine.Ee_s
#       print('m_s = '+str(m_s))
#       print('n_s = '+str(n_s))
#       print('Ee_s = '+str(Ee_s))
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
            nej=n_s[j] + fpLe.SensCascade*Ee_s[j]
            ne_j.append(nej)
            pLe=App.Vector(0.,m_s[j],nej)
            LoiLongueurse.append(pLe)
        fpLe.ne_j=ne_j
        fpLe.Points=LoiLongueurse
        fpLe.Shape = Part.Compound([Part.Vertex(k) for k in fpLe.Points])
#       print('DiscCle_s.execute - fin')
        return
    def onChanged(self, fpLe, prop):
#       print('DiscCle_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
    #       print('on effectue le changement')
            self.execute(fpLe)
        return
        

class DiscCe_s:
    def __init__(self, fpAe, fpAs, fpLe, Npts, i):
        fpAe.addProperty("App::PropertyLink", "fp_origine1",      "Discretization",   "Courbe discrétisée d'origine").fp_origine1 = fpAs
        fpAe.addProperty("App::PropertyLink", "fp_origine2",      "Discretization",   "Courbe discrétisée d'origine").fp_origine2 = fpLe
        fpAe.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpAe.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpAe.addProperty("App::PropertyVectorList",   "Points",    "Points extrados",   "Points").Points
        fpAe.Proxy=self
        self.execute(fpAe)
        return
    def execute(self,fpAe):
#       print('DiscCe_s.execute')
        r_s=fpAe.fp_origine1.r_s
        n_s=fpAe.fp_origine1.n_s
        u_s=fpAe.fp_origine1.u_s
        v_s=fpAe.fp_origine1.v_s
        ne_j=fpAe.fp_origine2.ne_j
#       print('r_s = '+str(r_s))
#       print('n_s = '+str(n_s))
#       print('u_s = '+str(u_s))
#       print('v_s = '+str(v_s))
#       print('ne_j = '+str(ne_j))
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
        fpAe.Points=LoiCascadee
        fpAe.Shape = Part.Compound([Part.Vertex(k) for k in fpAe.Points])
#       print('DiscCe_s.execute - fin')
        return
    def onChanged(self, fpAe, prop):
#       print('DiscCe_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
    #       print('on effectue le changement')
            self.execute(fpAe)
        return
        
class DiscCi_s:
    def __init__(self, fpAi, fpAs, fpLi, Npts, i):
        fpAi.addProperty("App::PropertyLink", "fp_origine1",      "Discretization",   "Courbe discrétisée d'origine").fp_origine1 = fpAs
        fpAi.addProperty("App::PropertyLink", "fp_origine2",      "Discretization",   "Courbe discrétisée d'origine").fp_origine2 = fpLi
        fpAi.addProperty("App::PropertyInteger", "Npts", "Parameter", "Nombre de points à discrétiser").Npts =Npts
        fpAi.addProperty("App::PropertyInteger",   "i",    "Discretization",   "No du filet").i=i
        fpAi.addProperty("App::PropertyVectorList",   "Points",    "Points intrados",   "Points").Points
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
        fpAi.Points=LoiCascadei
        fpAi.Shape = Part.Compound([Part.Vertex(k) for k in fpAi.Points])
        return
    def onChanged(self, fpAe, prop):
#       print('DiscCe_s.onChanged propriété changée: '+prop)
        if (prop == "Npts"):
    #       print('on effectue le changement')
            self.execute(fpAe)
        return