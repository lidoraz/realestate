#
# # https://lyz-code.github.io/blue-book/coding/python/dash_leaflet/
# https://dash-leaflet-docs.onrender.com/#geojson

import time
import dash
import dash_bootstrap_components as dbc
from dash import dcc
import dash_leaflet as dl
import dash_leaflet.express as dlx
from plotly import graph_objects as go
from dash import html, Output, Input, State, ctx
import numpy as np
from datetime import datetime
import pandas as pd

from app_map.utils import create_tooltip, get_icon, js_draw_icon, build_sidebar
from forsale.utils import calc_dist, get_similar_closed_deals  # , plot_deal_vs_sale_sold

df_all = pd.read_pickle('/Users/lidorazulay/Documents/DS/realestate/resources/yad2_df.pk')
# TODO: df_all.query("last_price > 500000 and square_meters < 200 and status == 'משופץ'").sort_values('avg_price_m'), can create a nice view for sorting by avg_price per meter.
df_all['avg_price_m'] = df_all['last_price'] / df_all['square_meters']
df_all['date_added'] = pd.to_datetime(df_all['date_added'])
df_all['date_added_d'] = (datetime.today() - df_all['date_added']).dt.days
df_all['updated_at'] = pd.to_datetime(df_all['updated_at'])
df_all['updated_at_d'] = (datetime.today() - df_all['updated_at']).dt.days
# df_f = df.query('last_price < 3000000 and -0.9 < price_pct < -0.01 and price_diff < 1e7')  # [:30]
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])


# def get_asset_points(price_from=500_000, price_to=3_000_000, median_price_pct=-0.1, date_added_days=100,
#                      rooms_range=(3, 4), with_agency=True, state_asset=()):
def get_asset_points(price_from=None, price_to=None, median_price_pct=None, discount_price_pct=None,
                     date_added_days=None, updated_at=None,
                     rooms_range=(None, None), with_agency=True, state_asset=(), map_bounds=None, is_median=True,
                     limit=False):
    if len(state_asset) > 0:
        states = ','.join([f"'{x}'" for x in state_asset])
        sql_state_asset = f' and status in ({states})'
    else:
        sql_state_asset = ""
    rooms_from = rooms_range[0] or 1
    rooms_to = rooms_range[1] or 100
    sql_cond = dict(
        sql_rooms_range=f"{rooms_from} <= rooms <= {rooms_to}.5" if rooms_from is not None and rooms_to is not None else "",
        sql_price_from=f"and {price_from} <= last_price" if price_from is not None else "",
        sql_price_to=f"and {price_to} >= last_price" if price_to is not None else "",
        sql_is_agency="and is_agency == False" if not with_agency else "",
        sql_state_asset=sql_state_asset,
        sql_median_price_pct=f"and group_size > 30 and pct_diff_median <= {median_price_pct}" if median_price_pct is not None else "",
        sql_discount_pct=f"and -0.90 <= price_pct <= {discount_price_pct}" if discount_price_pct is not None else "",
        sql_map_bounds=f"and {map_bounds[0][0]} < lat < {map_bounds[1][0]} and {map_bounds[0][1]} < long < {map_bounds[1][1]}" if map_bounds else "",
        sql_date_added=f"and date_added_d <= {date_added_days}" if date_added_days else "",
        sql_updated_at=f"and updated_at_d <= {updated_at}" if updated_at else "")
    q = ' '.join(list(sql_cond.values()))
    print(q)
    df_f = df_all.query(q)
    if limit:
        df_f = df_f[:10_000]
    print(f"Triggerd, Fetched: {len(df_f)} rows")
    return df_f


from_price_txt = 'עד מחיר(מ)'
to_price_txt = 'עד מחיר(מ)'
date_added_txt = 'הועלה עד '
date_updated_text = 'עודכן לפני'
n_rooms_txt = 'מספר חדרים'
median_price_txt = '% מהחציון'
price_pct_txt = 'שינוי במחיר'
rooms_marks = {r: str(r) for r in range(7)}
rooms_marks[6] = '6+'

app.layout = html.Div(children=[
    html.Div(className="flex-container", children=[
        html.Div(className="left-div", children=[
            dl.Map(children=[dl.TileLayer(),
                             dl.GeoJSON(data=None, id="geojson", zoomToBounds=False, cluster=True,
                                        # superClusterOptions=dict(radius=50, maxZoom=12),
                                        options=dict(pointToLayer=js_draw_icon),
                                        ),
                             ],
                   zoom=3, id='map', zoomControl=False,
                   bounds=[[31.7, 32.7], [32.5, 37.3]]
                   ),
            html.Div(children=[
                dbc.Button(children=[html.Span('סה"כ:'), html.Span("0", id="fetched-assets")]),
                html.Span(from_price_txt),
                dcc.Input(
                    id="price-from",
                    type="number",
                    placeholder=from_price_txt,
                    value=0.5,
                    step=0.1,
                    min=0,
                    debounce=True,
                    className='input-ltr'
                ),
                html.Span(to_price_txt),
                dcc.Input(
                    id="price-to",
                    type="number",
                    placeholder=to_price_txt,
                    value=3,
                    step=0.1,
                    min=0,
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
                    step=0.01,
                    min=-1,
                    max=1,
                    className="input-ltr"
                ),
                html.Span(price_pct_txt),
                dcc.Input(
                    id="discount-price-pct",
                    type="number",
                    placeholder=price_pct_txt,
                    value=None,
                    debounce=True,
                    step=0.01,
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
                html.Span(date_updated_text),
                dcc.Input(
                    id="date-updated",
                    type="number",
                    placeholder=date_updated_text,
                    value=30,
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
                html.Span('שיטה'),
                dbc.Switch(value=True, id='switch-median'),
                # dbc.Button(children="AAAAAA"),
                dbc.Button("באיזור", id="button-around"),
                dbc.Button("סנן", id='button-return'),

                dbc.Button(children="נקה", id="button-clear"),
                html.Span(n_rooms_txt),
                html.Div(dcc.RangeSlider(1, 6, 1, value=[3, 4], marks=rooms_marks, id='rooms-slider'),
                         style=dict(width="30em")),
            ], className="top-toolbar")
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


def get_similar_deals(deal, days_back=99, dist_km=1):
    # https://plotly.com/python/histograms/
    # deal = df.loc[deal_id]
    other_close_deals = calc_dist(df_all, deal, dist_km)  # .join(df)
    df_tax = get_similar_closed_deals(deal, days_back, dist_km, True)
    print(f'get_similar_deals: other_close_deals={len(other_close_deals)}, df_tax={len(df_tax)}')
    # display(df_tax)
    fig = plot_deal_vs_sale_sold(other_close_deals, df_tax, deal)
    return fig


@app.callback(
    [Output("price-from", "value"),
     Output("price-to", "value"),
     Output("median-price-pct", "value"),
     Output("date-added", "value"),
     Output("rooms-slider", "value"),
     Output("state-asset", "value"),
     ],
    Input('button-clear', "n_clicks")
)
def clear_filter(n_clicks):
    if n_clicks:
        return None, None, None, None, (1, 6), []
    return dash.no_update


def print_ctx():
    import json
    ctx_msg = json.dumps({
        # 'states': ctx.states,
        'triggered_prop_ids': ctx.triggered_prop_ids,
        'triggered': ctx.triggered,
        'timing_information': ctx.timing_information,
        # 'inputs': ctx.inputs
    }, indent=2)
    print(ctx_msg)


def sleep_bounds(min_sleep_time=1.5):
    is_triggered_by_map_bounds = len(ctx.triggered_prop_ids) == 1 and list(ctx.triggered_prop_ids)[0] == "map.bounds"
    if is_triggered_by_map_bounds:
        trigger_timing = ctx.timing_information
        time_passed_sec = (datetime.now().timestamp() - trigger_timing['__dash_server']['dur'])
        print('time_passed_sec', time_passed_sec)
        if time_passed_sec < min_sleep_time:
            sleep_time = min_sleep_time - time_passed_sec
            print('sleep_time', sleep_time)
            time.sleep(sleep_time)


context = dict(map_zoom=300, zoom_ts=time.time())


@app.callback(
    [Output("geojson", "data"), Output("fetched-assets", "children"), Output("button-around", "n_clicks"),
     Output("button-return", "n_clicks")],
    [Input("price-from", "value"), Input("price-to", "value"), Input("median-price-pct", "value"),
     Input("discount-price-pct", "value"),
     Input("date-added", "value"), Input("date-updated", "value"),
     Input("rooms-slider", "value"), Input('agency-check', "value"),
     Input('state-asset', "value"),
     Input("button-around", "n_clicks"), Input("button-return", "n_clicks"),
     Input('switch-median', 'value')],
    Input('map', 'bounds'), State('map', 'zoom')
)
def show_assets(price_from, price_to, median_price_pct, discount_price_pct, date_added, updated_at,
                rooms_range, with_agency, state_asset, n_clicks_around, n_clicks_return, is_median,
                map_bounds, map_zoom):
    # print_ctx()
    print(locals())
    is_triggered_by_map_bounds = len(ctx.triggered_prop_ids) == 1 and list(ctx.triggered_prop_ids)[0] == "map.bounds"
    if map_zoom != context['map_zoom'] and is_triggered_by_map_bounds:
        print("Zoom changed! - No update")
        context['map_zoom'] = map_zoom
        context['zoom_ts'] = time.time()
        return dash.no_update
    print(ctx.triggered_prop_ids, map_zoom)
    # sleep_bounds()
    if n_clicks_around:
        df_f = get_asset_points(map_bounds=map_bounds, limit=True)
    else:
        price_from = price_from * 1e6 if price_from is not None else None
        price_to = price_to * 1e6 if price_to is not None else None
        with_agency = True if len(with_agency) else False
        df_f = get_asset_points(price_from, price_to, median_price_pct, discount_price_pct, date_added, updated_at,
                                rooms_range,
                                with_agency, map_bounds=map_bounds,
                                state_asset=state_asset, is_median=is_median)
    # Can keep a list of points, if after fetch there was no new, no need to build new points, just keep them to save resources
    deal_points = [dict(deal_id=idx, lat=d['lat'], lon=d['long'], color='black', icon="fa-light fa-house", metadata=d)
                   for
                   idx, d in df_f.iterrows()]
    icon_metric = 'pct_diff_median' if is_median else 'price_pct'
    deal_points = dlx.dicts_to_geojson([{**deal, **dict(tooltip=create_tooltip(deal), icon=get_icon(deal, icon_metric))}
                                        for deal in deal_points])
    return deal_points, len(df_f), None, None


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
            deal = df_all.loc[deal_id]
            str_html = build_sidebar(deal)
            fig = get_similar_deals(deal)
            return not is_open, None, str_html, fig
    return is_open, None, None, {}


if __name__ == '__main__':
    app.run_server(debug=True)
