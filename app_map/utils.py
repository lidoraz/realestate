import os

import pandas as pd
from datetime import datetime
import numpy as np
from app_map.marker import get_marker_tooltip, icon_maps, icon_real_estate, get_color, convert_rooms_str
from app_map.util_layout import *
from scrape_yad2.utils import _get_parse_item_add_info
from fetch_data.utils import filter_by_dist, get_nadlan_trans
import logging
import requests

LOGGER = logging.getLogger()

FETCH_LIMIT = 250
PORT = os.getenv("PORT", 8050)
try:
    res = requests.get("http://localhost/")
    PORT = 80
except:
    PORT = 8050


def app_preprocess_df(df_all):
    df_all['pct_diff_median'] = df_all['price'] / df_all['median_price'] - 1
    df_all['ai_price'] = df_all['ai_price'] * (df_all['ai_std_pct'] < 0.15)  # Take only certain AI predictions
    df_all['ai_price_pct'] = df_all['ai_price'].replace(0, np.nan)
    df_all['ai_price_pct'] = df_all['price'] / df_all['ai_price_pct'] - 1
    df_all['square_meters'] = df_all['square_meter_build'].replace(0, np.nan).combine_first(df_all['square_meters'])
    df_all['avg_price_m'] = df_all['price'] / df_all['square_meters']
    df_all['date_added'] = pd.to_datetime(df_all['date_added'])
    df_all['date_added_d'] = (datetime.today() - df_all['date_added']).dt.days
    df_all['date_updated'] = pd.to_datetime(df_all['date_updated'])
    df_all['date_updated_d'] = (datetime.today() - df_all['date_updated']).dt.days

    df_all = preprocess_to_str_deals(df_all)
    df_all = df_all.reset_index()  # to extract id
    # df_f = df.query('price < 3000000 and -0.9 < price_pct < -0.01 and price_diff < 1e7')  # [:30]
    return df_all


# STATS
def preprocess_stats(df):
    import numpy as np
    df['price_meter'] = df['price'] / df['square_meter_build']
    df['price_meter'] = df['price_meter'].replace(np.inf, np.nan)
    df.sort_values('price_meter', ascending=False)
    return df


def preprocess_to_str_deals(df):
    df['rooms_s'] = df['rooms'].apply(lambda m: f"{m if m % 10 == 0 else round(m)}")
    df['price_s'] = df['price'].apply(lambda m: f"₪{format_number(m)}")
    df['ai_price_pct_s'] = df['ai_price_pct'].apply(lambda m: f"{m:0.1%}")
    df['pct_diff_median_s'] = df['pct_diff_median'].apply(lambda m: f"{m:0.1%}")
    df['price_pct_s'] = df['price_pct'].apply(lambda m: f"{m:0.1%}")
    return df


meta_data_cols = ['lat', 'long', 'price', 'price_s', 'asset_status', 'floor', 'square_meters', 'rooms', 'price_pct',
                  'ai_price_pct', 'pct_diff_median']


def get_geojsons(df, marker_metric):
    dff = df[meta_data_cols]
    deal_points = [dict(deal_id=idx, lat=d['lat'], lon=d['long'], metadata=d) for idx, d in dff.iterrows()]
    deal_points = get_marker_tooltip(deal_points, marker_metric)
    return deal_points


def format_number(num):
    def safe_num(num):
        if isinstance(num, str):
            num = float(num)
        return float('{:.3g}'.format(abs(num)))

    num = safe_num(num)
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def _multi_str_filter(multi_choice, col_name):
    sql_state_asset = ""
    if len(multi_choice) > 0:
        states = ','.join(["'{}'".format(x.replace("'", "\\'")) for x in multi_choice])
        sql_state_asset = f'{col_name} in ({states})'
    return sql_state_asset


def find_center(df, search, err_th=0.1):
    dff = df.query(f'id == "{search}"')
    if len(dff):
        r = dff.squeeze()
        return [r['lat'], r['long']]
    dff = df.query(f'(city.str.contains("{search}") or neighborhood.str.contains("{search}"))')
    if dff.empty:
        return None
    if max(dff['lat'].std(), dff['long'].std()) > err_th:
        return None
    lat = dff['lat'].mean()
    long = dff['long'].mean()
    return [lat, long]


def get_asset_points(df_all, price_from=-np.inf, price_to=np.inf, city=None,
                     price_median_pct_range=None, price_discount_pct_range=None, price_ai_pct_range=None,
                     is_price_median_pct_range=False, is_price_discount_pct_range=False, is_price_ai_pct_range=False,
                     date_added_days=None, date_updated=None,
                     rooms_range=(None, None), floor_range=(None, None),
                     with_agency=True, with_parking=None, with_balconies=None,
                     asset_status=(),
                     asset_type=(),
                     map_bounds=None, id_=None):
    if id_ is not None:
        df_f = df_all.query(f'id == "{id_}"')
        return df_f
    sql_asset_status = _multi_str_filter(asset_status, "asset_status")
    sql_asset_type = _multi_str_filter(asset_type, "asset_type")
    rooms_from = rooms_range[0] or 1
    rooms_to = rooms_range[1] or 100
    floor_from = floor_range[0] if floor_range[0] is not None else 0
    floor_to = 9999 if floor_range[1] == 32 else floor_range[1] or 9999

    sql_cond = dict(
        sql_city=f'(city.str.contains("{city}") or neighborhood.str.contains("{city}"))' if city else "",
        sql_rooms_range=f"{rooms_from} <= rooms <= {rooms_to}.5",
        sql_floor_range=f"{floor_from} <= floor <= {floor_to}",
        sql_price=f"{price_from} <= price <= {price_to}",
        sql_is_agency="is_agency == False" if not with_agency else "",
        sql_is_parking="parking > 0" if with_parking else "",
        sql_is_balcony="balconies == True" if with_balconies else "",
        sql_asset_status=sql_asset_status,
        sql_asset_type=sql_asset_type,
        sql_median_price_pct=f"group_size > 30 and {price_median_pct_range[0] / 100}<=pct_diff_median <= {price_median_pct_range[1] / 100}" if is_price_median_pct_range else "",
        sql_discount_pct=f"{price_discount_pct_range[0] / 100} <= price_pct <= {price_discount_pct_range[1] / 100}" if is_price_discount_pct_range else "",
        # sql_median_price_pct=f"and group_size > 30 and pct_diff_median <= {median_price_pct}" if median_price_pct is not None else "",
        # sql_discount_pct=f"and -0.90 <= price_pct <= {discount_price_pct}" if discount_price_pct is not None else "",
        sql_ai_pct=f"{price_ai_pct_range[0] / 100} <= ai_price_pct <= {price_ai_pct_range[1] / 100}" if is_price_ai_pct_range else "",
        sql_map_bounds=f"{map_bounds[0][0]} < lat < {map_bounds[1][0]} and {map_bounds[0][1]} < long < {map_bounds[1][1]}" if map_bounds else "",
        sql_date_added=f"date_added_d <= {date_added_days}" if date_added_days else "",
        sql_date_updated=f"date_updated_d <= {date_updated}" if date_updated else "")
    q = "1==1 and " + ' and '.join(list([v for v in sql_cond.values() if len(v)]))
    LOGGER.info(q)
    df_f = df_all.query(q)

    LOGGER.info(f"{datetime.now()} Triggerd, Fetched: {len(df_f)} rows")
    return df_f


def genereate_plots(deal):
    from datetime import timedelta
    def plot_line(df, x, y, hover_data, color='Blue'):
        fig = px.line(df, x, y, hover_data=hover_data, line_shape='spline')  # labels={'x': 'Month', 'y': 'Prices'}
        # time_back = timedelta(days=7) if x == 'week' else timedelta(days=30)
        fig.add_annotation(x=df[x].iloc[-1], y=df[y].iloc[-1],
                           text=format_number(df[y].iloc[-1]),
                           showarrow=True, ax=-10, ay=30)
        fig.update_layout(
            #     title='Plotly Figure with Traces',
            # yaxis_visible=False,
            # xaxis_visible=False,
            margin=dict(l=1, r=1, t=1, b=1),
            width=450,
            height=250,
            dragmode=False,
            legend=dict(x=0, y=1))
        fig.update_yaxes(rangemode="tozero")
        fig.update_traces(
            line_color=color,
            line_width=2)
        return fig

    def read_preprocess(data, time_col):
        df = pd.DataFrame(data)
        df[time_col] = pd.to_datetime(df[time_col])
        return df

    dist_km = 1.0
    res = requests.post(f"http://localhost:{PORT}/get_data",
                        # backend runs on local, fetches data from remote server #TODO: might need to change port
                        json=dict(lat=deal['lat'], long=deal['long'], dist_km=dist_km)).json()
    if 'error' in res:
        return []
    import plotly.express as px
    print(res.keys())
    df = read_preprocess(res['data_recent'], 'week')
    fig1 = plot_line(df, 'week', 'price', 'cnt')
    df = read_preprocess(res['data_recent_rent'], 'week')
    fig1_ = plot_line(df, 'week', 'price', 'cnt', 'orange')
    df = read_preprocess(res['data_nadlan'], 'month')
    fig2 = plot_line(df, 'month', 'median_avg_meter_price', 'cnt')
    fig3 = plot_line(df, 'month', 'median_price', 'cnt')
    config = {'displayModeBar': False, 'scrollZoom': False}
    return [
        html.Div([
            html.H4("חציון מחירים לאורך זמן בסביבה הקרובה"),
            html.Div([html.H5("בטווח הארוך (מתוך הלמ״ס)"),
                      dcc.Graph(id='g1', figure=fig3, config=config)]),
            html.Div([html.H5("מכירה טווח קצר"),
                      dcc.Graph(id='g2', figure=fig1, config=config), ]),
            html.Div([html.H5("שכירות טווח קצר"),
                      dcc.Graph(id='g2_', figure=fig1_, config=config)]),
            html.Div([html.H5("מכירה מחיר למטר (מתוך הלמ״ס)"),
                      dcc.Graph(id='g3', figure=fig2, config=config)])],
            className="modal-time-graphs")]
    # fig3 = go.Figure([
    #     go.Scatter(x=df['month'], y=df['median_price'], name="Price"),
    #     # go.Scatter(x=df['month'], y=df['old_median_price'], name="OLD_Price"),
    #     # go.Scatter(x=df['month'], y=df['new_median_price'], name="NEW_Price")
    #                   ])


def build_sidebar(deal, fig):
    # THIS NEEDS REWORK - to DBC usage and better design
    maps_url = f"http://maps.google.com/maps?z=12&t=m&q=loc:{deal['lat']}+{deal['long']}&hl=iw"  # ?hl=iw, t=k sattalite
    days_online = (datetime.today() - pd.to_datetime(deal['date_added'])).days
    days_updated = (datetime.today() - pd.to_datetime(deal['date_updated'])).days
    days_str_txt = lambda x: 'היום' if x == 0 else 'אתמול' if x == 1 else f'{x} ימים'
    date_added = pd.to_datetime(deal['date_added'])
    add_info = _get_parse_item_add_info(deal['id'])
    if add_info:
        image_urls = add_info.pop('image_urls')
        image_urls = image_urls if image_urls is not None else []
        info_text = add_info.pop('info_text')
        # add_info_text = [html.Tr(html.Td(f"{k}: {v}")) for k, v in add_info.items()]
    else:
        image_urls = []
        info_text = deal['info_text']
        # add_info_text = None
    df_price_hist = None
    if isinstance(deal['price_hist'], list):
        df_hist = pd.DataFrame([deal['dt_hist'], [f"{x:0,.0f}" for x in deal['price_hist']]])
        df_price_hist = html.Table([html.Tr([html.Td(v) for v in row.values]) for i, row in df_hist.iterrows()],
                                   className="price-diff-table")
    carousel = None
    if len(image_urls):
        carousel = dbc.Carousel(
            items=[{"key": f"{idx + 1}", "src": url, "href": "https://google.com", "img_class_name": "asset-images-img"}
                   for idx, url in
                   enumerate(image_urls)],
            controls=True,
            indicators=True,
            interval=2500,
            ride="carousel",
            # style="sidebar-carousel"
        )

    def get_html_span_pct(pct):
        pct = 0 if np.isnan(pct) else pct
        return html.Span(f"{pct:.1%}", style={"background-color": get_color(pct)}, className="span-color-pct text-ltr")

    title_html = html.Div([html.Span(f"{deal['price']:,.0f}₪"),
                           get_html_span_pct(deal['price_pct'])])
    street = deal['street'] if deal['street'] else deal['neighborhood'] if deal['neighborhood'] else ""
    n_floors_building = round(deal['number_of_floors']) if deal['number_of_floors'] > 0 else None
    n_floors_building_str = f', (מתוך {n_floors_building})' if n_floors_building else ""
    txt_html = html.Div(
        [html.Span(f"מחיר הנכס מהחציון באיזור: "),
         get_html_span_pct(deal['pct_diff_median']),
         html.P([html.Span(f"מחיר הנכס ממודל AI : "),
                 html.Span(f"{deal['ai_price']:,.0f} (±{deal['ai_std_pct']:.1%})", className="text-ltr"),
                 get_html_span_pct(deal['ai_price_pct'])]),
         html.H6(f"הועלה בתאריך {date_added.date()}, (לפני {days_online / 7:0.1f} שבועות)"),
         html.Span(f"מתי עודכן: {deal['date_updated']}, ({days_str_txt(days_updated)})"),
         html.Div(df_price_hist, className='text-ltr'),
         html.Span(),
         html.P([
             'תיווך' if deal['is_agency'] else 'לא תיווך',
             html.Br(),
             f"מצב הנכס: ",
             html.B(deal['asset_status'])]),
         html.P([f" {convert_rooms_str(deal['rooms'])} חדרים,",
                 f" קומה  {round(deal['floor']) if deal['floor'] > 0 else 'קרקע'} ",
                 n_floors_building_str,
                 html.Br(),
                 f"{deal['asset_type']}, {deal['city']}, {street}",
                 html.Br(),
                 html.Span(f"{deal['square_meters']:,.0f} מטר"),
                 html.Span(f"(מחיר למטר ₪{deal['price'] / deal['square_meters']:,.0f})"),
                 html.Br(),
                 f" חנייה: {deal['parking'] if deal['parking'] else 'ללא'} ",
                 html.Br(),
                 f"{'עם מרפסת' if deal['balconies'] else 'ללא מרפסת'}",
                 html.A(href=maps_url, children=html.Img(src=icon_maps, style=dict(width=32, height=32)),
                        target="_blank"),
                 html.A(href=f"https://www.yad2.co.il/item/{deal['id']}",
                        children=html.Img(src=icon_real_estate, style=dict(width=32, height=32)),
                        target="_blank"),
                 ]),
         html.Div(children=[carousel], className="asset-images", style={"display": "block" if image_urls else "none"}),
         html.Span(info_text, className='sidebar-info-text'),
         html.Span(deal['id'], style={"display": "block", "font-size": "8pt"}),
         html.H5("פילוח מס׳ עסקאות עם מספר חדרים זהה בסביבה:", style=dict(display="block", margin="0px 5px 0px")),
         # TODO: Move this graph to the loading too, but a bit problem because it uses massive dataframe, maybe agg it and send it via state to front
         dcc.Graph(id='histogram', figure=fig,
                   config={'displayModeBar': False,
                           'scrollZoom': False}),
         dcc.Loading(children=[html.Div(id="modal-plots-cont")], type='circle', color='blue', fullscreen=False),

         # html.Br(),
         # html.Table(children=add_info_text, style={"font-size": "10pt"}),
         # html.P("\n".join([f"{k}: {v}" for k, v in res_get_add_info(deal.name).items()])),
         ])
    return title_html, txt_html


from plotly import graph_objects as go


def plot_deal_vs_sale_sold(other_close_deals, df_tax, deal):
    sale_items = other_close_deals['price']
    fig = go.Figure()
    # When the hist becomes square thats because there a huge anomaly in terms of extreme value
    max_price_th = sale_items.median() + sale_items.std() * 3
    sale_items = sale_items[sale_items < max_price_th]
    tr_1 = go.Histogram(x=sale_items, name=f'Total #{len(sale_items)}', opacity=0.75, nbinsx=len(sale_items))
    fig.add_trace(tr_1)
    if df_tax is not None:
        sold_items = df_tax['price_declared']
        days_back = df_tax.attrs['days_back']
        if len(sold_items):
            sold_items = sold_items.rename(
                f'realPrice{days_back}D #{len(sold_items)}')  # .hist(bins=min(70, len(sold_items)), legend=True,alpha=0.8)
            tr_2 = go.Histogram(x=sold_items, name=sold_items.name, opacity=0.75, nbinsx=len(sold_items))
            fig.add_trace(tr_2)
    fig.add_vline(x=deal['price'], line_width=2,
                  line_color='red', line_dash='dash',
                  name=f"{deal['price']:,.0f}")
    fig.update_layout(
        xaxis_title="מחיר",
        yaxis_title="# מס עסקאות",
        # title_text=str_txt,
        # barmode='stack',
        width=450,
        height=250,
        margin=dict(l=0, r=0, b=0, t=0.0),
        legend=dict(x=0.0, y=1),
        dragmode=False)
    # fig.update_xaxes(rangemode="tozero")
    return fig


def get_similar_deals(df_all, deal, days_back=99, dist_km=1, with_nadlan=True):
    filter_rooms = True
    df_open_deals = filter_by_dist(df_all, deal, dist_km)
    if filter_rooms:
        df_open_deals = df_open_deals.dropna(subset='rooms')
        df_open_deals = df_open_deals[df_open_deals['rooms'].astype(float).astype(int) == int(float(deal['rooms']))]
    df_tax = None
    if with_nadlan:
        from app_map.api import create_connection
        from app_map.sql_scripts import sql_similar_deals
        conn = create_connection()
        n_months = 6
        q = sql_similar_deals.format(table_name="nadlan_trans", lat=deal['lat'], long=deal['long'],
                                     n_rooms=deal['rooms'], n_months=n_months)
        df_tax = pd.read_sql(q, conn)
        df_tax.attrs['days_back'] = n_months * 30
        # df_tax = get_nadlan_trans(deal, days_back, dist_km, filter_rooms)
    fig = plot_deal_vs_sale_sold(df_open_deals, df_tax, deal)
    return fig


def create_pct_bar(df_agg, col_name):
    median_price = df_agg[col_name]['50%']
    year_5_median = median_price.iloc[-(5 * 12)]
    year_3_median = median_price.iloc[-(3 * 12)]
    year_1_median = median_price.iloc[-12]
    year_6m_median = median_price.iloc[-6]
    curr_price = median_price.iloc[-1]
    prev = np.array([year_5_median, year_3_median, year_1_median, year_6m_median])
    prev = curr_price / prev - 1

    def get_span(name, val):
        if np.isnan(val):
            name = ""
            val = 0
        sign = '+' if val > 0 else ''
        val_str = f"{sign}{val:.2%}" if val != 0 else ""
        color = "red" if val > 0 else "green" if val < 0 else "gray"
        return html.Div(
            [html.Span(name),
             html.Span(val_str,
                       style=dict(color=color, padding="5px 5px 0px"))],
            style={"margin-left": "10px", "gap-left": "10px"})

    return [  # vhtml.Span(":", style={"margin-right": "10px",}),
        get_span("5Y:", prev[0]),
        get_span("3Y:", prev[1]),
        get_span("1Y:", prev[2]),
        get_span("6M:", prev[3])]

#
# def res_get_add_info(item):
#     import requests
#     add_info = None
#     try:
#         res = requests.get('https://gw.yad2.co.il/feed-search-legacy/item?token={}'.format(item))
#         d = res.json()['data']
#         image_urls = d['images_urls']
#         items_v2 = {x['key']: x['value'] for x in d['additional_info_items_v2']}
#         # add_info = dict(parking=d['parking'],
#         #                 balconies=d['balconies'],
#         #                 renovated=items_v2['renovated'],
#         #                 elevator=d['analytics_items']['elevator'],
#         #                 storeroom=d['analytics_items']['storeroom'],
#         #                 number_of_floors=d['analytics_items']['number_of_floors'],
#         #                 shelter=d['analytics_items']['shelter_room'],
#         #                 immediate=d['analytics_items']['immediate'],
#         #                 info_text=d['info_text']
#         #                 )
#         add_info = dict(חנייה=d['parking'],
#                         מרפסות=d['balconies'],
#                         משופץ=items_v2['renovated'],
#                         מעלית=d['analytics_items']['elevator'],
#                         מחסן=d['analytics_items']['storeroom'],
#                         מספר_קומות=d['analytics_items']['number_of_floors'],
#                         מקלט=d['analytics_items']['shelter_room'],
#                         פינוי_מיידי=d['analytics_items']['immediate'],
#                         טקסט_חופשי=d['info_text'],
#                         image_urls=image_urls
#                         )
#     except Exception as e:
#         print("ERROR IN res_get_add_info", e)
#     return add_info
