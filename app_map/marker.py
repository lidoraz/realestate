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
    const x = L.divIcon({
        className: 'marker-div-icon',
        html: `
        <div class="marker-div">
        <span class="marker-div-span" style="background-color: ${feature.properties._marker_color}">${feature.properties._marker_text}</span>
        <span>${feature.properties._price_s}</span>
        </div>`
    })
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


def _row_table_if_pct_ok(pct, text):
    if np.isnan(pct):
        return ""
    return f"""<tr><td class="text-ltr" style="color:{gen_color(pct)}">{pct:0.1%}</td><td class="text-rtl">{text}</td></tr>"""


def convert_rooms_str(rooms: float):
    return str(int(rooms)) if (rooms * 10) % 10 == 0 else f"{rooms:0.1f}"


def create_tooltip(deal):
    m = deal['metadata']
    tr_ai_price = _row_table_if_pct_ok(m['ai_price_pct'], "AI")
    tr_chg_price = _row_table_if_pct_ok(m['price_pct'], "%")
    rooms_s = convert_rooms_str(m['rooms'])
    floor_s = "קרקע"[::-1] if m['floor'] == 0 else f"{m['floor']:.0f}"
    html_tp = f"""
    <table class="">    
    <tr><td class="text-ltr">{m['price']:,.0f}</td>      <td class="text-rtl">מחיר</td>   </tr>
    <tr><td class="text-rtl" colspan="2"><b>{m['asset_status']}</b></td>  </tr>
    <tr><td class="text-ltr">{rooms_s}</td>          <td class="text-rtl">חדרים</td>  </tr>
    <tr><td class="text-ltr">{floor_s}</td>          <td class="text-rtl">קומה</td>  </tr>
    <tr><td class="text-ltr">{m['square_meters']:,.0f}</td>          <td class="text-rtl">מ״ר</td>  </tr>
    {tr_ai_price}
    {tr_chg_price}
    </table>"""
    return html_tp


from colour import Color

max_colors = 6
multiplier = 4.0
col1 = "green"
col2 = "red"
col3 = "darkgray"  # Charcoal
g_colors = list(Color(col1).range_to(col3, max_colors))
r_colors = list(Color(col2).range_to(col3, max_colors))[::-1]
colors = (g_colors[:-1] + r_colors)  # [::-1]
# print("len(colors)", len(colors))
# https://stackoverflow.com/questions/929103/convert-a-number-range-to-another-range-maintaining-ratio
old_range = (1 - (-1))
new_range = ((len(colors) - 1) - 0)


def get_color(x):
    x = x * multiplier
    x = max(min(x, 1), -1)
    idx = int((((x - (-1)) * new_range) / old_range) + 0)
    return colors[idx].hex


def generate_icon_custom(deal, marker_metric):
    p = deal['metadata'][marker_metric]
    if np.isnan(p):
        p_text = "."
        color = "gray"
    else:
        prefix = '+' if p > 0 else '-' if p < 0 else ''
        p_text = f"{abs(p):.0%}" if p != 0 else "."
        p_text = f"{prefix}{p_text}"
        color = get_color(p) if abs(p) > 0.003 else "gray"  # "#00000000"
    return dict(_marker_text=p_text, _marker_color=color, _price_s=deal['metadata']['price_s'])


marker_tooltip = "custom"

if marker_tooltip == 'simple':
    POINT_TO_LAYER_FUN = js_draw_icon
elif marker_tooltip == "custom":
    POINT_TO_LAYER_FUN = js_draw_custom
else:
    raise ValueError()


def get_marker_tooltip(deal_points, marker_metric):
    if marker_tooltip in "custom":
        deal_points = dlx.dicts_to_geojson([{**deal, **dict(tooltip=create_tooltip(deal),
                                                            icon=get_icon(deal, marker_metric),
                                                            icon_text=deal['metadata']['price_s'],
                                                            **generate_icon_custom(deal, marker_metric)
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
