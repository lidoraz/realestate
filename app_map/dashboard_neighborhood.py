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
js_draw_price_chg = assign("""function(feature) {
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

colors_grad = dict(
    c0="#32671d",
    c1="#3f6e1c",
    c2="#4e761b",
    c3="#617e19",
    c4="#758618",
    c5="#8d8e16",
    c6="#978614",
    c7="#a07911",
    c8="#a9690f",
    c9="#b2560c",
    c10="#bb3f09",
    c11="#c52405",
    c12="#cf0602")

js_draw_price = assign("""function(feature) {{
        let is_rent = "price_50" in feature.properties;
        let p = is_rent ? feature.properties.price_50 : feature.properties.price_meter_50
        if(!is_rent){{
            switch(true) {{
            case (p >= 0 && p < 5000):      col = "{c0}"; break;
            case (p >= 5000 && p < 10000):  col = "{c1}"; break;
            case (p >= 10000 && p < 15000): col = "{c2}"; break;
            case (p >= 15000 && p < 20000): col = "{c3}"; break;
            case (p >= 20000 && p < 25000): col = "{c4}"; break;
            case (p >= 25000 && p < 30000): col = "{c5}"; break;
            case (p >= 30000 && p < 35000): col = "{c6}"; break;
            case (p >= 35000 && p < 40000): col = "{c7}"; break;
            case (p >= 40000 && p < 45000): col = "{c8}"; break;
            case (p >= 45000 && p < 50000): col = "{c9}"; break;
            case (p >= 50000 && p < 55000): col = "{c10}"; break;
            case (p >= 55000 && p < 60000): col = "{c11}"; break;
            default:                        col = "{c12}";
            }}
        }}
        else{{
            switch(true) {{
            case (p >= 0 && p < 2000):      col = "{c0}"; break;
            case (p >= 2000 && p < 3000):   col = "{c1}"; break;
            case (p >= 3000 && p < 4000):   col = "{c2}"; break;
            case (p >= 4000 && p < 5000):   col = "{c3}"; break;
            case (p >= 5000 && p < 6000):   col = "{c4}"; break;
            case (p >= 6000 && p < 7000):   col = "{c5}"; break;
            case (p >= 7000 && p < 8000):   col = "{c6}"; break;
            case (p >= 8000 && p < 9000):   col = "{c7}"; break;
            case (p >= 9000 && p < 10000):  col = "{c8}"; break;
            case (p >= 10000 && p < 11000): col = "{c9}"; break;
            case (p >= 11000 && p < 12000): col = "{c10}"; break;
            case (p >= 12000 && p < 13000): col = "{c11}"; break;
            default:                        col = "{c12}";
            }}
        }}
        return {{color: col}};
        }}
        """.format(**colors_grad))

_html_title_style = {"position": "absolute", "direction": "rtl", "z-index": "999", "right": "0px",
                     "border-radius": "15%", "margin": "0px",
                     "padding": "5px 20px 5px 15px", "background-color": "#FFFFFFB3"}
# "position": "absolute", "z-index": "999",
_html_radio_style = { "top": "30px", "left": "80px",
                     #"font-size": "1.0em",
                     "padding": "5px 15px 5px 5px", "border-radius": "20%"}


def get_json_layer():
    return dl.GeoJSON(data=None, format='geojson',
                      id="geogson_",
                      hoverStyle=arrow_function(dict(weight=6, dashArray='')),  # yellow # color='#FFFF00',
                      options=dict(style=js_draw_price_chg),
                      # zoomToBounds=True,
                      zoomToBoundsOnClick=False)


def load_json(asset_type, zoom, zoom_cutoff=12):
    # ZOOM => 12 ===> go to neighborhood
    prepath = "resources/"
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


def get_points_by(asset_type, zoom, metric):
    assert metric in ("price", "pct_chg")
    assert asset_type in ("forsale", "rent")
    if metric == "price":
        zoom = 1000
    json_points = load_json(asset_type, zoom)
    js_func = js_draw_price if metric == "price" else js_draw_price_chg
    return json_points, js_func


def get_dash(server):
    app = dash.Dash(server=server,
                    external_stylesheets=[dbc.themes.BOOTSTRAP],
                    title="Neighborhood", url_base_pathname='/neighborhood/')

    app.layout = html.Div([
        html.Div([
            get_page_menu(),
            html.H2("מפת המחירים"),
            dash.dcc.RadioItems(
                [{'label': 'שכירות', 'value': 'rent'},
                 {'label': 'מכירה', 'value': 'forsale'}],
                'rent', id="radio-asset_type"),
            html.H5("הצג לפי"),
            dash.dcc.RadioItems(
                [{'label': 'מחיר', 'value': 'price'},
                 {'label': 'שינוי במחיר', 'value': 'pct_chg'}],
                'price', id="radio-metric"),
            html.Sub("(רבעון נוכחי מול קודם)"),
            dash.dcc.Checklist(["Y"], ["Y"], id="polygon_toggle"),

        ], style=_html_title_style),
        dl.Map([
            dl.TileLayer(),
            get_json_layer()],
            id='big-map',
            style={'width': '100%', 'height': '700px'},
            center=(31.87, 35.00),
            zoom=10,
        ),
        html.Div(id='output_'),

    ])

    @app.callback(
        Output(component_id='geogson_', component_property='data'),
        Output("geogson_", "options"),
        Input(component_id='radio-asset_type', component_property='value'),
        Input("big-map", "zoom"),
        Input("polygon_toggle", "value"),
        Input("radio-metric", "value")
    )
    def change_asset_type(asset_type, zoom, poly_toggle, metric_toggle):
        if not len(poly_toggle):
            return None, None
        json_points, js_func = get_points_by(asset_type, zoom, metric_toggle)
        return json_points, dict(style=js_func)

    return server, app


if __name__ == '__main__':
    _, app = get_dash(True)
    app.run_server(debug=True)
