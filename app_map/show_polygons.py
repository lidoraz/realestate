import pandas as pd
import geopandas as gpd
import dash_leaflet as dl
import dash_leaflet.express as dlx

import json

# df = pd.read_pickle("../resources/yad2_forsale_df.pk")

# geometry = gpd.points_from_xy(df['long'], df['lat'])
# gdf = gpd.GeoDataFrame(df, crs=3857, geometry=geometry)
#
# # polygons = gdf.dissolve("city").simplify(0.00001) # preserve_topology=True
# # polygons = polygons[polygons.geometry.type == 'MultiPoint']
# polygons = gdf.dissolve("city").convex_hull
# polygons = polygons[polygons.geometry.type == "Polygon"]
# import shapely.wkt
# df['geometry'].apply(lambda x: shapely.wkt.dumps(x, rounding_precision=2))
# shapely.wkt.dumps(p, rounding_precision=2)

###########
# df = pd.read_pickle("../notebooks/df_gush.pk")
#
# # cols = ['GUSH_NUM', 'LOCALITY_N', 'COUNTY_NAM', 'REGION_NAM', 'SHAPE_AREA']
# cols = ['GUSH_NUM']
# cols.append('geometry')
# df_s = df[cols] # [:10]
# # df_s = df_s[:10]
# df_s['tooltip'] = df_s['GUSH_NUM'].astype(str)
# df_s['popup'] = df_s['GUSH_NUM'].astype(str)
# gdf = gpd.GeoDataFrame(df_s)
# d_json = json.loads(gdf.to_json())
# print(d_json)


# gdf = gpd.read_file("../notebooks/dataframe.geojson")
gdf = gpd.read_file("../notebooks/gdf_gush.geojson")
# df = pd.read_csv("../notebooks/city_poly.csv")
from shapely import wkt

# cols = ['GUSH_NUM', 'LOCALITY_N', 'COUNTY_NAM', 'REGION_NAM', 'SHAPE_AREA']
# cols = ['index']
# cols.append('geometry')
# df_s = df[cols]  # [:10]
# df_s = df_s[:10]
from shapely import wkt

# df['geometry'] = df['geometry'].apply(wkt.loads)
gdf['tooltip'] = gdf['COUNTY_NAM'].astype(str) + '</br>' + gdf['GUSH_NUM'].astype(str)
# gdf['tooltip'] = gdf['city'].astype(str) + '\n' + gdf['gush_cnt'].astype(str)



# df_s['popup'] = df_s['GUSH_NUM'].astype(str)
# gdf = gpd.GeoDataFrame(df_s)  # geometry='geometry'
d_json = json.loads(gdf.to_json())
# print(d_json)

# exit(0)
# polygons = gdf['geometry']


# geojson_coffee = dlx.dicts_to_geojson(
#     [{**shop, **dict(tooltip=shop["name"])} for shop in coffee_shops]
# )
# print(gdf)

# polygons = polygons[polygons.index == ' תל אביב יפו']
# print(polygons)
# map_hooray = folium.Map(location=[31.5, 35.314],
#                     zoom_start = 7)
# geo_j = folium.GeoJson(data=polygons.to_json(),
#                            style_function=lambda x: {'fillColor': 'orange'})
# geo_j.add_to(map_hooray)
# map_hooray

# polygons.to_json()

import json

import dash_leaflet.express as dlx

# zipfile = "zip://cb_2019_us_county_20m.zip"
# gdf = gpd.read_file(zipfile)
# alaska = gdf[gdf['STATEFP']=='02']
# geojson = json.loads(polygons.to_json())

# geojson['features'] = [p['properties'] = {'name': 'In Gamba', 'metadata': 'AAA', 'tooltip': 'In Gamba'}  for p in geojson['features']]
# geobuf = dlx.geojson_to_geobuf(geojson)

from dash import html
from dash.dependencies import Input, Output
import dash

app = dash.Dash(__name__)

app.layout = html.Div([dl.Map([
    dl.TileLayer(),
    dl.GeoJSON(data=d_json, format='geojson', zoomToBounds=True, zoomToBoundsOnClick=True)
],
    id="map_",
    style={
        'width': '1000px',
        'height': '500px'
    })
    , html.Div(id='output_')]
)


@app.callback(
    Output(component_id='output_', component_property='children'),
    Input(component_id='map_', component_property='bounds')
)
def update_output_div(bounds):
    return 'Output: {}'.format(bounds)


if __name__ == '__main__':
    app.run_server(debug=True)
