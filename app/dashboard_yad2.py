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

from forsale.utils import calc_dist, get_similar_closed_deals  # , plot_deal_vs_sale_sold

df = pd.read_pickle('/Users/lidorazulay/Documents/DS/realestate/resources/yad2_df.pk')
df['date_added'] = pd.to_datetime(df['date_added'])
df['date_added_d'] = (datetime.today() - df['date_added']).dt.days
# df_f = df.query('last_price < 3000000 and -0.9 < price_pct < -0.01 and price_diff < 1e7')  # [:30]
# df_f = df.query('last_price < 3000000 and price_diff < 1e7')[:30]

# geojsonMarkerOptions = {
#     # "radius": 8,
#     "fillColor": "#ff7800",
#     "color": "#000",
#     # "weight": 1,
#     # "opacity": 1,
#     "fillOpacity": 0.8
# }
#
#
# def prifunc(feature, latlng):
#     return dl.CircleMarker(latlng, geojsonMarkerOptions)
# lambda feature, latlng: dl.CircleMarker(latlng,geojsonMarkerOptions))


from dash_extensions.javascript import assign

icon_05 = "https://cdn-icons-png.flaticon.com/128/9387/9387262.png"
icon_10 = "https://cdn-icons-png.flaticon.com/128/6912/6912962.png"
icon_20 = "https://cdn-icons-png.flaticon.com/128/6913/6913127.png"
icon_30 = "https://cdn-icons-png.flaticon.com/128/6913/6913198.png"
icon_40 = "https://cdn-icons-png.flaticon.com/128/9556/9556570.png"
icon_50 = "https://cdn-icons-png.flaticon.com/128/5065/5065451.png"
icon_regular = "https://cdn-icons-png.flaticon.com/128/6153/6153497.png"
icon_maps = "https://cdn-icons-png.flaticon.com/128/684/684809.png"
icon_real_estate = "https://cdn-icons-png.flaticon.com/128/602/602275.png"


def get_icon(deal):
    p = deal['metadata']['pct_diff_median']
    if -0.1 < p <= 0.05:
        return icon_05
    elif -0.2 < p <= -0.1:
        return icon_10
    elif -0.3 < p <= -0.2:
        return icon_20
    elif -0.4 < p <= -0.3:
        return icon_30
    elif -0.5 < p <= -0.4:
        return icon_40
    elif p <= -0.5:
        return icon_50
    else:
        return icon_regular


icon1 = "https://cdn-icons-png.flaticon.com/128/447/447031.png"  # "/resources/location-pin.png" # "/Users/lidorazulay/Downloads/location-pin.png"
icon2 = "https://cdn-icons-png.flaticon.com/128/7976/7976202.png"  # "/resources/location.png" # '/Users/lidorazulay/Downloads/location.png'
draw_icon = assign("""function(feature, latlng){
const flag = L.icon({iconUrl: feature.properties.icon, iconSize: [28, 28]});
console.log(feature.properties.icon);
return L.marker(latlng, {icon: flag});
}""")
# point_to_layer = assign(
#     "function(feature, latlng, context) {console.log(feature); return L.marker(latlng, {fillColor: '#ff7800'});}")

# time.sleep(1)
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])


def get_asset_points(price_from=500_000, price_to=3_000_000, median_price_pct=-0.1, date_added_days=100,
                     rooms_range=(3, 4), with_agency=True, state_asset=()):
    if len(state_asset) > 0:
        states = ','.join([f"'{x}'" for x in state_asset])
        sql_state_asset = f' and status in ({states})'
    else:
        sql_state_asset = ""
    median_price_pct = 1 if median_price_pct is None else median_price_pct
    rooms_from = rooms_range[0]
    rooms_to = rooms_range[1]
    rooms_to = 100 if rooms_to == 6 else rooms_to
    sql_is_agency = " and is_agency == False" if not with_agency else ""
    df_f = df.query('group_size > 30 '
                    f'and {rooms_from} <= rooms <= {rooms_to}.5'
                    f' and last_price > {price_from}'
                    f' and last_price < {price_to}'
                    f' and pct_diff_median <= {median_price_pct or 1}'
                    f"and date_added_d < {date_added_days or 1000}" + sql_is_agency + sql_state_asset)  # [:1000]
    print(f"Triggerd, Fetched: {len(df_f)} rows")
    deal_points = [dict(deal_id=idx, lat=d['lat'], lon=d['long'], color='black', icon="fa-light fa-house", metadata=d)
                   for
                   idx, d in df_f.iterrows()]
    deal_points = dlx.dicts_to_geojson(
        [{**deal, **dict(
            tooltip=f"{deal['deal_id']}</br> חדרים {deal['metadata']['rooms']} </br> {deal['metadata']['last_price']:,.0f} </br> {deal['metadata']['pct_diff_median']:0.2%}",
            icon=get_icon(deal))}
         for deal in deal_points])
    return deal_points


from_price_txt = 'עד מחיר(מ)'
to_price_txt = 'עד מחיר(מ)'
date_added_txt = 'הועלה עד (ימים)'
n_rooms_txt = 'מספר חדרים'
median_price_txt = 'מחיר חציוני'
rooms_marks = {r: str(r) for r in range(7)}
rooms_marks[6] = '6+'

app.layout = html.Div(children=[
    html.Div(className="flex-container", children=[
        html.Div(className="left-div", children=[
            html.Span("d"),
            dl.Map(children=[dl.TileLayer(),

                             # dl.LayerGroup(id="layer"),
                             # dl.LayerGroup(id="layer1"),

                             dl.GeoJSON(data=None, id="geojson", zoomToBounds=False, cluster=True,
                                        # superClusterOptions=dict(radius=50, maxZoom=12),
                                        # pointToLayer=prifunc,
                                        # hideout=dict(pointToLayer=prifunc),
                                        options=dict(pointToLayer=draw_icon),  # , style={"color": "yellow"}
                                        # options={"style": {"color": "yellow"}}
                                        ),
                             ],
                   zoom=3, id='map', zoomControl=False,
                   bounds=[[30.96890699680559, 32.753622382879264], [32.93332597831644, 37.367880195379264]]),
            html.Div(children=[
                dbc.Button(children=[html.Span('סה"כ:'), html.Span("0", id="fetched-assets")]),
                html.Span(from_price_txt),
                dcc.Input(
                    id="price-from",
                    type="number",
                    placeholder=from_price_txt,
                    value=0.5,
                    debounce=True,
                    className='input-ltr'
                ),
                html.Span(to_price_txt),
                dcc.Input(
                    id="price-to",
                    type="number",
                    placeholder=to_price_txt,
                    value=3,
                    debounce=True,
                    className='input-ltr'
                ),
                html.Span(median_price_txt),
                dcc.Input(
                    id="median-price-pct",
                    type="number",
                    placeholder=median_price_txt,
                    value=-0.2,
                    debounce=True,
                    min=-1,
                    max=1,
                    className="input-ltr"
                ),
                html.Span(date_added_txt),
                dcc.Input(
                    id="date-added",
                    type="number",
                    placeholder=date_added_txt,
                    value=100,
                    debounce=True,
                    className="input-ltr"
                ),
                dcc.Checklist(options=[{'label': 'כולל תיווך', 'value': 'Y'}], value=['Y'], inline=True,
                              id='agency-check'),
                dcc.Dropdown(
                    ['משופץ', 'במצב שמור', 'חדש (גרו בנכס)', 'חדש מקבלן (לא גרו בנכס)', 'דרוש שיפוץ'],
                    [],
                    placeholder="מצב הנכס",
                    multi=True,
                    searchable=False,
                    id='state-asset',
                    style=dict(width='10em')),
                dbc.Button(children="AAAAAA"),
                dbc.Button(children="BBBBBB"),
                html.Span(n_rooms_txt),
                html.Div(dcc.RangeSlider(1, 6, 1, value=[3, 4], marks=rooms_marks, id='rooms-slider'),
                         style=dict(width="30em"))
                # dcc.Dropdown(
                #     ['New York City', 'Montreal', 'San Francisco'],
                #     ['Montreal', 'San Francisco'],
                #     multi=True
                # )
            ], className="top-toolbar")  # style={"position": "absolute", "z-index": 1000, "top": 0, "margin-right": 1},
        ]),

        dbc.Offcanvas(
            [
                # dbc.ModalHeader(dbc.ModalTitle("Header")),
                dbc.ModalBody(children=[html.Div(children=[html.Div(id='country'), html.Div(id='marker'),
                                                           dcc.Graph(id='histogram', figure={},
                                                                     config={'displayModeBar': False,
                                                                             'scrollZoom': False}),
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
    ]),
])


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
    fig.add_vline(x=deal['last_price'], line_width=2, line_color='red', line_dash='dash',
                  name=f"{deal['last_price']:,.0f}")
    fig.update_layout(  # title_text=str_txt,
        # barmode='stack',
        width=450,
        height=250,
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(x=0.0, y=1),
        dragmode=False)
    # fig['layout']['yaxis'].update(autorange=True)
    # fig['layout']['xaxis'].update(autorange=True)
    fig.update_xaxes(range=[deal['last_price'] // 2, deal['last_price'] * 2.5])
    return fig
    # plt.legend()


def res_get_add_info(item):
    import requests
    add_info = None
    try:
        res = requests.get('https://gw.yad2.co.il/feed-search-legacy/item?token={}'.format(item))
        d = res.json()['data']
        image_urls = d['images_urls']
        items_v2 = {x['key']: x['value'] for x in d['additional_info_items_v2']}
        # add_info = dict(parking=d['parking'],
        #                 balconies=d['balconies'],
        #                 renovated=items_v2['renovated'],
        #                 elevator=d['analytics_items']['elevator'],
        #                 storeroom=d['analytics_items']['storeroom'],
        #                 number_of_floors=d['analytics_items']['number_of_floors'],
        #                 shelter=d['analytics_items']['shelter_room'],
        #                 immediate=d['analytics_items']['immediate'],
        #                 info_text=d['info_text']
        #                 )
        add_info = dict(חנייה=d['parking'],
                        מרפסות=d['balconies'],
                        משופץ=items_v2['renovated'],
                        מעלית=d['analytics_items']['elevator'],
                        מחסן=d['analytics_items']['storeroom'],
                        מספר_קומות=d['analytics_items']['number_of_floors'],
                        מקלט=d['analytics_items']['shelter_room'],
                        פינוי_מיידי=d['analytics_items']['immediate'],
                        טקסט_חופשי=d['info_text'],
                        image_urls=image_urls
                        )
    except Exception as e:
        print("ERROR IN res_get_add_info", e)
    return add_info


def get_similar_deals(deal, days_back=99, dist_km=1):
    # https://plotly.com/python/histograms/
    # deal = df.loc[deal_id]
    other_close_deals = calc_dist(df, deal, dist_km)  # .join(df)
    df_tax = get_similar_closed_deals(deal, days_back, dist_km, True)
    print(f'get_similar_deals: other_close_deals={len(other_close_deals)}, df_tax={len(df_tax)}')
    # display(df_tax)
    fig = plot_deal_vs_sale_sold(other_close_deals, df_tax, deal)
    maps_url = f"http://maps.google.com/maps?z=12&t=m&q=loc:{deal['lat']}+{deal['long']}&hl=iw"  # ?hl=iw, t=k sattalite
    days_online = (datetime.today() - pd.to_datetime(deal['date_added'])).days
    date_added = pd.to_datetime(deal['date_added'])

    add_info = res_get_add_info(deal.name)
    image_urls = add_info.pop('image_urls') or []
    info_text = add_info.pop('טקסט_חופשי')
    info_text = info_text if info_text is not None else deal['info_text']
    add_info_text = [html.Tr(html.Td(f"{k}: {v}")) for k, v in add_info.items() if
                     k not in ('image_urls', 'טקסט_חופשי')] if add_info is not None else []
    pct = deal['price_pct']
    str_price_pct = html.Span(f" ({pct:.2%})" if pct != 0 else "",
                              style={"color": "green" if pct < 0 else "red"})
    txt_html = html.Div(
        [html.Div([html.Span(f"{deal['last_price']:,.0f}₪", style={"font-size": "1.5vw"}),
                   html.Span(str_price_pct, className="text-ltr")]),
         html.Span(f"מחיר הנכס מהחציון באיזור: "),
         html.Span(f"{deal['pct_diff_median']:0.2%}", className="text-ltr"),
         html.H6(f"הועלה בתאריך {date_added.date()}, (לפני {(datetime.today() - date_added).days / 7:0.1f} שבועות)"),
         html.Span('תיווך' if deal['is_agency'] else 'לא תיווך'),
         html.P([f" {deal['rooms']} חדרים",
                 html.Br(),
                 f"{deal['type']}, {deal['city']},{deal['street']}",
                 html.Br(),
                 f"{deal['square_meters']:,.0f} מטר",

                 html.A(href=maps_url, children=html.Img(src=icon_maps, style=dict(width=32, height=32)),
                        target="_blank"),
                 html.A(href=f"https://www.yad2.co.il/item/{deal.name}",
                        children=html.Img(src=icon_real_estate, style=dict(width=32, height=32)),
                        target="_blank"),
                 ]),
         html.Div(children=[html.Img(src=src, style=dict(width="40%", height="40%")) for src in image_urls[:3]],
                  className="asset-images"),
         # html.Br(),
         html.Table(children=add_info_text, style={"font-size": "0.8vw"}),
         # html.P("\n".join([f"{k}: {v}" for k, v in res_get_add_info(deal.name).items()])),
         html.Span(info_text, style={"font-size": "0.7vw"}),
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


@app.callback(
    [Output("geojson", "data"), Output("fetched-assets", "children")],
    [Input("price-from", "value"), Input("price-to", "value"), Input("median-price-pct", "value"),
     Input("date-added", "value"), Input("rooms-slider", "value"), Input('agency-check', "value"),
     Input('state-asset', "value")],
    State('map', 'bounds')
)
def show_assets(price_from, price_to, median_price_pct, date_added, rooms_range, with_agency, state_asset, map_bounds):
    print(locals())
    price_from = price_from * 1e6 if price_from is not None else 0
    price_to = price_to * 1e6 if price_to is not None else 1e30
    with_agency = True if len(with_agency) else False
    print(with_agency)
    points = get_asset_points(price_from, price_to, median_price_pct, date_added, rooms_range, with_agency, state_asset)
    return points, len(points['features'])


# https://python.plainenglish.io/how-to-create-a-model-window-in-dash-4ab1c8e234d3

@app.callback(
    [Output("modal", "is_open"), Output("geojson", "click_feature"),
     Output("marker", "children"), Output("histogram", "figure")],
    [Input("geojson", "click_feature"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(feature, n2, is_open):
    print(f'toggle_modal', n2, is_open)
    if feature or n2:
        props = feature['properties']
        if 'deal_id' in props:
            deal_id = feature['properties']['deal_id']
            deal = df.loc[deal_id]
            str_html, fig = get_similar_deals(deal)
            # print(link, days_online)
            return not is_open, None, str_html, fig
    return is_open, None, None, {}


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
