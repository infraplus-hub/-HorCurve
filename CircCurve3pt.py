#
# CirCurve3pt : Determaine horizontal curve from 3-points (linestring),
#         named 'P1','PI' and 'PN'.  It requires 'RADIUS' of 
#         the circular curve for tangentially fit next to the 3-points 
#         form deflected lines. It results list of tangential points 
#         'PC' and 'PT'. After that user will specify number of 
#         'sampling points' to be produced for curve representation.
# Revision:
# V 1.0 : Phisan Santitamont, Chulalongkorn University
#                20 Mar 2021 phisan.chula@gmail.com
# V 1.1 : refractoring to object oriented       
#
#
import numpy as np
import math,sys,os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from shapely.affinity import translate, rotate
from shapely import wkt
import matplotlib.pyplot as plt

#####################################################################
def _CalcDeflAng( line  ):
    ''' calculate deflection angles from three consecutive points
        forming two independent lines. The 3-points must not
        lie on the same line.  It eturns delfection angel with 
        sign +/- which refered to prior alignment following:-
        + for right deflection andi - for left deflection '''
    x0,y0 = line.coords[0]
    x1,y1 = line.coords[1]
    x2,y2 = line.coords[2]
    chk = (x1-x0)*(y2-y0)-(x2-x0)*(y1-y0)   # on the left / right
    if  math.isclose(chk,0.0):
        print( '***ERROR*** 3 points might lie on a line')
        raise
    v1 = [x1-x0, y1-y0]
    v2 = [x2-x1, y2-y1]
    uv1 = v1/ np.linalg.norm(v1)
    uv2 = v2/ np.linalg.norm(v2)
    dot = np.dot( uv1, uv2 )
    ang = np.arccos( dot )
    if chk>0.0:  # deflected to the left
        return -ang
    else:  # deflected to the right
        return +ang

#####################################################################
def _GenNormCircular( R, CenAng, NUM_PNT=40  ):
    ''' generate normalized circular curve centered at (0,0) with 
        specified 'centraol angle of curve', series of sampling
        points are generate and encoded as LineString.
    '''
    dCenAng = np.linspace( -CenAng/2., +CenAng/2., num=NUM_PNT, endpoint=True) 
    xp = R*np.sin( dCenAng )
    yp = R*np.cos( dCenAng )
    pnts = list()
    for x,y in zip(xp,yp):
        pnts.append( Point( x,y ) )
    return LineString( pnts )

#####################################################################
def _GenHorizCircCurve( alignm , RADIUS=1000, NUM_PNT=10):
    ''' align is LineString with 3-pionts and middle vertice has 
        some deflection '''
    Dflc_Ang = _CalcDeflAng( alignm )
    norm_curve = _GenNormCircular( RADIUS,Dflc_Ang,NUM_PNT=NUM_PNT )
    ##########################################
    pnt_P1 = Point(alignm.coords[0])  # first point
    pnt_PN = Point(alignm.coords[-1]) # last point
    T = abs( RADIUS*math.tan( Dflc_Ang/2 ) )

    pnt_PI = Point(alignm.coords[1])
    dist_PI = alignm.project( pnt_PI, normalized=False )

    dist_PC = dist_PI-T
    pnt_PC = alignm.interpolate( dist_PC , normalized=False ) 

    dist_PT = dist_PI+T
    pnt_PT = alignm.interpolate( dist_PT , normalized=False ) 

    dir_P1_PI = math.atan2( pnt_PI.y-pnt_P1.y, pnt_PI.x-pnt_P1.x )
    if Dflc_Ang>0.0:
        rot_ang = -Dflc_Ang/2 + dir_P1_PI
    else:
        rot_ang = (-Dflc_Ang/2 + dir_P1_PI) + math.pi
    curve_rot = rotate( norm_curve,rot_ang, origin=(0,0), use_radians=True ) 
    curve_at_PC = Point( curve_rot.coords[0] )  # move to 
    Curve_Align = translate( curve_rot, 
         xoff=pnt_PC.x-curve_at_PC.x, yoff=pnt_PC.y-curve_at_PC.y )
    Circ_Cent = translate( Point(0,0), 
         xoff=pnt_PC.x-curve_at_PC.x, yoff=pnt_PC.y-curve_at_PC.y )
    # create dataframe but not GeoDataFrame !!! 
    df_Pnt = pd.DataFrame( [ ['P1',pnt_P1],['PC',pnt_PC],['PI',pnt_PI],
                ['PT',pnt_PT],['PN',pnt_PN] ], columns=['Name','geometry'] )
    def to_xy( row ):
        x = row.geometry.x
        y = row.geometry.y
        return pd.Series([x,y])
    df_Pnt[['x','y']] = df_Pnt.apply( to_xy, axis='columns')
    #import pdb; pdb.set_trace()
    return df_Pnt, Curve_Align, Circ_Cent, Dflc_Ang  

#####################################################################
class CircularCurve:
    ''' CircularCurve is instantiated by 3-points LINESTRING in either
        WKT or Shapely/LineString and optional number of points
        representing the cicular curve.
    '''
    def __init__( self, WKT_LS, RADIUS, NUM_PNT=10):
        self.Radius = RADIUS
        if type( WKT_LS ) is str: # WKT "LINESTRING( x y, x y, x y )"
            self.LS_3pt = wkt.loads( WKT_LS )         
        else:                   # Shapely.LineString()
            self.LS_3pt = WKT_LS          
        #import pdb; pdb.set_trace()
        self.df_Pnt, self.LS_Curve, self.Circ_Cent, self.Dflc_Ang =\
              _GenHorizCircCurve( self.LS_3pt, RADIUS=RADIUS, NUM_PNT=NUM_PNT )
        self.LenCurve = abs(self.Dflc_Ang)*RADIUS
        pass

    def Plot_Curve(self, PLOT_FILE, TITLE, SIZE=(10,10) ):
        def plot_line(ax, line, COLOR='#6699cc', WIDTH=3 ):
            x,y = line.xy
            ax.plot( x,y, color=COLOR, alpha=0.7, 
                    linewidth=WIDTH, solid_capstyle='round')
        fig,ax = plt.subplots(1,1, figsize=SIZE )
        self.df_Pnt.plot( kind='scatter', x='x', y='y' ,color='red', 
                            s=100 ,ax=ax) 
        for i,row in self.df_Pnt.iterrows():
            x,y = row.geometry.x, row.geometry.y
            ax.text( x,y , row.Name , fontsize=24 )
        plot_line( ax, self.LS_3pt )
        plot_line( ax, self.LS_Curve, COLOR='red' )
        xc,yc = self.Circ_Cent.coords[0]
        xcv,ycv = self.LS_Curve.coords[ len(self.LS_Curve.coords)//2 ]
        #import pdb; pdb.set_trace()
        arrow_wid = int(self.LS_3pt.length*0.005)
        ax.arrow( xc,yc, xcv-xc,ycv-yc , width=arrow_wid,
            fc='red', ec='red', length_includes_head=True)
        #####################################
        ax.ticklabel_format(useOffset=False, style='plain')
        ax.set_aspect( 'equal' , adjustable='box' )
        plt.setp(ax.get_xticklabels(), rotation=90, ha='right')
        plt.grid(True)
        plt.title( TITLE )
        fig.tight_layout()
        if PLOT_FILE: plt.savefig( f'{PLOT_FILE}' )
        else: plt.show()
        plt.clf()

    def Report_Data(self, REPORTER ):
        REP=REPORTER
        REP.PRN( 'Input 3pt Traverse : {}'.format( list(self.LS_3pt.coords) ) )
        REP.PRN( 'Input Radius    : {:.3f} meter.'.format( self.Radius ))
        REP.PRN( 'Circular Curve Data: ' )
        REP.PRN( 'Deflection Angle: {:+.5f} degree'.format( 
                                        np.degrees(self.Dflc_Ang)))
        REP.PRN( 'Length of Curve : {:.3f} meter.'.format( self.LenCurve ))
        REP.PRN( 'Circle Center   : ({:.3f},{:.3f})'.format( 
                                    *self.Circ_Cent.coords[0] ))
        for p in ('PC','PI','PT'):
            p_geom = self.df_Pnt[self.df_Pnt.Name==p].iloc[0].geometry 
            REP.PRN( '"{}" : ({:.3f},{:.3f})'.format( p, p_geom.x,p_geom.y )) 
        REP.PRN('===== Coordinates of Circular Curve =====')
        for i,(x,y) in enumerate( list( self.LS_Curve.coords) ):
            REP.PRN('C{},{:.3f},{:.3f}'.format( i+1,x, y) )

###################################################################
class Report:
    def __init__(self):
        self.LINES = list()
    def PRN(self, msg ):
        print( msg )
        self.LINES.append( msg+'\n' )
    def PARAM(self):
        anno = ''
        for line in self.LINES:
            if line[0]=='@':
                anno = anno+line
        #import pdb; pdb.set_trace()
        return anno

#####################################################################
#####################################################################
#####################################################################
if __name__=="__main__": 
    Rep = Report()
    if len(sys.argv)==4: 
        WKT    = sys.argv[1]
        RADIUS = float(sys.argv[2])
        NUM_PNT    = int( sys.argv[3] )
        cc = CircularCurve( WKT, RADIUS=RADIUS, NUM_PNT=NUM_PNT )
    else:
        #WKT = 'LINESTRING (0 5000, 10000 7000, 10000 0)'
        #WKT = 'LINESTRING (0 5000, 10000 7000, 14000 0)'
        WKT = 'LINESTRING ( 496488 2086098, 495612 2086130, 495827 2085535)'
        #WKT = 'LINESTRING (0 5000, 10000 5000, 10000 12000)'

        cc = CircularCurve( WKT, RADIUS=200., NUM_PNT=10 )
   
    RESULT = 'CACHE/GENCIRCCURVE3pt'
    FILE_CURV = str(RESULT) + '_CURVE.png'
    FILE_REPO = str(RESULT) + '_REPORT.txt'

    cc.Report_Data( Rep )

    ################################################
    #import pdb; pdb.set_trace()
    cc.Plot_Curve( FILE_CURV, 'GENCIRCCURVE3pt'  )
    with open( FILE_REPO, 'w' ) as f:
        f.writelines( Rep.LINES )

    if 0:
        # 3-point alignment !!!
        alignments = (
        LineString( [ Point(0,5000), Point(10000,7000), Point(10000, 0) ] ),
        LineString( [ Point(0,5000), Point(10000,7000), Point(7000, -5000) ] ),
        LineString( [ Point(0,5000), Point(10000,7000), Point(10000, 15000) ] ),
        LineString( [ Point(0,5000), Point(10000,7000), Point(13000, 15000) ] )
        )
        for i, align in enumerate( alignments):
            print(70*'=')
            #df_Pnt, curve, dflc_ang =  GenHorizCircCurve( align, RADIUS=4000 )
            cc =  CircularCurve( align, RADIUS=4000 )

            print( 'DEFLECTION angle = {} deg.'.format( 
                                np.degrees(cc.Dflc_Ang ) ) )
            df_Pnt = gpd.GeoDataFrame( cc.df_Pnt,   # DataFrame to GeoDataFrame
                    crs='epsg:32647', geometry=cc.df_Pnt.geometry )
            print( df_Pnt )
            print( cc.LS_Curve )
            cc.Plot_Curve( PLOT_FILE=f'CACHE/PLOT_CURVE_{i}.png' )
    #import pdb; pdb.set_trace()
