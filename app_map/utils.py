import os
import time

import pandas as pd
from datetime import datetime
import numpy as np
from app_map.marker import get_marker_tooltip, icon_maps, icon_real_estate, get_color
from app_map.util_layout import *
from scrape_yad2.utils import _get_parse_item_add_info
from fetch_data.utils import filter_by_dist, get_nadlan_trans

FETCH_LIMIT = 500


def get_df_with_prod(is_prod, filename):
    s3_file = "https://real-estate-public.s3.eu-west-2.amazonaws.com/resources/{filename}"
    pre_path = f"resources/"
    if not is_prod:
        pre_path = "../" + pre_path
    path_file = pre_path + filename
    should_update = True
    if os.path.exists(path_file):
        time_modified = os.path.getmtime(path_file)
        if (time.time() - time_modified) < (3600 * 24):
            should_update = False
    # should_update=True
    if should_update:
        print(f"{datetime.now()}, Downloading file")
        from smart_open import open
        # TODO Add here access only to auth users, something with bucket is not correct
        # import boto3
        # session = boto3.Session(
        #     aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        #     aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
        # s3_file_name = "s3://real-estate-public/resources/yad2_rent_df.pk"
        nadlan_path = pre_path + "df_nadlan_recent.pk"
        with open(s3_file.format(filename="df_nadlan_recent.pk"), 'rb') as f:
            pd.read_pickle(f).to_pickle(nadlan_path)
        with open(s3_file.format(filename=filename), 'rb') as f:
            df_all = pd.read_pickle(f)
            df_all.to_pickle(path_file)
        print(f"{datetime.now()}, Downloaded files")
    else:
        print(f"{datetime.now()} loading from FS file")
        df_all = pd.read_pickle(path_file)
    return df_all


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


def preprocess_to_str_deals(df):
    df['rooms_s'] = df['rooms'].apply(lambda m: f"{m if m % 10 == 0 else round(m)}")
    df['price_s'] = df['price'].apply(lambda m: f"₪{format_number(m)}")
    df['ai_price_pct_s'] = df['ai_price_pct'].apply(lambda m: f"{m:0.1%}")
    df['pct_diff_median_s'] = df['pct_diff_median'].apply(lambda m: f"{m:0.1%}")
    df['price_pct_s'] = df['price_pct'].apply(lambda m: f"{m:0.1%}")
    return df


meta_data_cols = ['lat', 'long', 'price', 'price_s', 'asset_status', 'floor', 'square_meters', 'rooms_s', 'price_pct',
                  'ai_price_pct',
                  'pct_diff_median', 'pct_diff_median_s', 'price_pct_s']


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
        sql_state_asset = f' and {col_name} in ({states})'
    return sql_state_asset


def get_asset_points(df_all, price_from=None, price_to=None,
                     price_median_pct_range=None, price_discount_pct_range=None, price_ai_pct_range=None,
                     is_price_median_pct_range=False, is_price_discount_pct_range=False, is_price_ai_pct_range=False,
                     date_added_days=None, date_updated=None,
                     rooms_range=(None, None), with_agency=True, with_parking=None, with_balconies=None,
                     asset_status=(),
                     asset_type=(),
                     map_bounds=None,
                     limit=True, id_=None):
    if id_ is not None:
        df_f = df_all.query(f'id == "{id_}"')
        return df_f
    sql_asset_status = _multi_str_filter(asset_status, "asset_status")
    sql_asset_type = _multi_str_filter(asset_type, "asset_type")
    rooms_from = rooms_range[0] or 1
    rooms_to = rooms_range[1] or 100
    sql_cond = dict(
        sql_rooms_range=f"{rooms_from} <= rooms <= {rooms_to}.5" if rooms_from is not None and rooms_to is not None else "",
        sql_price=f"and {price_from} <= price <= {price_to}" if price_from is not None else "",
        sql_is_agency="and is_agency == False" if not with_agency else "",
        sql_is_parking="and parking > 0" if with_parking else "",
        sql_is_balcony="and balconies == True" if with_balconies else "",
        sql_asset_status=sql_asset_status,
        sql_asset_type=sql_asset_type,
        sql_median_price_pct=f"and group_size > 30 and {price_median_pct_range[0] / 100}<=pct_diff_median <= {price_median_pct_range[1] / 100}" if is_price_median_pct_range else "",
        sql_discount_pct=f"and {price_discount_pct_range[0] / 100} <= price_pct <= {price_discount_pct_range[1] / 100}" if is_price_discount_pct_range else "",
        # sql_median_price_pct=f"and group_size > 30 and pct_diff_median <= {median_price_pct}" if median_price_pct is not None else "",
        # sql_discount_pct=f"and -0.90 <= price_pct <= {discount_price_pct}" if discount_price_pct is not None else "",
        sql_ai_pct=f"and {price_ai_pct_range[0] / 100} <= ai_price_pct <= {price_ai_pct_range[1] / 100}" if is_price_ai_pct_range else "",
        sql_map_bounds=f"and {map_bounds[0][0]} < lat < {map_bounds[1][0]} and {map_bounds[0][1]} < long < {map_bounds[1][1]}" if map_bounds else "",
        sql_date_added=f"and date_added_d <= {date_added_days}" if date_added_days else "",
        sql_date_updated=f"and date_updated_d <= {date_updated}" if date_updated else "")
    q = ' '.join(list(sql_cond.values()))
    print(q)
    df_f = df_all.query(q)
    if limit:
        df_f = df_f[:FETCH_LIMIT]

    print(f"{datetime.now()} Triggerd, Fetched: {len(df_f)} rows")
    return df_f


def build_sidebar(deal):
    maps_url = f"http://maps.google.com/maps?z=12&t=m&q=loc:{deal['lat']}+{deal['long']}&hl=iw"  # ?hl=iw, t=k sattalite
    days_online = (datetime.today() - pd.to_datetime(deal['date_added'])).days
    date_added = pd.to_datetime(deal['date_added'])
    add_info = _get_parse_item_add_info(deal['id'])
    # add_info = res_get_add_info(deal.name)
    IMG_LIMIT = None
    if add_info:
        image_urls = add_info.pop('image_urls')
        image_urls = image_urls if image_urls is not None else []
        info_text = add_info.pop('info_text')
        add_info_text = [html.Tr(html.Td(f"{k}: {v}")) for k, v in add_info.items()]
    else:
        image_urls = []
        info_text = deal['info_text']
        add_info_text = None
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
            controls=False,
            indicators=True,
            interval=2000,
            ride="carousel",
            # style="sidebar-carousel"
        )

    # txt_html = html.Div([dbc.Row(
    #     [html.Span(f"{deal['price']:,.0f}₪", style={"font-size": "1.5vw"}),
    #      html.Span(str_price_pct, className="text-ltr")]
    # ),
    #     dbc.Row([dbc.Col([html.Span(f"מחיר הנכס מהחציון באיזור: "),
    #                       html.Span(f"{deal['pct_diff_median']:0.2%}", className="text-ltr")])])
    # ])
    def get_pct_style(v):
        if np.isnan(v):
            v = 0
        return {"background-color": get_color(v)}

    def get_html_span_pct(pct):
        return html.Span(f"{pct:.1%}", style=get_pct_style(pct), className="span-color-pct text-ltr")

    title_html = html.Div([html.Span(f"{deal['price']:,.0f}₪"),
                           get_html_span_pct(deal['price_pct'])])
    txt_html = html.Div(
        [html.Span(f"מחיר הנכס מהחציון באיזור: "),
         get_html_span_pct(deal['pct_diff_median']),
         html.P([html.Span(f"מחיר הנכס ממודל AI : "),
                 html.Span(f"{deal['ai_price']:,.0f} (±{deal['ai_std_pct']:.1%})", className="text-ltr"),
                 get_html_span_pct(deal['ai_price_pct'])]),

         html.H6(f"הועלה בתאריך {date_added.date()}, (לפני {days_online / 7:0.1f} שבועות)"),
         html.Span(f"מתי עודכן: {deal['date_updated']}"),
         html.Div(df_price_hist, className='text-ltr'),
         html.Span(),
         html.P([
             'תיווך' if deal['is_agency'] else 'לא תיווך',
             html.Br(),
             f"מצב הנכס: ",
             html.B(deal['asset_status'])]),
         html.P([f" {deal['rooms']} חדרים",
                 f" קומה  {round(deal['floor']) if deal['floor'] > 0 else 'קרקע'} ",
                 html.Br(),
                 f"{deal['asset_type']}, {deal['city']},{deal['street']}",
                 html.Br(),
                 f"{deal['square_meters']:,.0f} מטר",

                 html.A(href=maps_url, children=html.Img(src=icon_maps, style=dict(width=32, height=32)),
                        target="_blank"),
                 html.A(href=f"https://www.yad2.co.il/item/{deal['id']}",
                        children=html.Img(src=icon_real_estate, style=dict(width=32, height=32)),
                        target="_blank"),
                 ]),
         html.Div(children=[carousel], className="asset-images"),
         html.Span(info_text, className='sidebar-info-text'),
         # html.Br(),
         html.Table(children=add_info_text, style={"font-size": "0.8vw"}),
         # html.P("\n".join([f"{k}: {v}" for k, v in res_get_add_info(deal.name).items()])),
         ])
    return title_html, txt_html


from plotly import graph_objects as go


def plot_deal_vs_sale_sold(other_close_deals, df_tax, deal):
    # When the hist becomes square thats because there a huge anomaly in terms of extreme value
    sale_items = other_close_deals['price']
    # .hist(bins=min(70, len(sale_items)), legend=True, alpha=0.8)
    fig = go.Figure()
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
    fig.update_layout(  # title_text=str_txt,
        # barmode='stack',
        width=450,
        height=250,
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(x=0.0, y=1),
        dragmode=False)
    # fig['layout']['yaxis'].update(autorange=True)
    # fig['layout']['xaxis'].update(autorange=True)
    fig.update_xaxes(range=[deal['price'] // 2, deal['price'] * 2.5])
    return fig
    # plt.legend()


def get_similar_deals(df_all, deal, days_back=99, dist_km=1, with_nadlan=True):
    filter_rooms = True
    df_open_deals = filter_by_dist(df_all, deal, dist_km)
    if filter_rooms:
        df_open_deals = df_open_deals.dropna(subset='rooms')
        df_open_deals = df_open_deals[df_open_deals['rooms'].astype(float).astype(int) == int(float(deal['rooms']))]
    df_tax = None
    if with_nadlan:
        df_tax = get_nadlan_trans(deal, days_back, dist_km, filter_rooms)
    fig = plot_deal_vs_sale_sold(df_open_deals, df_tax, deal)
    return fig

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
