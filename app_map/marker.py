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


def get_icon(deal, marker_metric='median'):
    p = deal['metadata'][marker_metric]
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

# js_draw_custom = assign("""
# function(feature, latlng){
#     console.log("1");
#     // console.log(feature.properties.icon);
#     const x = L.divIcon({
#         className: 'marker-div-icon',
#         html: `
#         <div class="marker-div">
#         <span class="marker-div-span" style="background-color: ${feature.properties._marker_color}">${feature.properties._marker_text}</span>
#         <img class="marker-div-image" src="https://cdn-icons-png.flaticon.com/128/6153/6153497.png"/>
#         </div>`
#     })
#     console.log("2");
#     return L.marker(latlng, {icon: x});
# }
# """)

js_draw_custom = assign("""
function(feature, latlng){
    console.log("1");
    // console.log(feature.properties.icon);
    const x = L.divIcon({
        className: 'marker-div-icon',
        html: `
        <div class="marker-div">
        <span class="marker-div-span" style="background-color: ${feature.properties._marker_color}">${feature.properties._marker_text}</span>
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
    <tr><td class="text-ltr">{m['price_s']}</td>      <td class="text-rtl">מחיר</td>   </tr>
    <tr><td class="text-ltr"></td> <td class="text-rtl" colspan="2"><b>{m['asset_status']}</b></td>  </tr>
    <tr><td class="text-ltr">{m['rooms_s']}</td>          <td class="text-rtl">חדרים</td>  </tr>
    <tr><td class="text-ltr">{m['floor']:.0f}</td>          <td class="text-rtl">קומה</td>  </tr>
    <tr><td class="text-ltr">{m['square_meters']:,.0f}</td>          <td class="text-rtl">מ״ר</td>  </tr>
    <tr><td class="text-ltr">₪{m['price'] / m['square_meters']:,.0f}</td>          <td class="text-rtl">למ״ר</td>  </tr>
    <tr><td class="text-ltr" {style_color_pct_med}>{m['pct_diff_median_s']}</td><td class="text-rtl">חציון</td>  </tr>
    <tr><td class="text-ltr" {style_color_pct}>{m['price_pct_s']}</td>       <td class="text-rtl">הנחה</td>   </tr>
    </table>"""
    return html_tp


from colour import Color

max_colors = 5
g_colors = list(Color("green").range_to('lightgray', max_colors))
r_colors = list(Color("red").range_to('lightgray', max_colors))[::-1]
colors = (g_colors + r_colors[1:])[::-1]
print("len(colors)", len(colors))
# https://stackoverflow.com/questions/929103/convert-a-number-range-to-another-range-maintaining-ratio
old_range = (1 - (-1))
new_range = ((len(colors) - 1) - 0)


def get_color(x):
    x = x * 2
    x = max(min(x, 1), -1)
    idx = int((((x - (-1)) * new_range) / old_range) + 0)
    # x = max(min(x, 1), -1)
    # idx = int(x * half_idx + half_idx)
    return colors[idx].hex


def generate_icon(deal, _):
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


def generate_icon_custom(deal, marker_metric):
    p = deal['metadata'][marker_metric]
    if np.isnan(p):
        p_text = "?"
        color = "Black"
    else:
        prefix = '+' if p > 0 else '-' if p < 0 else ''
        p_text = f"{abs(p):.0%}" if p != 0 else ""
        p_text = f"{prefix}{p_text}"
        color = get_color(p) if p != 0 else "#00000000"
    return dict(_marker_text=p_text, _marker_color=color)


marker_tooltip = "custom"

if marker_tooltip == 'simple':
    POINT_TO_LAYER_FUN = js_draw_icon
elif marker_tooltip == 'complex':
    POINT_TO_LAYER_FUN = js_draw_icon3_div
elif marker_tooltip == "custom":
    POINT_TO_LAYER_FUN = js_draw_custom
else:
    raise ValueError()


def get_marker_tooltip(deal_points, marker_metric):
    if marker_tooltip in ('complex', "custom"):
        icon_details = generate_icon_custom if marker_tooltip == "custom" else generate_icon
        deal_points = dlx.dicts_to_geojson([{**deal, **dict(tooltip=create_tooltip(deal),
                                                            icon=get_icon(deal, marker_metric),
                                                            icon_text=deal['metadata']['price_s'],
                                                            **icon_details(deal, marker_metric)
                                                            )}
                                            for deal in deal_points])
    elif marker_tooltip == 'simple':
        deal_points = dlx.dicts_to_geojson([{**deal, **dict(tooltip=create_tooltip(deal),
                                                            icon=get_icon(deal, marker_metric),
                                                            icon_text=deal['metadata']['price_s']
                                                            )}
                                            for deal in deal_points])
    else:
        raise ValueError()

    return deal_points
