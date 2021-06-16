#
#
PROG='''
EstCircCurve: Estimating horizontal circular curve from specified
              3 group of samplings representing alignments namely :
           1) "Lead_In" linestring for straight line on entering curve
           2) "Curve" linestring representing the circular curve 
           3) "Lead_Out" linestring for straight line on exiting curve 
      and  4) a kilometer post for linear referencing , if any.
'''
# Revision:
# Version 1.0 : Phisan Santitamont, Chulalongkorn University
#                20 Mar 2021 phisan.chula@gmail.com
#
#
import numpy as np
import math,os,sys
import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point, LineString
from shapely.affinity import translate, rotate, scale
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import fiona
import circle_fit as cf
from CircCurve3pt import *
sys.path.append('D:\sourc_code\S21\HorCurve\Dist\Data')
from PandasKML import *
from tabulate import tabulate

for lib in ('kml','KML','libkml','LIBKML'):
    fiona.drvsupport.supported_drivers[lib] = 'rw'

#############################################################
def convert_wgs_to_utm(lon, lat):
    ''' auto UTM EPSG code'''
    utm_band = str((math.floor((lon + 180) / 6 ) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0'+utm_band
    if lat >= 0:
        epsg_code = 'epsg:326' + utm_band
    else:
        epsg_code = 'epsg:327' + utm_band
    return epsg_code

#############################################################
def ReadKML_Align( KML_FILE ):
    ''' read KML and convert to appropriate UTM zone '''
    df_kml = gpd.read_file( KML_FILE, driver='KML')
    df_sampling = pd.DataFrame()
    for i,row in df_kml.iterrows():
        xy = np.array( row.geometry.coords )
        df_ = pd.DataFrame.from_dict( { 'lng': xy[:,0], 'lat': xy[:,1]} )
        df_['Name']=row.Name
        df_sampling = df_sampling.append( df_ )
    df_sampling.reset_index( inplace=True, drop=True )
    df_sampling = gpd.GeoDataFrame( df_sampling, crs='epsg:4326',
            geometry=gpd.points_from_xy( df_sampling.lng, df_sampling.lat ))
    ########################
    mid = df_sampling.iloc[ len(df_sampling)//2 ]
    utm = convert_wgs_to_utm( mid.lng, mid.lat )
    df_sampling = df_sampling.to_crs( utm )
    #import pdb; pdb.set_trace()
    df_sampling['E'] = df_sampling.geometry.apply(lambda p: p.x)
    df_sampling['N'] = df_sampling.geometry.apply(lambda p: p.y)
    return df_sampling 

######################################################
def FitStraight( df ):
    X = df['E'].values.reshape(-1,1)
    Y = df['N'].values.reshape(-1,1)
    linear_regressor = LinearRegression()  # create object for the class
    linear_regressor.fit(X, Y)  # perform linear regression
    Y_pred = linear_regressor.predict(X)  # make predictions
    df['N_pred'] = Y_pred
    df.reset_index( inplace=True,drop=True )
    #import pdb; pdb.set_trace()
    return df

######################################################
def Find_PI( df_SAMPLING, FACT=5 ):
    ''' Find point of intersection PI ,user supplies df_SAMPLING
        with names "Lead_In" and "Lead_Out" 
        Find_PI() will extend the straigth upto FACT times for 
        LineString.intersection().
        Find_PI returns df_TRAVERSE which comprise of '''
    ### make two linestrings ###
    df_in = df_SAMPLING[df_SAMPLING.Name=='Lead_In'].copy()
    df_in = FitStraight( df_in )
    df_out = df_SAMPLING[df_SAMPLING.Name=='Lead_Out'].copy()
    df_out = FitStraight( df_out )
    lines = list()
    for df in (df_in , df_out ):
        if df.iloc[0].Name=='Lead_In': 
            PC = Point( df.iloc[0].E,   df.iloc[0].N_pred ) 
            FR,TO=0,-1
        elif df.iloc[0].Name=='Lead_Out': 
            PT = Point( df.iloc[-1].E,   df.iloc[-1].N_pred ) 
            FR,TO=-1,0
        else:
            print('***ERROR*** "Lead_In" or "Lead_Out" not existed.')
            raise
        fr = Point( df.iloc[FR].E, df.iloc[FR].N_pred )
        to = Point( df.iloc[TO].E, df.iloc[TO].N_pred )
        ls = LineString( [fr,to] )
        ls_sc = scale( ls, xfact=FACT, yfact=FACT, origin=fr )
        lines.append( ls_sc )
    df_leadline = gpd.GeoDataFrame({'Alignment': ['lead_in','lead_out']},
            crs=df_in.crs, geometry=lines )
    PI = lines[0].intersection( lines[1] )  # do intersection()
    align_trav = LineString( [PC,PI,PT] )
    df_TRAVERSE = pd.DataFrame.from_dict( 
            {'Name':['Traverse'],  'geometry':[align_trav]  } )
    df_TRAVERSE = gpd.GeoDataFrame( df_TRAVERSE, crs = df_in.crs, 
            geometry=df_TRAVERSE.geometry )
    return df_TRAVERSE

######################################################
def CalcLinearRef( AlignCurve , df_Pnt, km_post=None ):
    pt_1 =list(df_Pnt[df_Pnt.Name=='P1'].iloc[0].geometry.coords)
    pt_N =list(df_Pnt[df_Pnt.Name=='PN'].iloc[0].geometry.coords)

    pt_all = pt_1.copy()
    pt_all.extend( list( AlignCurve.coords) )
    pt_all.extend( pt_N )
    Al_Curve_Lead = LineString( pt_all )

    if km_post is not None:
        df_Pnt = df_Pnt.append( { 'Name': km_post.Name, 
            'geometry' :km_post.geometry }, ignore_index=True )
    def ProjDist( row, Al_Curve_Lead ):
        if row.geometry.type=='LineString':
            geom = row.geometry.centroid
        else:
            geom = row.geometry
        d = Al_Curve_Lead.project( Point( geom.x, geom.y) ,normalized=False ) 
        return d
    df_Pnt['sampl_dist'] = df_Pnt.apply( ProjDist, axis='columns', 
            args=(Al_Curve_Lead,) )
    if km_post is not None:
        cols = km_post.Name.replace('_',',').replace('+',',').split(',')
        km_post_m = float(cols[1])*1000 + float(cols[2])
        km_sampl_dist = df_Pnt[df_Pnt.Name==km_post.Name].iloc[0].sampl_dist
        df_Pnt['kmpost_dist'] = df_Pnt['sampl_dist']-km_sampl_dist
        df_Pnt['sta_dist'] = df_Pnt['kmpost_dist']+km_post_m
    else:
        df_Pnt['sta_dist'] = df_Pnt['sampl_dist']
    def Dist2KM( dist ):
        full,rest = divmod( dist, 1000 )
        km_str = '{:d}+{:07.3f}'.format( int(dist/1000), rest )
        return km_str
    df_Pnt['Sta_KM'] = df_Pnt['sta_dist'].apply( Dist2KM )
    df_Pnt['x'] = df_Pnt.geometry.x
    df_Pnt['y'] = df_Pnt.geometry.y
    return df_Pnt, Al_Curve_Lead

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

######################################################################
class Estimate_Circular_Curve(CircularCurve): 
    def __init__(self, KML_FILE, NUM_PNT ):
        self.KML_FILE = KML_FILE
        self.KML_STEM = KML_FILE.parent.joinpath( KML_FILE.stem )
        self.OutKML  = str(self.KML_STEM) + '_PLOT.kml'
        self.OutPLOT = str(self.KML_STEM) + '_PLOT.png'
        self.OutREPO = str(self.KML_STEM) + '_REPORT.txt'
        self.OutALIG = str(self.KML_STEM) + '_ALIGN.csv'

        self.df_SAMPLING = ReadKML_Align( KML_FILE )
        ##################################################
        df_TRAVERSE = Find_PI( self.df_SAMPLING )
        XC,YC,RADIUS, self.Sigma = self.EstimateCurve( 
                self.df_SAMPLING[ self.df_SAMPLING.Name=='Curve'] )
        super().__init__( df_TRAVERSE.iloc[0].geometry, 
                RADIUS=RADIUS, NUM_PNT=NUM_PNT ) 
        self.df_Pnt = gpd.GeoDataFrame( self.df_Pnt, 
            crs=self.df_SAMPLING.crs, geometry=self.df_Pnt.geometry )

    def EstimateCurve( self, df_curve ):
        data = np.array( df_curve[['E','N']] )
        #xc,yc,r,stat = cf.hyper_fit(data)
        xc,yc,r,sigma = cf.least_squares_circle(data)
        return xc,yc,r,sigma

    def Calc_Linear_Referencing( self ):
        if np.any( self.df_SAMPLING.Name.str[:3]=='KM_' ): 
            km_post = self.df_SAMPLING[
                    self.df_SAMPLING.Name.str[:3]=='KM_'].iloc[0]
            self.df_Pnt, Al_Curve_Lead = CalcLinearRef( self.LS_Curve, 
                    self.df_Pnt, km_post )
        else:
            self.df_Pnt, Al_Curve_Lead = CalcLinearRef( self.LS_Curve, 
                                         self.df_Pnt, km_post=None )
        self.df_Alignm_All = gpd.GeoDataFrame({'Name': ['P1_PC_PT_PN']},
                crs=self.df_SAMPLING.crs, geometry=[Al_Curve_Lead] )
        return

######################################################
######################################################
######################################################
if __name__ == "__main__":
    if len(sys.argv)==3:
        KML_FILE = Path( sys.argv[1] )
        NUM_PNTS = int(  sys.argv[2] )
    elif len(sys.argv)>=2:
        print('*** ERROR ***')
        print('Usage: {} kml_file NUM_PNT ')
    else:
        #KML_FILE = Path('CACHE/CM_700yr_toS.kml')
        KML_FILE = Path('D:\sourc_code\S21\HorCurve\Dist\Data\Sport700Yr.kml')
        NUM_PNTS = 10

    cc = Estimate_Circular_Curve(KML_FILE, NUM_PNTS )
    cc.Calc_Linear_Referencing()
    ################################################
    Rep = Report()
    Rep.PRN(70*'='); Rep.PRN( PROG ); Rep.PRN(70*'='); 
    Rep.PRN(f'Reading lead-in,curve, lead-out sampling point : {KML_FILE}' )
    Rep.PRN('@RADIUS OF CURVE : {:.3f} m. (+/-{:.1f} m.)'.\
            format( cc.Radius, cc.Sigma ) )
    cc.Report_Data( Rep )
    #################################################
    Rep.PRN(f'Writing report REPORT & PLOT : {cc.KML_STEM}_-->png|kml|txt')
    tab = cc.df_Pnt[['Name','sampl_dist','Sta_KM']].copy()
    tab['sampl_dist']=tab['sampl_dist'].map( '{:.3f}'.format )
    tab.index += 1
    t = tabulate( tab, tab.columns, tablefmt='pretty' )
    Rep.PRN( t )
    ################################
    with open( cc.OutREPO, 'w' ) as f:
        f.writelines( Rep.LINES )
    ###############################
    cc.Plot_Curve( cc.OutPLOT, cc.KML_STEM ) 
    ###############################

    df_Pnt = cc.df_Pnt[['Name','Sta_KM','geometry']].copy()
    df_Pnt.rename( columns={'Sta_KM':'Desc'} ,inplace=True )
    df_Pnt.crs= 'epsg:32647'
    df_Pnt    = df_Pnt.to_crs( epsg=4326 )
    df_Alignm = cc.df_Alignm_All.copy()
    df_Alignm['Desc'] = ('Radius {:.3f} m.<br>'+\
                        ' Deflection Angle : {:.3f} deg.<br>').\
                        format( cc.Radius, np.degrees(cc.Dflc_Ang) )
    df_Alignm = df_Alignm.to_crs( epsg=4326 )
    kml = PlotPntKML( cc.OutKML )
    #import pdb; pdb.set_trace()
    isPI = (df_Pnt.Name=='PI')
    kml.PlotPnt('Station', df_Pnt[~isPI] , ('target',   Color.yellow, 3) )
    kml.PlotPnt('Station', df_Pnt[isPI] , ('target',   Color.red, 3) )
    kml.PlotLineString('Alignment', df_Alignm, WIDTH=10,
                        COLOR=Color.rgb(0,255,0,a=127)   )
    kml.Save()

    print('######### end of EstCircCurve ###############')
