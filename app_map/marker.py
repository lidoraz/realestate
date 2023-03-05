import numpy as np
import dash_leaflet.express as dlx
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


icon1 = "https://cdn-icons-png.flaticon.com/128/447/447031.png"
icon2 = "https://cdn-icons-png.flaticon.com/128/7976/7976202.png"

js_draw_icon = assign("""
function(feature, latlng){
    console.log("A");
    const flag = L.icon({iconUrl: feature.properties.icon,
                         iconSize: [28, 28],
                         });
    console.log(feature.properties.icon);
    return L.marker(latlng, {icon: flag});
}""")

# js_draw_icon_div = assign("""
# function(feature, latlng){
#     console.log("1");
#     // console.log(feature.properties.icon);
#     const x = L.divIcon({
#         className: 'marker-div-icon',
#         html: `<img class="marker-div-image" src="${feature.properties.icon}"/>
#         <span class="marker-div-span">${feature.properties.icon_text}</span>`
#     })
#     console.log("2");
#     return L.marker(latlng, {icon: x});
# }
# """)
#
# TODO: ADDED SOPHISTICATED ICON HERE with 3 colors, but it does fit too good,
js_draw_icon3_div = assign("""
function(feature, latlng){
    console.log("1");
    // console.log(feature.properties.icon);
    const x = L.divIcon({
        className: 'marker-div-icon',
        html: `<img class="marker-div-image" src="${feature.properties.icon}"/>
        <div class="marker-div">
        <span class="marker-div-span" style="background-color: ${feature.properties._c1}">${feature.properties._t1}</span>
        <span class="marker-div-span" style="background-color: ${feature.properties._c2}">${feature.properties._t2}</span>
        <span class="marker-div-span" style="background-color: ${feature.properties._c3}">${feature.properties._t3}</span>
        </div>`
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
    <tr><td class="text-ltr"></td> <td class="text-rtl" colspan="2"><b>{m['asset_status']}</b></td>  </tr>
    <tr><td class="text-ltr">{m['rooms_s']}</td>          <td class="text-rtl">חדרים</td>  </tr>
    <tr><td class="text-ltr">{m['floor']:.0f}</td>          <td class="text-rtl">קומה</td>  </tr>
    <tr><td class="text-ltr">{m['square_meters']:,.0f}</td>          <td class="text-rtl">מ״ר</td>  </tr>
    <tr><td class="text-ltr">₪{m['last_price'] / m['square_meters']:,.0f}</td>          <td class="text-rtl">למ״ר</td>  </tr>
    <tr><td class="text-ltr" {style_color_pct_med}>{m['pct_diff_median_s']}</td><td class="text-rtl">חציון</td>  </tr>
    <tr><td class="text-ltr" {style_color_pct}>{m['price_pct_s']}</td>       <td class="text-rtl">הנחה</td>   </tr>
    </table>"""
    return html_tp


from colour import Color

max_colors = 13
colors = list(Color("green").range_to(Color("red"), max_colors))
half_idx = max_colors // 2


def get_color(x):
    if np.isnan(x):
        return "Black"
    x = x * 2.5
    x = max(min(x, 1), -1)
    idx = int(x * half_idx + half_idx)
    return colors[idx].hex


def generate_icon(deal):
    m = deal['metadata']
    return dict(  # icon=get_icon(deal, icon_metric),
        # icon_text=m['last_price_s'],
        _t1=m['price_pct_s'],
        _t2=m['pct_diff_median_s'],
        _t3=m['ai_price_pct_s'],
        _c1=get_color(m['price_pct']),
        _c2=get_color(m['pct_diff_median']),
        _c3=get_color(m['ai_price_pct'])
    )

marker_tooltip = "simple"

if marker_tooltip == 'simple':
    POINT_TO_LAYER_FUN = js_draw_icon
    _val = 0
elif marker_tooltip == 'complex':
    POINT_TO_LAYER_FUN = js_draw_icon3_div
    _val = 1
else:
    raise ValueError()


def get_marker_tooltip(deal_points, icon_metric):
    if marker_tooltip == 'complex':
        deal_points = dlx.dicts_to_geojson([{**deal, **dict(tooltip=create_tooltip(deal),
                                                            icon=get_icon(deal, icon_metric),
                                                            icon_text=deal['metadata']['last_price_s'],
                                                            **generate_icon(deal)
                                                            )}
                                            for deal in deal_points])
    elif marker_tooltip == 'simple':
        deal_points = dlx.dicts_to_geojson([{**deal, **dict(tooltip=create_tooltip(deal),
                                                            icon=get_icon(deal, icon_metric),
                                                            icon_text=deal['metadata']['last_price_s']
                                                            )}
                                            for deal in deal_points])
    else:
        raise ValueError()

    return deal_points
