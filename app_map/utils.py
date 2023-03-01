import numpy as np
from dash import html
import pandas as pd
from datetime import datetime
import dash_leaflet.express as dlx
from dash_extensions.javascript import assign

from forsale.scraper_yad2 import _get_parse_item_add_info
from forsale.utils import calc_dist, get_similar_closed_deals

icon_05 = "https://cdn-icons-png.flaticon.com/128/9387/9387262.png"
icon_10 = "https://cdn-icons-png.flaticon.com/128/6912/6912962.png"
icon_20 = "https://cdn-icons-png.flaticon.com/128/6913/6913127.png"
icon_30 = "https://cdn-icons-png.flaticon.com/128/6913/6913198.png"
icon_40 = "https://cdn-icons-png.flaticon.com/128/9556/9556570.png"
icon_50 = "https://cdn-icons-png.flaticon.com/128/5065/5065451.png"
icon_regular = "https://cdn-icons-png.flaticon.com/128/6153/6153497.png"
icon_maps = "https://cdn-icons-png.flaticon.com/128/684/684809.png"
icon_real_estate = "https://cdn-icons-png.flaticon.com/128/602/602275.png"


def get_icon(deal, metric='pct_diff_median'):
    p = deal['metadata'][metric]
    if -0.1 < p <= -0.05:
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


icon1 = "https://cdn-icons-png.flaticon.com/128/447/447031.png"
icon2 = "https://cdn-icons-png.flaticon.com/128/7976/7976202.png"

# https://stackoverflow.com/questions/34775308/leaflet-how-to-add-a-text-label-to-a-custom-marker-icon
# Can use text instead of just icon with using DivIcon in JS.
js_draw_icon = assign("""
function(feature, latlng){
    const flag = L.icon({iconUrl: feature.properties.icon,
                         iconSize: [28, 28],
                         });
    console.log(feature.properties.icon);
    return L.marker(latlng, {icon: flag});
}""")


def get_geojsons(df, icon_metric):
    deal_points = [dict(deal_id=idx, lat=d['lat'], lon=d['long'], color='black', icon="fa-light fa-house", metadata=d)
                   for
                   idx, d in df.iterrows()]
    deal_points = dlx.dicts_to_geojson([{**deal, **dict(tooltip=create_tooltip(deal),
                                                        icon=get_icon(deal, icon_metric),
                                                        # f"{deal['metadata'][metric]:.0%}"
                                                        icon_text=deal['metadata']['last_price_s'])}
                                        for deal in deal_points])
    return deal_points


# function(feature, latlng){
#     const ico = L.DivIcon({
#         className: 'my-div-icon',
#         html: '<img class="icon-div-image" src=${feature.properties.icon}/>'+
#               '<span class="icon-div-span">feature.properties.icon_text</span>'
#     })
#     return L.Marker(latlng, {icon: ico})
# }
js_draw_icon_div = assign("""
function(feature, latlng){
    console.log("1");
    // console.log(feature.properties.icon);
    const x = L.divIcon({
        className: 'marker-div-icon',
        html: `<img class="marker-div-image" src="${feature.properties.icon}"/>
        <span class="marker-div-span">${feature.properties.icon_text}</span>`
    })
    console.log("2");
    return L.marker(latlng, {icon: x});
}
""")


def gen_color(x):
    if x == np.NaN:
        return 'black'
    if x > 0.02:
        return 'red'
    if x < -0.02:
        return 'green'
    return 'black'


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
    df['pct_diff_median_s'] = df['pct_diff_median'].apply(lambda m: f"{m:0.1%}")
    df['price_pct_s'] = df['price_pct'].apply(lambda m: f"{m:0.1%}")
    return df


def create_tooltip(deal):
    m = deal['metadata']
    #  <img src="{icon_05}" class="tooltip-icon"/>
    # f"{deal['deal_id']}</br>
    style_color_pct_med = f"""style="color:{gen_color(m['pct_diff_median'])}" """
    style_color_pct = f"""style="color:{gen_color(m['price_pct'])}" """
    # print(style_color_pct)
    html_tp = f"""
    <table class="">
    <tr><td class="text-ltr">{m['last_price_s']}</td>      <td class="text-rtl">מחיר</td>   </tr>
    <tr><td class="text-ltr"></td> <td class="text-rtl" colspan="2"><b>{m['status']}</b></td>  </tr>
    <tr><td class="text-ltr">{m['rooms_s']}</td>          <td class="text-rtl">חדרים</td>  </tr>
    <tr><td class="text-ltr">{m['floor']:.0f}</td>          <td class="text-rtl">קומה</td>  </tr>
    <tr><td class="text-ltr">{m['square_meters']:,.0f}</td>          <td class="text-rtl">מ״ר</td>  </tr>
    <tr><td class="text-ltr">₪{m['last_price'] / m['square_meters']:,.0f}</td>          <td class="text-rtl">למ״ר</td>  </tr>
    <tr><td class="text-ltr" {style_color_pct_med}>{m['pct_diff_median_s']}</td><td class="text-rtl">חציון</td>  </tr>
    <tr><td class="text-ltr" {style_color_pct}>{m['price_pct_s']}</td>       <td class="text-rtl">הנחה</td>   </tr>
    </table>"""
    return html_tp


def get_asset_points(df_all, price_from=None, price_to=None, median_price_pct=None, discount_price_pct=None,
                     date_added_days=None, updated_at=None,
                     rooms_range=(None, None), with_agency=True, with_parking=None, with_balconies=None, state_asset=(),
                     map_bounds=None, is_median=True,
                     limit=True):
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
        sql_is_parking="and parking > 0" if with_parking else "",
        sql_is_balcony="and balconies == True" if with_balconies else "",
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
                 html.Span(f"{deal['ai_mean']:,.0f} ({deal['ai_std_pct']    :.2%})", className="text-ltr"),
                 ]),

         html.H6(f"הועלה בתאריך {date_added.date()}, (לפני {days_online / 7:0.1f} שבועות)"),
         html.Span(f"מתי עודכן: {deal['updated_at']}"),
         html.Div(df_price_hist, className='text-ltr'),
         html.Span(),
         html.P([
             'תיווך' if deal['is_agency'] else 'לא תיווך',
             html.Br(),
             f"מצב הנכס: ",
             html.B(deal['status'])]),
         html.P([f" {deal['rooms']} חדרים",
                 f" קומה  {round(deal['floor']) if deal['floor'] > 0 else 'קרקע'} ",
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


def get_similar_deals(df_all, deal, days_back=99, dist_km=1):
    # https://plotly.com/python/histograms/
    # deal = df.loc[deal_id]
    other_close_deals = calc_dist(df_all, deal, dist_km)  # .join(df)
    df_tax = get_similar_closed_deals(deal, days_back, dist_km, True)
    print(f'get_similar_deals: other_close_deals={len(other_close_deals)}, df_tax={len(df_tax)}')
    # display(df_tax)
    # nice cols:
    #
    # df_tax[['dist_from_deal', 'gush', 'tarIska', 'yeshuv', 'rechov', 'bayit', 'dira', 'mcirMozhar', 'shetachBruto', 'shetachNeto', 'shnatBniya', 'misHadarim', 'lblKoma']]
    fig = plot_deal_vs_sale_sold(other_close_deals, df_tax, deal)
    return fig
