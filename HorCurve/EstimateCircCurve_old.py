#
#
# Estimating horizontal circular curve from user specified 3 
#      linestrings namely :
#           1) lead-in linestring assummed straight centerline
#           2) on-curve linestring 
#           3) lead-out linestring over straight centerline
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
from GenerateCircCurve import *
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'

#############################################################
def convert_wgs_to_utm(lon, lat):
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
    df_kml = gpd.read_file( KML_FILE, driver='KML')
    df_align = pd.DataFrame()
    for i,row in df_kml.iterrows():
        xy = np.array( row.geometry.coords )
        df_ = pd.DataFrame.from_dict( { 'lng': xy[:,0], 'lat': xy[:,1]} )
        df_['Name']=row.Name
        df_align = df_align.append( df_ )
    df_align.reset_index( inplace=True, drop=True )
    df_align = gpd.GeoDataFrame( df_align, crs='epsg:4326',
            geometry=gpd.points_from_xy( df_align.lng, df_align.lat ))
    ########################
    mid = df_align.iloc[ len(df_align)//2 ]
    utm = convert_wgs_to_utm( mid.lng, mid.lat )
    df_align = df_align.to_crs( utm )
    #import pdb; pdb.set_trace()
    df_align['E'] = df_align.geometry.apply(lambda p: p.x)
    df_align['N'] = df_align.geometry.apply(lambda p: p.y)
    return df_align 

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
def Find_PI( df_in, df_out ):
    FACT=3
    lines = list()
    for df in (df_in , df_out ):
        if df.iloc[0].Name=='Lead_In': 
            PC = Point( df.iloc[0].E,   df.iloc[0].N_pred ) 
            FR,TO=0,-1
        else: 
            PT = Point( df.iloc[-1].E,   df.iloc[-1].N_pred ) 
            FR,TO=-1,0
        PC_fr = Point( df.iloc[FR].E, df.iloc[FR].N_pred )
        PC_to = Point( df.iloc[TO].E, df.iloc[TO].N_pred )
        ls = LineString( [PC_fr,PC_to] )
        ls_sc = scale( ls, xfact=FACT, yfact=FACT, origin=PC_fr )
        lines.append( ls_sc )
    df_leadline = gpd.GeoDataFrame({'Alignment': ['lead_in','lead_out']},
            crs=df_in.crs, geometry=lines )
    PI = lines[0].intersection( lines[1] )
    #import pdb; pdb.set_trace()
    align_trav = LineString( [PC,PI,PT] )
    df_trav = pd.DataFrame.from_dict( 
            {'Name':['Traverse'],  'geometry':[align_trav]  } )
    df_trav = gpd.GeoDataFrame( df_trav, crs = df_in.crs, 
            geometry=df_trav.geometry )
    return df_leadline, df_trav

def EstimateRadius( df_curve ):
    data = np.array( df_curve[['E','N']] )
    xc,yc,r,stat = cf.hyper_fit(data)
    #import pdb; pdb.set_trace()
    return xc,yc,r

######################################################
if __name__ == "__main__":
    KML_FILE = Path('Data/Sport700Yr.kml')
    if len(sys.argv)==2:
        KML_FILE  = Path( sys.argv[1] )
    print(f'Reading lead-in,curve, lead-out sampling point : {KML_FILE}' )
    STEM = KML_FILE.stem
    df_align = ReadKML_Align( KML_FILE )
    ##################################################
    df = df_align[df_align.Name=='Lead_In'].copy()
    df_in = FitStraight( df )
    df = df_align[df_align.Name=='Lead_Out'].copy()
    df_out = FitStraight( df )

    #################################################
    df_lead,df_trav = Find_PI( df_in, df_out )
    xc,yc,RADIUS=EstimateRadius( df_align[df_align.Name=='Curve'] )
    print('Radius : {:.3f} meter.'.format( RADIUS ) )
    df_final  = CreateHorCurve( df_trav.iloc[0].geometry, RADIUS=RADIUS )

    PLOT_FILE  = f'PLOT_{STEM}'
    print(f'Writing plot file : {PLOT_FILE}. png|kml')
    #import pdb; pdb.set_trace()
    if 1:
        fig,ax = plt.subplots(1,1, figsize=(15,15) )
        df_align.plot( ax = ax , color='pink' )
        df_align[df_align.Name=='Curve'].plot( ax = ax , color='green' )
        df_trav.plot( ax=ax, color='yellow')
        df_final.plot( ax=ax, color='red')
        #df_lead.plot( ax=ax, color='yellow')
        ax.ticklabel_format(useOffset=False, style='plain')
        ax.set_aspect( 'equal' , adjustable='box' )
        ax.grid( True )
        plt.suptitle( KML_FILE )
        plt.setp(ax.get_xticklabels(), rotation=90, ha='right')
        fig.tight_layout()
        plt.savefig( PLOT_FILE+'.png' )
        #plt.show()
    if 1:
        df_final=df_final.to_crs('epsg:4326')
        with fiona.Env():
            df_final.to_file( PLOT_FILE+'kml', driver='KML')

    #import pdb; pdb.set_trace()
