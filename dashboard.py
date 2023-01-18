import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime
import sys
import folium
from pyproj import Transformer

trans_itm_to_wgs84 = Transformer.from_crs(2039, 4326)
import pandas as pd
import sqlite3


# GEO PANDAS HAS BETTER INTEGRATION WITH DASH
# https://plotly.com/python/scattermapbox/?_ga=2.136324342.718238851.1672097943-81810637.1672097941

def preprocess_df(df):
    df['tarIska'] = pd.to_datetime(df['tarIska'], format='%Y%m%d')
    df = df[df['tarIska'] >= pd.to_datetime('2010-01-01')]
    df = df.set_index('tarIska')
    df['helekNimkar'] = df['helekNimkar'].astype(float)
    df = df[df['helekNimkar'] == 1.0]
    return df


con = sqlite3.connect("nadlan.db", check_same_thread=False)
df = pd.read_sql("select * from trans", con=con)
df = preprocess_df(df)
print(len(df))
central_cities = ['רמת גן',
                  'ראשון לציון',
                  'תל אביב -יפו',
                  'גבעתיים',
                  'בת ים',
                  'חולון',
                  'רמת השרון',
                  'הרצלייה', ]
color_rooms = {1: 'black', 2: 'gray', 3: 'green', 4: 'cadetblue', 5: 'darkpurple', 6: 'red'}
df_s = df.sample(500)

live_update = True
title = 'Nadlan'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])
server = app.server  # needed for deployment
app.title = title

coins = ["a", "b"]
title_html = html.H4(title, style={'paddingRight': '5%', 'marginLeft': '2%'})
coin_html = dcc.Dropdown(coins, 'BTC', id='coin-type', clearable=False, style=dict(width='60pt'))
live_update_html = html.Div(id='live-update-text', style={'margin': 'auto'}, children="")  # 'width': '20%',
# resample_selector_html = dcc.RadioItems(options=resample_radio_options, value=resample_keywords[2], id='resample-type',
#                                         inline=True)
# https://dash-bootstrap-components.opensource.faculty.ai/docs/components/input/ # RadioItems and Checklist
right_portion_html = html.Div(id='right-portion',
                              children=[  # html.Div(resample_selector_html),
                                  html.Div(id='live-switch-update-container',  # , style={'padding-left': '3%'}
                                           children=[dbc.Switch(id='show-legend', label='Legend ', value=True),
                                                     dbc.Switch(id="live-update-button", label="Live Update",
                                                                value=live_update),
                                                     html.Button("Refresh", id="refresh"),
                                                     html.Div(dcc.Dropdown(['DEALS', 'HEATMAP', 'THEATMAP'], 'DEALS',
                                                                           id='map-dropdown', clearable=False),
                                                              style={"width": "30%"}),
                                                     live_update_html],
                                           style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap',
                                                  'boxSizing': 'borderBox', 'columnGap': '7%'})],
                              )
from datetime import date

app.layout = html.Div([
    html.Div(children=[
        title_html,
        coin_html,
        html.Div(dcc.RangeSlider(1, 6, 1, value=[3, 5], id='my-range-slider'), style={"width": "30%"}),

        dcc.DatePickerRange(
            id='my-date-picker-range',
            start_date_placeholder_text=date(2022, 1, 1),
            end_date_placeholder_text=datetime.today().date() - pd.to_timedelta('30D'),
            initial_visible_month=date(2022, 1, 1),
            display_format='D-M-Y',  # -Q
            # calendar_orientation='vertical',
        ),
        # dcc.Input(
        #     id="input-lookahead",
        #     type="number",
        #     value=14,
        #     placeholder="lookahead",
        #     style=dict(width='30pt')),
        # live_update_html,
        right_portion_html],
        style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'},
    ),
    html.Div(id='graph-container', children=[
        # TODO: fix here height of getting to bottom
        html.Iframe(id='map', srcDoc=None, width='100%', height='100%', hidden=False),
        #           # TODO important https://stackoverflow.com/questions/46287189/how-can-i-change-the-size-of-my-dash-graph
        #           ),
        # https://stackoverflow.com/questions/68188107/how-to-add-create-a-custom-loader-with-dash-plotly
        dcc.Loading(
            id="loading-2",
            children=[html.Div([html.Div(id="loading-output-2")])],
            type="circle",
            loading_state={}
        ),
        # dcc.Interval(id='interval-component', interval=INTERVAL_UPDATE_SECONDS * 1000, n_intervals=0,
        #              disabled=not live_update)
    ], style=dict(height='100vh'))  #
])


#
# @app.callback(
#     Output('interval-component', 'disabled'),
#     Output('interval-component', 'n_intervals'),
#     Input('live-update-button', 'value'),
#     Input('coin-type', 'value'),
#     Input('resample-type', 'value'),
#     Input('input-lookahead', 'value')
# )
# def start_stop_interval(value, _1, _2, _3):
#     is_on = value
#     disabled = not is_on
#     return disabled, 0
#
#
# # show graph only when ready to display, to avoid blank white figure
# @app.callback(Output('graph-container', 'style'),
#               Input('live-update-graph', 'figure'))
# def show_graph_when_loaded(figure):
#     if figure is None:
#         return {'display': 'None'}
#     else:
#         return None
#
#
# def _adjust_input_lookahead(input_lookahead):
#     if input_lookahead is None:
#         input_lookahead = 14
#     return max(min(input_lookahead, 100), 3)
#
#
# def create_text(coin, df_ohlcv):
#     db_dt = pd.to_datetime(df_ohlcv.attrs['curr_ts_db'], unit='s', utc=True).tz_convert('Israel')
#     db_dt = db_dt + pd.to_timedelta('1min')
#     last_value = df_ohlcv.iloc[-1]['close']
#     time_conv = "%b %d, %H:%M"  # .strftime
#     text = [html.Span('{} | {}  {}'.format(db_dt.strftime(time_conv), coin, last_value))]  # {0:.2f}
#     return text
#
# @app.callback(Output('live-update-graph', 'figure'),
#               Output('live-update-text', 'children'),
#               Input('interval-component', 'n_intervals'),
#               Input('coin-type', 'value'),
#               Input('resample-type', 'value'),
#               Input('input-lookahead', 'value'),
#               Input('show-legend', 'value'), )


def get_deals(slider, start_date, end_date):
    m = folium.Map(location=[*trans_itm_to_wgs84.transform(185118, 666233)], zoom_start=8)
    len_df = 0
    if start_date is not None and end_date is not None:
        df_s = pd.read_sql(f"SELECT * FROM trans where tarIska between {pd.to_datetime(start_date).strftime('%Y%m%d')}"
                           f" and {pd.to_datetime(end_date).strftime('%Y%m%d')}"
                           f" and misHadarim between {slider[0]} and {slider[1]}", con)
        len_df = len(df_s)
        df_s = df_s.sample(100) if len_df > 100 else df_s
    else:
        df_s = df.sample(100)
        len_df = len(df_s)
    for idx, row in df_s.iterrows():
        if row['corX'] == 0 and row['corY'] == 0:
            continue
        # dt = str(pd.to_datetime(row['tarIska'], format='%Y%m%d').date())
        dt = idx
        price_mr_net = row['mcirMozhar'] / row['shetachNeto'] if row['shetachNeto'] > 0 else -1
        price_mr_bruto = row['mcirMozhar'] / row['shetachBruto'] if row['shetachBruto'] > 0 else -1
        tooltip = f"{row['ezor']}<br>{dt}<br>{row['yeshuv']}, {row['rechov']}, {row['bayit']}<br>{row['shnatBniya']} {row['misHadarim']} חדרים<br>{row['mcirMozhar']:0,.0f}, {price_mr_net:0,.0f}"
        #     print(row['misHadarim'])
        folium.Marker([*trans_itm_to_wgs84.transform(row['corX'], row['corY'])],
                      popup=tooltip,
                      tooltip=tooltip,
                      # https://fontawesome.com/icons?d=gallery
                      icon=folium.Icon(color=color_rooms[min(int(row['misHadarim']), 6)],
                                       icon="fa-light fa-house", prefix='fa')
                      ).add_to(m)
    m.save("mymapnew.html")
    text = [html.Span('{}'.format(len_df))]  # {0:.2f}
    return open('mymapnew.html', 'r', encoding="utf8").read(), text


def get_heatmap(start_date, end_date):
    from folium.plugins import HeatMap
    m = folium.Map(location=[*trans_itm_to_wgs84.transform(185118, 666233)], zoom_start=8)
    df_s = df[(df.index >= start_date) & (df.index < end_date)]
    heat_data = [[*trans_itm_to_wgs84.transform(row['corX'], row['corY'])] for index, row in df_s.iterrows()]
    # Plot it on the map
    HeatMap(heat_data).add_to(m)
    m.save("mymapnew.html")
    return open('mymapnew.html', 'r', encoding="utf8").read(), ""


def get_heatmap_time():
    print('get_heatmap_time')
    from folium.plugins import HeatMapWithTime
    head_data = []
    timestamps = []
    for g_name, df_g in df.resample('M'):
        points = [[*trans_itm_to_wgs84.transform(row['corX'], row['corY']), 0.1] for index, row in df_g.iterrows()]
        head_data.append(points)
        timestamps.append(str(g_name.date()))
    m = folium.Map(location=[*trans_itm_to_wgs84.transform(185118, 666233)], zoom_start=8)
    hm = HeatMapWithTime(head_data, index=timestamps, auto_play=True, scale_radius=False, position="topright")
    hm.add_to(m)
    m.save("mymapnew.html")
    return open('mymapnew.html', 'r', encoding="utf8").read(), ""


@app.callback(Output('map', 'srcDoc'),
              Output('live-update-text', 'children'),
              Input('my-range-slider', 'value'),
              Input('my-date-picker-range', 'start_date'),
              Input('my-date-picker-range', 'end_date'),
              Input('map-dropdown', 'value'))
def update_graph_live(slider, start_date: date, end_date, map_dropdown):
    if map_dropdown == "DEALS":
        data, text = get_deals(slider, start_date, end_date)
    elif map_dropdown == "HEATMAP":
        data, text = get_heatmap(start_date, end_date)
    elif map_dropdown == "THEATMAP":
        data, text = get_heatmap_time()
    else:
        raise ValueError
    return data, text
    # return m
    # t0 = datetime.now()
    # print(n, coin, resample, input_lookahead)
    # start_ts = int((datetime.utcnow() - INTERVAL_CANDLE_LOOKBACK_TABLE[resample]).timestamp())
    # df_ohlcv = get_candles_from_db(db, coin, resample, start_ts=start_ts)
    # # df_ohlcv = get_candles_from_ccxt(coin, '1D')
    # fig = get_updated_fig(df_ohlcv, xy_limit=True, show_legend=show_legend)
    #
    # t1 = (datetime.now() - t0).total_seconds()
    # print(f'ready at:{round(t1, 2)}sec')
    # text = create_text(coin, df_ohlcv)
    # return fig, text


if __name__ == '__main__':

    args = sys.argv[1:]
    print('args:', args)
    if len(args) == 2 and args[0] == '-port':
        app.run_server(port=args[1], host='0.0.0.0')
    else:
        app.run_server(debug=True)
    # https://dash.plotly.com/live-updates
    # live-updates keep the plot intact:
    # https://stackoverflow.com/questions/63876187/plotly-dash-how-to-show-the-same-selected-area-of-a-figure-between-callbacks

    # app.run_server(debug=True, port=80, host='0.0.0.0' )
# Used in dash to update dashboard, too complicated and does not work well, keep here until i removed this.
# my_state = {}
# def no_update_using_state(coin, resample, show_legend, input_lookahead, state_txt):
#     t0 = datetime.now()
#     if 3 < t0.second < 8 and len(my_state) > 0 and len(state_txt) > 0:
#         # print('is going to sleep?')
#         curr_state = dict(coin=coin, resample=resample, show_legend=show_legend, input_lookahead=input_lookahead)
#         print(curr_state, my_state)
#         if curr_state.items() == my_state.items():
#             print('Yes')
#             return True
#     my_state['coin'] = coin
#     my_state['resample'] = resample
#     my_state['show_legend'] = show_legend
#     my_state['input_lookahead'] = input_lookahead
#     print('Updating...')
#     return False

# if no_update_using_state(coin, resample, show_legend, input_lookahead, state_txt):
#     return dash.no_update, dash.no_update
