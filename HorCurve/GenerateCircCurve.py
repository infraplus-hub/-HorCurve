#
#
# Determaine Horizontal Curve for sampling points
#
#
import numpy as np
import math
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from shapely.affinity import translate, rotate
import matplotlib.pyplot as plt

#####################################################################
def angle_2vect( line  ):
    ''' plot '''
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
    if chk>0.0:  # on the left
        return -ang
    else:
        return +ang

#####################################################################
def plot_line(ax, lin, COLOR='#6699cc', WIDTH=3 ):
    x, y = lin.xy
    ax.plot(x, y, color=COLOR, alpha=0.7, linewidth=WIDTH, 
            solid_capstyle='round', zorder=2)

#####################################################################
def GenNormCircular( R, CenAng, NUM=40  ):
    ''' generate normalized circular curve centered at (0,0) 
    '''
    dCenAng = np.linspace( -CenAng/2., +CenAng/2., num=NUM, endpoint=True) 
    xp = R*np.sin( dCenAng )
    yp = R*np.cos( dCenAng )
    if 0:
        plt.plot( xp, yp )
        #plt.ylim( 0, 350 )
        plt.grid()
        plt.gca().set_aspect("equal")
        plt.show()
    pnts = list()
    for x,y in zip(xp,yp):
        pnts.append( Point( x,y ) )
    line = LineString( pnts )
    return line

#####################################################################
def CreateHorCurve( alignm , RADIUS=1000):
    ''' align is LineString with 3-pionts and middle vertice has 
        some deflection '''
    #import pdb; pdb.set_trace()
    dflc_ang = angle_2vect( alignm )
    #print( 'angle = ', np.degrees(dflc_ang) )
    norm_curve = GenNormCircular( RADIUS, dflc_ang , NUM=10 )
    dflc_ang = angle_2vect( alignm )
    ##########################################
    pnt_P1 = Point(alignm.coords[0])
    pnt_PN = Point(alignm.coords[-1])
 
    T=RADIUS*math.tan( dflc_ang/2 )
    pnt_PI = Point(alignm.coords[1])
    dist_PI = alignm.project( pnt_PI, normalized=False )
    dist_PC = dist_PI-T
    pnt_PC = alignm.interpolate( dist_PC , normalized=False ) 
    dist_PT = dist_PI+T
    pnt_PT = alignm.interpolate( dist_PT , normalized=False ) 

    dir_P1_PI = math.atan2( pnt_PI.y-pnt_P1.y, pnt_PI.x-pnt_P1.x )
    if dflc_ang>0.0:
        rot_ang = -dflc_ang/2 + dir_P1_PI
    else:
        rot_ang = (-dflc_ang/2 + dir_P1_PI) + math.pi
    curve_rot = rotate( norm_curve,rot_ang, 
                    origin=(0,0), use_radians=True ) 
    curve_at_PC = Point( curve_rot.coords[0] )

    if dflc_ang>0.0:
        curve_align = translate( curve_rot, 
            xoff=pnt_PC.x-curve_at_PC.x, yoff=pnt_PC.y-curve_at_PC.y )
    else: 
        curve_align = translate( curve_rot, 
            xoff=pnt_PT.x-curve_at_PC.x, yoff=pnt_PT.y-curve_at_PC.y )

    ##########################################
    df = pd.DataFrame( [ ['P1',pnt_P1],['PC',pnt_PC],['PI',pnt_PI],
                   ['PT',pnt_PT],['PN',pnt_PN], ['Curve',curve_align] ],  
                    columns=['Name','geometry'] )
    df = gpd.GeoDataFrame( df, crs='epsg:32647', geometry=df.geometry )
    return df 

#####################################################################
if __name__=="__main__": 
    # define 3-point alignment !!!
    #alignm = LineString( [ Point(0,5000), Point(10000,5000), Point(20000, 4000) ] )
    #alignm = LineString( [ Point(0,5000), Point(10000,5000), Point(20000, 2000) ] )
    alignm = LineString( [ Point(0,5000), Point(10000,7000), Point(20000, 500) ] )
    #alignm = LineString( [ Point(0,5000), Point(10000,7000), Point(10000, 0) ] )
    #alignm = LineString( [ Point(0,5000), Point(10000,7000), Point(10000, 0) ] )
    #alignm = LineString( [ Point(0,5000), Point(10000,7000), Point(10000, 15000) ] )

    #######################################################################
    df_curve  = CreateHorCurve( alignm, RADIUS=4000 )
    if 1:
        fig,ax = plt.subplots(1,1, figsize=(15,15) )
        df_curve.iloc[:5].plot(  color='red', ax=ax )
        df_curve.iloc[5:].plot(  color='green', ax=ax )
        #df_curve.iloc[:5].apply(lambda x: ax.annotate(s=x.Name, size=15,
        #       xy=x.geometry.coords[0], ha='center', va='center',axis=1))
        plot_line( ax, alignm )
        plt.grid(True)
        plt.gca().set_aspect("equal")
        fig.tight_layout()
        plt.show()

    import pdb; pdb.set_trace()
    print( df_curve.iloc[5].geometry.coords.xy )
#import pdb; pdb.set_trace()
