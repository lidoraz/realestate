#
# # https://lyz-code.github.io/blue-book/coding/python/dash_leaflet/
# https://dash-leaflet-docs.onrender.com/#geojson

import time
import dash
import dash_bootstrap_components as dbc
from dash import Output, Input, State, ctx

from app_map.util_layout import div_left_map, div_offcanvas, get_div_top_bar, get_table
from app_map.utils import *

rent_config_default = {"price-from": 0.5, "price-to": 3, "median-price-pct": None,
                       "switch-median": False,
                       "discount-price-pct": -0.05,
                       "price_mul": 1e3}
df_all = pd.read_pickle('resources/yad2_rent_df.pk')
# TODO: df_all.query("last_price > 500000 and square_meters < 200 and status == 'משופץ'").sort_values('avg_price_m'), can create a nice view for sorting by avg_price per meter.
df_all['pct_diff_median'] = 0

df_all['ai_mean'] = df_all['ai_mean'] * (df_all['ai_std_pct'] < 0.15)  # Take only certain AI predictions
df_all['ai_mean_pct'] = df_all['ai_mean'].replace(0, np.nan)
df_all['ai_mean_pct'] = df_all['last_price'] / df_all['ai_mean_pct'] - 1

df_all['avg_price_m'] = df_all['last_price'] / df_all['square_meters']
df_all['date_added'] = pd.to_datetime(df_all['date_added'])
df_all['date_added_d'] = (datetime.today() - df_all['date_added']).dt.days
df_all['updated_at'] = pd.to_datetime(df_all['updated_at'])
df_all['updated_at_d'] = (datetime.today() - df_all['updated_at']).dt.days
# df_f = df.query('last_price < 3000000 and -0.9 < price_pct < -0.01 and price_diff < 1e7')  # [:30]
df_all.query('-0.89 <price_pct < -0.05').to_csv('df_rent.csv')
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

# def get_asset_points(price_from=500_000, price_to=3_000_000, median_price_pct=-0.1, date_added_days=100,
#                      rooms_range=(3, 4), with_agency=True, state_asset=()):


app.layout = html.Div(children=[
    html.Div(className="top-container", children=get_div_top_bar(rent_config_default)),
    html.Div(className="grid-container", children=[
        html.Div(className="left-container", children=[html.Div(id='table-container', children=None)]),
        html.Div(className="right-container", children=[div_left_map]),
    ]),

    html.Div(className="modal-container", children=[div_offcanvas])
])


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
    [Output("geojson", "data"), Output("table-container", "children"), Output("fetched-assets", "children"),
     Output("button-around", "n_clicks"),
     Output("button-return", "n_clicks")],
    [Input("price-from", "value"), Input("price-to", "value"), Input("median-price-pct", "value"),
     Input("discount-price-pct", "value"),
     Input("date-added", "value"), Input("date-updated", "value"),
     Input("rooms-slider", "value"), Input('agency-check', "value"),
     Input('parking-check', "value"), Input('balconies-check', "value"),
     Input('state-asset', "value"),
     Input("button-around", "n_clicks"), Input("button-return", "n_clicks"),
     Input('switch-median', 'value')],
    Input('map', 'bounds'), State('map', 'zoom')
    # parking-check'),
    #                 dcc.Checklist(options=[{'label': 'מרפסת', 'value': 'Y'}], value=['Y'], inline=True,
    #                               id='balconies-check')
)
def show_assets(price_from, price_to, median_price_pct, discount_price_pct, date_added, updated_at,
                rooms_range, with_agency, with_parking, with_balconies, state_asset, n_clicks_around, n_clicks_return,
                is_median,
                map_bounds, map_zoom):
    # print_ctx()

    is_triggered_by_map_bounds = len(ctx.triggered_prop_ids) == 1 and list(ctx.triggered_prop_ids)[0] == "map.bounds"
    if map_zoom != context['map_zoom'] and is_triggered_by_map_bounds:
        context['map_zoom'] = map_zoom
        past_ts = context['zoom_ts']
        context['zoom_ts'] = time.time()
        update_diff = context['zoom_ts'] - past_ts
        if update_diff < 2:
            print(update_diff)
            print("not much time has passed")
            print("Zoom changed! - No update")
            return dash.no_update
    print(locals())
    print(ctx.triggered_prop_ids, map_zoom)
    # sleep_bounds()
    if n_clicks_around:
        df_f = get_asset_points(df_all, map_bounds=map_bounds, limit=True)
    else:
        price_from = price_from * rent_config_default["price_mul"] if price_from is not None else None
        price_to = price_to * rent_config_default["price_mul"] if price_to is not None else None
        with_agency = True if len(with_agency) else False
        with_parking = True if len(with_parking) else None
        with_balconies = True if len(with_balconies) else None
        df_f = get_asset_points(df_all, price_from, price_to, median_price_pct, discount_price_pct, date_added,
                                updated_at,
                                rooms_range,
                                with_agency, with_parking, with_balconies, map_bounds=map_bounds,
                                state_asset=state_asset, is_median=is_median, limit=True)
    # Can keep a list of points, if after fetch there was no new, no need to build new points, just keep them to save resources
    df_f = preprocess_to_str_deals(df_f)
    icon_metric = 'pct_diff_median' if is_median else 'price_pct'
    icon_metric = 'price_pct'
    deal_points = get_geojsons(df_f, icon_metric)

    return deal_points, get_table(df_f), len(df_f), None, None


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
            fig = get_similar_deals(df_all, deal)
            return not is_open, None, str_html, fig
    return is_open, None, None, {}


# @app.callback(
#     Output('datatable-interactivity', "editable"),
#     # [Output("datatable-rfStats", "data"), Output("datatable-rfStats", "selected_rows")],
#     [Input("datatable-interactivity", "selected_rows")]# + plot_dev_lvl_filter_inputs
# )
# def handle_table_row_select(row):
#     print("handle_table_row_select", row)
#     return dash.no_update
#      # filtered_df.sort_values(by=['lastUpdated']).to_dict('records'), [row_id]

if __name__ == '__main__':
    app.run_server(debug=True)
