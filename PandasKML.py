#
#
# PandasKML : plot python/pandas DataFrame in Google KML format
#             All dataframe mush have attributes in column named 
#                'Name' and 'Desc'
# P.Santitamnont ( phisan.chula@gmail.com )
#
#
from simplekml import Kml, Style, Color
from shapely.geometry import Point, LineString, Polygon
import pandas as pd 
import geopandas as gpd

###################################################################
class PlotPntKML:
    def __init__( self, FILE_KML ):
        kml = Kml()
        self.kml = kml
        self.FILE_KML = FILE_KML

    def PlotPnt( self, FOLDER, df, MARKER=('target', Color.red, 5 )):
        ICON, COLOR, SIZE = MARKER 
        icon = 'http://maps.google.com/mapfiles/kml/shapes/{}.png'
        icon = icon.format( ICON )

        fol = self.kml.newfolder(name=FOLDER)
        sharedstyle = Style()
        sharedstyle.iconstyle.color = COLOR
        sharedstyle.iconstyle.scale = SIZE 
        sharedstyle.iconstyle.icon.href = icon
        sharedstyle.labelstyle.color = COLOR
        sharedstyle.labelstyle.scale = SIZE 
        for i,row in df.iterrows(): 
            lng = row.geometry.x
            lat = row.geometry.y
            pnt = fol.newpoint(name=row.Name, coords=[(lng,lat)])
            pnt.description = row.Desc
            pnt.style = sharedstyle  

    def PlotPoly( self, FOLDER, df_geom, WIDTH=5 ):
        if isinstance( df_geom, Polygon):
            import pdb; pdb.set_trace()
        else:
            raise( '***ERROR*** : isinstance( df_geom, Polygon)' )
        fol = self.kml.newfolder(name=FOLDER)
        style = Style()
        style.linestyle.color = Color.rgb(0,255,0,a=127)
        if isinstance( WIDTH, int ):
            style.linestyle.width = WIDTH
        for i,row in df.iterrows(): 
            #import pdb ; pdb.set_trace()
            lng0,lat0 = row.geometry.coords[0][0:2]
            lng1,lat1 = row.geometry.coords[1][0:2]
            lin = fol.newlinestring(name=row['Name'], 
                    description=row['Desc'],
                    coords=[ (lng0,lat0),(lng1,lat1) ])
            lin.style = style

    def PlotLine( self, FOLDER, df, WIDTH=5, COLOR=Color.rgb(0,255,0,a=127) ):
        ''' PlotLine from two points 
        '''
        fol = self.kml.newfolder(name=FOLDER)
        style = Style()
        style.linestyle.color = COLOR 
        if isinstance( WIDTH, int ):
            style.linestyle.width = WIDTH
        for i,row in df.iterrows(): 
            #import pdb ; pdb.set_trace()
            lng0,lat0 = row.geometry.coords[0][0:2]
            lng1,lat1 = row.geometry.coords[1][0:2]
            lin = fol.newlinestring(name=row['Name'], 
                    description=row['Desc'],
                    coords=[ (lng0,lat0),(lng1,lat1) ])
            lin.style = style
    
    def PlotDblLine( self, FOLDER, df ):
        fol = self.kml.newfolder(name=FOLDER)
        style1 = Style()
        style1.linestyle.color = Color.rgb(0,255,0,a=127)
        style1.linestyle.width = 5 
        style2 = Style()
        style2.linestyle.color = Color.rgb(255,0,0,a=127)
        style2.linestyle.width = 15 
        for i,row in df.iterrows(): 
            div,mod = divmod(i,2)
            #import pdb ; pdb.set_trace()
            lng0,lat0,_ = row.geometry.coords[0]
            lng1,lat1,_ = row.geometry.coords[1]
            lin = fol.newlinestring(name=row['Name'], 
                    description=row['Desc'],
                    coords=[ (lng0,lat0),(lng1,lat1) ])
            if mod==0:
                lin.style = style1  
            else:
                lin.style = style2
    ################################################################
    def PlotLineString(self, FOLDER, df_ls, WIDTH=5,
                        COLOR=Color.rgb(0,255,0,a=127) ):
        ''' PlotLine from dataframe of LineString 
        '''
        fol = self.kml.newfolder(name=FOLDER)
        style = Style()
        style.linestyle.color = COLOR 
        if isinstance( WIDTH, int ):
            style.linestyle.width = WIDTH
        for i,row in df_ls.iterrows(): 
            #import pdb ; pdb.set_trace()
            lin = fol.newlinestring(
                    name=row['Name'], 
                    description=row['Desc'],
                    coords= list(row.geometry.coords)  
                    )
            lin.style = style
 

    def Save( self ):
        self.kml.save( self.FILE_KML )


####################################################################
if __name__=="__main__":
    names = list(); lats =list() ; lngs=list()
    for lon in range(-180, 180, 10):
        for lat in range(-180, 180, 10):  # 10 Degree grid of points
            name = '{:.1f}:{:.1f}'.format(lat,lon)
            names.append( name )
            lats.append( lat )
            lngs.append( lon )
    df = pd.DataFrame(  { 'Name': names, 'lat': lats , 'lng': lngs } )
    gdf = gpd.GeoDataFrame( df, geometry=gpd.points_from_xy( df.lng, df.lat ) )
    gdf['Desc'] = 'User Description ...'

    kml = PlotPntKML('gdf_Control.kml' )
    kml.PlotPnt('Benchmark', gdf, ('target',   Color.yellow, 3) )
    kml.PlotPnt('Control',   gdf, ('triangle', Color.red, 3) )
    kml.Save()
    #import pdb; pdb.set_trace()
