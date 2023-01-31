#
# # https://lyz-code.github.io/blue-book/coding/python/dash_leaflet/
# https://dash-leaflet-docs.onrender.com/#geojson


#
import dash
import dash_bootstrap_components as dbc
from dash import dcc
import dash_leaflet as dl
import dash_leaflet.express as dlx
from plotly import graph_objects as go
from dash import html, Output, Input, State
import numpy as np
from datetime import datetime
import pandas as pd

from forsale.utils import calc_dist, get_similar_closed_deals, plot_deal_vs_sale_sold

df = pd.read_pickle('/Users/lidorazulay/Documents/DS/realestate/resources/yad2_df.pk')

# df_f = df.query('last_price < 3000000 and -0.9 < price_pct < -0.01 and price_diff < 1e7')  # [:30]
df_f = df.query('last_price < 3000000 and price_diff < 1e7')  # [:30]
df_f = df.sort_values('pct_diff_median').query('group_size > 30 '
                                               'and 2 < rooms < 5'
                                               ' and last_price > 500000'
                                               ' and pct_diff_median < -0.1')[:300]
print(f"loaded {len(df_f)} rows")
# icon="fa-light fa-house", prefix='fa'
deal_points = [dict(deal_id=idx, lat=d['lat'], lon=d['long'], color='black', icon="fa-light fa-house", metadata=d) for
               idx, d in df_f.iterrows()]
import time

geojsonMarkerOptions = {
    # "radius": 8,
    "fillColor": "#ff7800",
    "color": "#000",
    # "weight": 1,
    # "opacity": 1,
    "fillOpacity": 0.8
}


def prifunc(feature, latlng):
    return dl.CircleMarker(latlng, geojsonMarkerOptions)
    # lambda feature, latlng: dl.CircleMarker(latlng,geojsonMarkerOptions))


from dash_extensions.javascript import assign

point_to_layer = assign("function(feature, latlng, context) {console.log(feature); return L.marker(latlng, {fillColor: '#ff7800'});}")

# time.sleep(1)
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
deal_points = dlx.dicts_to_geojson(
    [{**deal, **dict(
        tooltip=f"{deal['deal_id']} </br> {deal['metadata']['last_price']:,.0f} </br> {deal['metadata']['pct_diff_median']:0.2%}")}
     for deal in deal_points])
deal_points['properties'] = {"marker-color": "RED"}
app.layout = html.Div(children=[
    html.Div(className="flex-container", children=[
        html.Div(className="left-div", children=[
            dl.Map(children=[dl.TileLayer(),

                             # dl.LayerGroup(id="layer"),
                             # dl.LayerGroup(id="layer1"),

                             dl.GeoJSON(data=deal_points, id="geojson", zoomToBounds=True, cluster=False,
                                        # superClusterOptions=dict(radius=50, maxZoom=12),
                                        # pointToLayer=prifunc,
                                        # hideout=dict(pointToLayer=prifunc),
                                        options=dict(pointToLayer=point_to_layer), # , style={"color": "yellow"}
                                        # options={"style": {"color": "yellow"}}
                                        ),

                             # dl.GeoJSON(
                             #     url='https://pkgstore.datahub.io/core/geo-countries/countries/archive/23f420f929e0e09c39d916b8aaa166fb/countries.geojson',
                             #     id="countries",
                             #     options=dict(style=dict(opacity=0, fillOpacity=0)))  # ,
                             # hoverStyle=dict(weight=2, color='red', dashArray='', opacity=1))
                             ],

                   style={'width': '100%', 'height': '800px'},
                   zoom=3, id='map'),
        ]),

        dbc.Offcanvas(
            [
                # dbc.ModalHeader(dbc.ModalTitle("Header")),
                dbc.ModalBody(children=[html.Div(children=[html.Div(id='country'), html.Div(id='marker'),
                                                           dcc.Graph(id='histogram', figure={}),
                                                           html.Div(id='Country info pane')])]),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ms-auto", n_clicks=0)
                ),
            ],
            id="modal",
            placement="end",
            is_open=False,
            style=dict(width="500px", direction="rtl")
        ),
        # html.Div(id="right-div-cont", className="right-div", children=[
        #     html.Div(children=[html.Div(id='country'), html.Div(id='marker'),
        #                        dcc.Graph(id='histogram', figure={}),
        #
        #                        html.Div(id='Country info pane')])
        # ])

    ]),
])


# @app.callback(Output('geojson', 'data'), Input("geojson", "click_feature"))
# def load_points(input):
#     return deal_points


def plot_deal_vs_sale_sold(other_close_deals, df_tax, deal, round_rooms=True):
    # When the hist becomes square thats because there a huge anomaly in terms of extreme value
    if round_rooms:
        other_close_deals = other_close_deals.dropna(subset='rooms')
        sale_items = \
            other_close_deals[other_close_deals['rooms'].astype(float).astype(int) == int(float(deal['rooms']))][
                'last_price']
    else:
        sale_items = other_close_deals[other_close_deals['rooms'] == deal['rooms']]['last_price']
    sale_items = sale_items.rename(
        f'last_price #{len(sale_items)}')  # .hist(bins=min(70, len(sale_items)), legend=True, alpha=0.8)
    fig = go.Figure()
    tr_1 = go.Histogram(x=sale_items, name=sale_items.name, opacity=0.75, nbinsx=len(sale_items))
    fig.add_trace(tr_1)
    sold_items = df_tax['mcirMorach']
    days_back = df_tax.attrs['days_back']
    if len(sold_items):
        sold_items = sold_items.rename(
            f'realPrice{days_back}D #{len(sold_items)}')  # .hist(bins=min(70, len(sold_items)), legend=True,alpha=0.8)
        tr_2 = go.Histogram(x=sold_items, name=sold_items.name, opacity=0.75, nbinsx=len(sold_items))
        fig.add_trace(tr_2)
    fig.add_vline(x=deal['last_price'], line_width=2, line_color='red', name=f"{deal['last_price']:,.0f}")
    # plt.axvline(deal['last_price'], color='red', label=f"{deal['last_price']:,.0f}", linewidth=2)
    fig.update_layout(  # title_text=str_txt,
        barmode='stack',
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(x=0.0, y=1))
    fig.update_xaxes(range=[deal['last_price'] // 2, deal['last_price'] * 3])
    return fig
    # plt.legend()


def get_similar_deals(deal, days_back=99, dist_km=1):
    # https://plotly.com/python/histograms/
    # deal = df.loc[deal_id]
    other_close_deals = calc_dist(df, deal, dist_km)  # .join(df)
    df_tax = get_similar_closed_deals(deal, days_back, dist_km, True)
    # display(df_tax)
    fig = plot_deal_vs_sale_sold(other_close_deals, df_tax, deal)
    # from IPython.display import display, HTML
    maps_url = f"http://maps.google.com/maps?z=12&t=m&q=loc:{deal['lat']}+{deal['long']}&hl=iw"  # ?hl=iw, t=k sattalite
    print(deal['info_text'])

    days_online = (datetime.today() - pd.to_datetime(deal['date_added'])).days
    # str_txt = f"{'חדרים'} {deal['rooms']},{deal['type']}, {deal['street']}, {deal['city']}, {deal['price_pct']:0.2%}, {days_online} days"
    str_txt = f"<h1>{deal['last_price']:,.0f}</h1>, {deal['city']}, {days_online}"
    txt_html = html.Div([html.H3(f"{deal['last_price']:,.0f} ₪"),
                         html.P([f" {deal['rooms']} חדרים",
                                 html.Br(),
                                 f"{deal['type']}, {deal['city']}, {deal['street']}",
                                 html.Br(),
                                 f"{deal['square_meters']:,.0f} מטר",
                                 html.Br(),
                                 html.Span(
                                     [html.A(href=f"https://www.yad2.co.il/item/{deal.name}", children="LINK TO DIRA!!",
                                             target="_blank"),
                                      html.A(href=maps_url, children="  LINK TO DIRA IN MAPS", target="_blank")])
                                 ]),
                         html.Span(f"{deal['info_text']}", style={"font-size": "0.7vw"}),
                         ])
    return txt_html, fig
    # display(df_tax.sort_values('mcirMozhar'))
    # display(other_close_deals[other_close_deals['rooms'].astype(float).astype(int) == int(float(deal['rooms']))].dropna(
    #     subset='price_pct').sort_values('last_price'))


# # show graph only when ready to display, to avoid blank white figure
# @app.callback(Output('histogram', 'style'),
#               Input('histogram', 'figure'))
# def show_graph_when_loaded(figure):
#     if figure is None or figure == {}:
#         return {'display': 'None'}
#     else:
#         return None


# https://python.plainenglish.io/how-to-create-a-model-window-in-dash-4ab1c8e234d3

@app.callback(
    [Output("modal", "is_open"), Output("marker", "children"), Output("histogram", "figure")],
    [Input("geojson", "click_feature"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(feature, n2, is_open):
    if feature or n2:
        props = feature['properties']
        print("marker clicked!")
        if 'deal_id' in props:
            deal_id = feature['properties']['deal_id']
            deal = df.loc[deal_id]
            str_html, fig = get_similar_deals(deal)
            # print(link, days_online)
            return not is_open, str_html, fig
    return is_open, None, {}


# @app.callback(Output("marker", "children"), Output("histogram", "figure"), Output('histogram', 'style'), Input("geojson", "click_feature"))
# def map_marker_click(feature):
#     if feature is not None:
#         props = feature['properties']
#         print("marker clicked!")
#         if 'deal_id' in props:
#             deal_id = feature['properties']['deal_id']
#             deal = df.loc[deal_id]
#             str_html, fig = get_similar_deals(deal)
#             # print(link, days_online)
#             return str_html, fig, None
#     return None, {}, {'display': 'None'}


# @app.callback(Output("layer", "children"), Input("countries", "click_feature"))
# def map_click(feature):
#     if feature is not None:
#         print('invoked')
#         return [dl.Marker(position=[np.random.randint(-90, 90), np.random.randint(-185, 185)])]
#
#
# @app.callback(Output('Country info pane', 'children'),
#               Input('countries', 'hover_feature'))
# def country_hover(feature):
#     if feature is not None:
#         country_id = feature['properties']['ISO_A3']
#         return country_id
#
#
# @app.callback(Output('layer1', 'children'),
#               Input('countries', 'hover_feature'))
# def country_hover(feature):
#     if feature is not None:
#         return dl.Polygon(positions=[[30, 40], [50, 60]], color='#ff002d', opacity=0.2)


if __name__ == '__main__':
    app.run_server(debug=True)
