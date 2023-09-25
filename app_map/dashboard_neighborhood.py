import dash_leaflet as dl
import json
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash
from dash_extensions.javascript import assign, arrow_function

from app_map.util_layout import get_page_menu

# https://www.dash-leaflet.com/components/vector_layers/polyline
# https://leafletjs.com/examples/geojson/  # style
js_draw_custom = assign("""function(feature) {
        let pct = feature.properties.pct_change;
        let col = "#5a5a5a"; //"#C0C0C0";
        let pctLow = feature.properties.type == "N" ? 0.05 : 0.03;
        if (pct > pctLow){
            col = "#ff0000";
        }
        else if (pct < -pctLow) {
            col = "#00ff00";
        }
        return {color: col};}""")

_html_title_style = {"position": "absolute", "direction": "rtl", "z-index": "999", "right": "0px",
                     "border-radius": "15%", "margin": "0px",
                     "padding": "5px 20px 5px 15px", "background-color": "#FFFFFFB3"}
_html_radio_style = {"position": "absolute", "z-index": "999", "top": "30px", "left": "80px",
                     "font-family": "sans-serif", "background-color": "#FFFFFFB3", "font-size": "1.2em",
                     "padding": "5px 15px 5px 5px", "border-radius": "20%"}


def get_json_layer():
    return dl.GeoJSON(data=None, format='geojson',
                      id="geogson_",
                      hoverStyle=arrow_function(dict(weight=6, dashArray='')),  # yellow # color='#FFFF00',
                      options=dict(style=js_draw_custom),
                      # zoomToBounds=True,
                      zoomToBoundsOnClick=False)


def load_geojson(asset_type, zoom):
    prepath = "resources/"
    zoom_cutoff = 13  # ZOOM => 13 ===> go to neighborhood
    if asset_type == "rent":
        if zoom >= zoom_cutoff:
            file_name = prepath + "changes_last_polygon_rent_city_neighborhood.json"
        else:
            file_name = prepath + "changes_last_polygon_rent_city.json"
    elif asset_type == "forsale":
        if zoom >= zoom_cutoff:
            file_name = prepath + "changes_last_polygon_forsale_city_neighborhood.json"
        else:
            file_name = prepath + "changes_last_polygon_forsale_city.json"
    else:
        return ValueError("Invalid asset_type")
    with open(file_name, "r") as f:
        return json.load(f)


def get_dash(server):
    app = dash.Dash(server=server,
                    external_stylesheets=[dbc.themes.BOOTSTRAP],
                    title="Neighborhood", url_base_pathname='/neighborhood/')

    app.layout = html.Div([
        html.Div([
            get_page_menu(),
            html.H2("שׁינויים במחירי הדירות"),
            html.Small("(רבעון נוכחי מול קודם)"),
            dash.dcc.Checklist(["Y"], ["Y"], id="polygon_toggle")], style=_html_title_style),
        dl.Map([
            dl.TileLayer(),
            get_json_layer()],
            id='big-map',
            style={'width': '100%', 'height': '700px'},
            center=(31.87, 35.00),
            zoom=10,
        ),
        html.Div(id='output_'), dash.dcc.RadioItems(
            [{'label': 'Rent', 'value': 'rent'},
             {'label': 'Sale', 'value': 'forsale'}],
            'rent', id="radio_",
            style=_html_radio_style)])

    # @app.callback(
    #     Output(component_id='output_', component_property='children'),
    #     Input(component_id='map_', component_property='bounds')
    # )
    # def update_output_div(bounds):
    #     return 'Output: {}'.format(bounds)

    @app.callback(
        Output(component_id='geogson_', component_property='data'),
        Input(component_id='radio_', component_property='value'),
        Input("big-map", "zoom"),
        Input("polygon_toggle", "value")
    )
    def change_asset_type(value, zoom, toggle):
        if not len(toggle):
            return None
        return load_geojson(value, zoom)

    return server, app


if __name__ == '__main__':
    _, app = get_dash(True)
    app.run_server(debug=True)
