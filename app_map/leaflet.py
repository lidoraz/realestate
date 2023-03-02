#
# # https://lyz-code.github.io/blue-book/coding/python/dash_leaflet/
#
import dash
import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash import html, Output, Input
import numpy as np

app = dash.Dash(__name__)

coffee_shops = [
    dict(name="In Gamba", lat=45.526891, lon=-73.598044, metadata='AAA'),
    dict(name="Cafe Olympico", lat=45.524153, lon=-73.600381, metadata='BBB'),
    dict(name="The Standard", lat=45.523087, lon=-73.595243, metadata='CCC'),
]
geojson_coffee = dlx.dicts_to_geojson(
    [{**shop, **dict(tooltip=shop["name"])} for shop in coffee_shops]
)
print(geojson_coffee)
exit(0)
app.layout = html.Div(children=[
    dl.Map(children=[dl.TileLayer(),

                     dl.LayerGroup(id="layer"),
                     dl.LayerGroup(id="layer1"),
                     dl.GeoJSON(data=geojson_coffee, id="geojson", zoomToBounds=True),
                     dl.GeoJSON(
                         url='https://pkgstore.datahub.io/core/geo-countries/countries/archive/23f420f929e0e09c39d916b8aaa166fb/countries.geojson',
                         id="countries",
                         options=dict(style=dict(opacity=0, fillOpacity=0))) #,
                         # hoverStyle=dict(weight=2, color='red', dashArray='', opacity=1))
                     ],

           style={'width': '1000px', 'height': '500px'}, zoom=3, id='map'),

    html.Div(id='country'), html.Div(id='marker'),

    html.Div(id='Country info pane')

])


@app.callback(Output("marker", "children"), Input("geojson", "click_feature"))
def map_marker_click(feature):
    if feature is not None:
        print("marker clicked!")
        return str(feature)


@app.callback(Output("layer", "children"), Input("countries", "click_feature"))
def map_click(feature):
    if feature is not None:
        print('invoked')
        return [dl.Marker(position=[np.random.randint(-90, 90), np.random.randint(-185, 185)])]


@app.callback(Output('Country info pane', 'children'),
              Input('countries', 'hover_feature'))
def country_hover(feature):
    if feature is not None:
        country_id = feature['properties']['ISO_A3']
        return country_id


@app.callback(Output('layer1', 'children'),
              Input('countries', 'hover_feature'))
def country_hover(feature):
    if feature is not None:
        return dl.Polygon(positions=[[30, 40], [50, 60]], color='#ff002d', opacity=0.2)


if __name__ == '__main__':
    app.run_server(debug=True)
