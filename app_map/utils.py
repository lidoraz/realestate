import numpy as np
from dash import html
import pandas as pd
from datetime import datetime

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


icon1 = "https://cdn-icons-png.flaticon.com/128/447/447031.png"  # "/resources/location-pin.png" # "/Users/lidorazulay/Downloads/location-pin.png"
icon2 = "https://cdn-icons-png.flaticon.com/128/7976/7976202.png"  # "/resources/location.png" # '/Users/lidorazulay/Downloads/location.png'
js_draw_icon = assign("""function(feature, latlng){
const flag = L.icon({iconUrl: feature.properties.icon, iconSize: [28, 28]});
console.log(feature.properties.icon);
return L.marker(latlng, {icon: flag});
}""")


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


def create_tooltip(deal):
    m = deal['metadata']
    #  <img src="{icon_05}" class="tooltip-icon"/>
    # f"{deal['deal_id']}</br>
    m['rooms_s'] = f"{m['rooms'] if m['rooms'] % 10 == 0 else round(m['rooms'])}"
    m['last_price_s'] = f"₪{m['last_price'] / 1e6:,.2f}m"
    m['pct_diff_median_s'] = f"{m['pct_diff_median']:0.1%}"
    m['price_pct_s'] = f"{m['price_pct']:0.1%}"
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


def build_sidebar(deal):
    maps_url = f"http://maps.google.com/maps?z=12&t=m&q=loc:{deal['lat']}+{deal['long']}&hl=iw"  # ?hl=iw, t=k sattalite
    days_online = (datetime.today() - pd.to_datetime(deal['date_added'])).days
    date_added = pd.to_datetime(deal['date_added'])

    add_info = res_get_add_info(deal.name)
    if add_info:
        image_urls = add_info.pop('image_urls')
        info_text = add_info.pop('טקסט_חופשי')
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
         html.Div(children=[html.A(html.Img(src=src, style={"max-height": "100px", "padding": "1px"}), href=src, target="_blank") for src in image_urls[:3]],
                  className="asset-images"),
         # html.Br(),
         html.Table(children=add_info_text, style={"font-size": "0.8vw"}),
         # html.P("\n".join([f"{k}: {v}" for k, v in res_get_add_info(deal.name).items()])),
         html.Span(info_text, style={"font-size": "0.7vw"}),
         ])
    return txt_html
