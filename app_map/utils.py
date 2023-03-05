from app_map.marker import get_marker_tooltip, icon_maps, icon_real_estate
from app_map.util_layout import *
from scrape_yad2.utils import _get_parse_item_add_info
from fetch_data.utils import filter_by_dist, get_nadlan_trans


def get_geojsons(df, icon_metric):
    deal_points = [dict(deal_id=idx, lat=d['lat'], lon=d['long'], metadata=d)
                   for
                   idx, d in df.iterrows()]
    deal_points = get_marker_tooltip(deal_points, icon_metric)
    return deal_points


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


def preprocess_to_str_deals(df):
    df['rooms_s'] = df['rooms'].apply(lambda m: f"{m if m % 10 == 0 else round(m)}")
    df['last_price_s'] = df['last_price'].apply(lambda m: f"₪{format_number(m)}")
    df['ai_price_pct_s'] = df['ai_price_pct'].apply(lambda m: f"{m:0.1%}")
    df['pct_diff_median_s'] = df['pct_diff_median'].apply(lambda m: f"{m:0.1%}")
    df['price_pct_s'] = df['price_pct'].apply(lambda m: f"{m:0.1%}")
    return df


def get_asset_points(df_all, price_from=None, price_to=None,
                     median_price_pct=None, discount_price_pct=None, ai_pct=None,
                     date_added_days=None, date_updated=None,
                     rooms_range=(None, None), with_agency=True, with_parking=None, with_balconies=None, state_asset=(),
                     map_bounds=None, is_median=True,
                     limit=True):
    if len(state_asset) > 0:
        states = ','.join([f"'{x}'" for x in state_asset])
        sql_state_asset = f' and asset_status in ({states})'
    else:
        sql_state_asset = ""
    rooms_from = rooms_range[0] or 1
    rooms_to = rooms_range[1] or 100
    sql_cond = dict(
        sql_rooms_range=f"{rooms_from} <= rooms <= {rooms_to}.5" if rooms_from is not None and rooms_to is not None else "",
        sql_price_from=f"and {price_from} <= last_price" if price_from is not None else "",
        sql_price_to=f"and {price_to} >= last_price" if price_to is not None else "",
        sql_is_agency="and is_agency == False" if not with_agency else "",
        sql_is_parking="and parking > 0" if with_parking else "",
        sql_is_balcony="and balconies == True" if with_balconies else "",
        sql_state_asset=sql_state_asset,
        sql_median_price_pct=f"and group_size > 30 and pct_diff_median <= {median_price_pct}" if median_price_pct is not None else "",
        sql_discount_pct=f"and -0.90 <= price_pct <= {discount_price_pct}" if discount_price_pct is not None else "",
        sql_ai_pct = f"and -0.90 <= ai_price_pct <= {ai_pct}" if ai_pct is not None else "",
        sql_map_bounds=f"and {map_bounds[0][0]} < lat < {map_bounds[1][0]} and {map_bounds[0][1]} < long < {map_bounds[1][1]}" if map_bounds else "",
        sql_date_added=f"and date_added_d <= {date_added_days}" if date_added_days else "",
        sql_date_updated=f"and date_updated_d <= {date_updated}" if date_updated else "")
    q = ' '.join(list(sql_cond.values()))
    print(q)
    df_f = df_all.query(q)
    if limit:
        df_f = df_f[:1_000]
    print(f"Triggerd, Fetched: {len(df_f)} rows")
    return df_f


def build_sidebar(deal):
    maps_url = f"http://maps.google.com/maps?z=12&t=m&q=loc:{deal['lat']}+{deal['long']}&hl=iw"  # ?hl=iw, t=k sattalite
    days_online = (datetime.today() - pd.to_datetime(deal['date_added'])).days
    date_added = pd.to_datetime(deal['date_added'])
    add_info = _get_parse_item_add_info(deal.name)
    # add_info = res_get_add_info(deal.name)
    if add_info:
        image_urls = add_info.pop('image_urls')
        image_urls = image_urls[:3] if image_urls is not None else []
        info_text = add_info.pop('info_text')
        add_info_text = [html.Tr(html.Td(f"{k}: {v}")) for k, v in add_info.items()]
    else:
        image_urls = []
        info_text = deal['info_text']
        add_info_text = None

    pct = deal['price_pct']
    str_price_pct = html.Span(f" ({pct:.2%})" if pct != 0 else "",
                              style={"color": "green" if pct < 0 else "red"})
    df_hist = pd.DataFrame([deal['dt_hist'], deal['price_hist']]) if deal['price_pct'] else None
    df_price_hist = html.Table([html.Tr([html.Td(v) for v in row.values]) for i, row in df_hist.iterrows()],
                               className="price-diff-table") if df_hist is not None else ""
    txt_html = html.Div(
        [html.Div([html.Span(f"{deal['last_price']:,.0f}₪", style={"font-size": "1.5vw"}),
                   html.Span(str_price_pct, className="text-ltr")]),
         html.Span(f"מחיר הנכס מהחציון באיזור: "),
         html.Span(f"{deal['pct_diff_median']:0.2%}", className="text-ltr"),
         html.P([html.Span(f"מחיר הנכס ממודל AI : "),
                 html.Span(f"{deal['ai_price']:,.0f} ({deal['ai_std_pct']    :.2%})", className="text-ltr"),
                 ]),

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
                 html.A(href=f"https://www.yad2.co.il/item/{deal.name}",
                        children=html.Img(src=icon_real_estate, style=dict(width=32, height=32)),
                        target="_blank"),
                 ]),
         # width="40%", height="40%")
         html.Div(children=[
             html.A(html.Img(src=src, style={"max-height": "100px", "padding": "1px"}), href=src, target="_blank") for
             src in image_urls],
             className="asset-images"),
         html.Span(info_text, className='sidebar-info-text'),
         # html.Br(),
         html.Table(children=add_info_text, style={"font-size": "0.8vw"}),
         # html.P("\n".join([f"{k}: {v}" for k, v in res_get_add_info(deal.name).items()])),
         ])
    return txt_html


from plotly import graph_objects as go


def plot_deal_vs_sale_sold(other_close_deals, df_tax, deal):
    # When the hist becomes square thats because there a huge anomaly in terms of extreme value
    sale_items = other_close_deals['last_price']
    sale_items = sale_items.rename(
        f'last_price #{len(sale_items)}')  # .hist(bins=min(70, len(sale_items)), legend=True, alpha=0.8)
    fig = go.Figure()
    tr_1 = go.Histogram(x=sale_items, name=sale_items.name, opacity=0.75, nbinsx=len(sale_items))
    fig.add_trace(tr_1)
    if df_tax is not None:
        sold_items = df_tax['price_declared']
        days_back = df_tax.attrs['days_back']
        if len(sold_items):
            sold_items = sold_items.rename(
                f'realPrice{days_back}D #{len(sold_items)}')  # .hist(bins=min(70, len(sold_items)), legend=True,alpha=0.8)
            tr_2 = go.Histogram(x=sold_items, name=sold_items.name, opacity=0.75, nbinsx=len(sold_items))
            fig.add_trace(tr_2)
    fig.add_vline(x=deal['last_price'], line_width=2,
                  line_color='red', line_dash='dash',
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


def get_similar_deals(df_all, deal, days_back=99, dist_km=1, get_nadlan=True):
    filter_rooms = True
    df_open_deals = filter_by_dist(df_all, deal, dist_km)
    if filter_rooms:
        df_open_deals = df_open_deals.dropna(subset='rooms')
        df_open_deals = df_open_deals[df_open_deals['rooms'].astype(float).astype(int) == int(float(deal['rooms']))]
    df_tax = get_nadlan_trans(deal, days_back, dist_km, filter_rooms) if get_nadlan else None
    print(f'get_similar_deals: other_close_deals={len(df_open_deals)}, df_tax={len(df_tax)}')
    fig = plot_deal_vs_sale_sold(df_open_deals, df_tax, deal)
    return fig
