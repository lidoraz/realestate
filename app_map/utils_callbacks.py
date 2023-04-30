import numpy as np
from dash import html, Output, Input, State, ctx
import dash
import time
import pandas as pd
from app_map.util_layout import get_interactive_table, CLUSTER_MAX_ZOOM, marker_type_options
from app_map.utils import get_asset_points, find_center, get_geojsons, build_sidebar, get_similar_deals
import logging
from flask import request

LOGGER = logging.getLogger()

clear_filter_input_outputs = [
    Output('button-clear', "n_clicks"),
    Output("price-slider", "value"),
    Output("price-median-pct-slider", "value"),
    Output("price-discount-pct-slider", "value"),
    Output("ai-price-pct-slider", "value"),
    Output("price-median-pct-slider-check", "value"),
    Output("price-discount-pct-slider-check", "value"),
    Output("ai-price-pct-slider-check", "value"),
    Output("date-added", "value"),
    Output("rooms-slider", "value"),
    Output("asset-status", "value"),
    Output("asset-type", "value"),
    Input('button-clear', "n_clicks")]


def clear_filter(n_clicks):
    if n_clicks:
        return 0, [0, 10_000], [-100, 0], [-100, 0], [-100, 0], [], [], [], None, (1, 6), [], []
    return dash.no_update


# df_all = pd.DataFrame()
config_defaults = dict()


def get_context_by_rule():
    name = request.url_rule.endpoint.split('/')[1]
    LOGGER.debug(f"context => {name}")
    return config_defaults[name]


context = dict(map_zoom=300, zoom_ts=time.time())


def handle_marker_type(marker_type, marker_types):
    # global context
    marker_type_bool = np.array(marker_types)
    marker_type_sum = marker_type_bool.sum()
    if marker_type_sum == 1:
        vals = [x['value'] for x in marker_type_options]
        out_marker = vals[marker_type_bool.argmax()]
    else:
        out_marker = marker_type
    return out_marker


# def print_ctx():
#     import json
#     ctx_msg = json.dumps({
#         # 'states': ctx.states,
#         'triggered_prop_ids': ctx.triggered_prop_ids,
#         'triggered': ctx.triggered,
#         'timing_information': ctx.timing_information,
#         # 'inputs': ctx.inputs
#     }, indent=2)
#     print(ctx_msg)


# def sleep_bounds(min_sleep_time=1.5):
#     is_triggered_by_map_bounds = len(ctx.triggered_prop_ids) == 1 and list(ctx.triggered_prop_ids)[0] == "map.bounds"
#     if is_triggered_by_map_bounds:
#         trigger_timing = ctx.timing_information
#         time_passed_sec = (datetime.now().timestamp() - trigger_timing['__dash_server']['dur'])
#         print('time_passed_sec', time_passed_sec)
#         if time_passed_sec < min_sleep_time:
#             sleep_time = min_sleep_time - time_passed_sec
#             print('sleep_time', sleep_time)
#             time.sleep(sleep_time)


def limit_refresh(map_zoom):
    is_triggered_by_map_bounds = len(ctx.triggered_prop_ids) == 1 and list(ctx.triggered_prop_ids)[
        0] == "big-map.bounds"
    if map_zoom != context['map_zoom'] and is_triggered_by_map_bounds:
        context['map_zoom'] = map_zoom
        past_ts = context['zoom_ts']
        context['zoom_ts'] = time.time()
        update_diff = context['zoom_ts'] - past_ts
        if update_diff < 2:
            LOGGER.debug(f'not much time has passed, Zoom changed! - No update {update_diff}')
            return True
    return False
    # print(locals())
    # print(ctx.triggered_prop_ids, map_zoom)
    # sleep_bounds()


show_assets_input_output = [Output("geojson", "data"),
                            Output("datatable-interactivity", "columns"),
                            Output("datatable-interactivity", "data"),
                            Output("datatable-interactivity", "style_data_conditional"),
                            Output("fetched-assets", "children"),
                            Output("button-around", "n_clicks"),
                            Input("price-slider", "value"),
                            Input("price-median-pct-slider", "value"),
                            Input("price-discount-pct-slider", "value"),
                            Input("ai-price-pct-slider", "value"),
                            #
                            Input("price-median-pct-slider-check", "value"),
                            Input("price-discount-pct-slider-check", "value"),
                            Input("ai-price-pct-slider-check", "value"),
                            #
                            Input("date-added", "value"), Input("date-updated", "value"),
                            Input("rooms-slider", "value"), Input("floor-slider", "value"),
                            Input('agency-check', "value"),
                            Input('parking-check', "value"), Input('balconies-check', "value"),
                            Input('asset-status', "value"), Input('asset-type', "value"),
                            Input("button-around", "n_clicks"),
                            Input('marker-type', 'value'),
                            Input('search-input', 'value'),
                            Input('big-map', 'bounds'), State('big-map', 'zoom'),
                            State("datatable-interactivity", "active_cell")]


def show_assets(price_range,
                price_median_pct_range, price_discount_pct_range, price_ai_pct_range,
                is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range,
                date_added, date_updated,
                rooms_range, floor_range,
                with_agency, with_parking, with_balconies, asset_status, asset_type, n_clicks_around,
                marker_type, search_input,
                map_bounds, map_zoom, active_cell=None):
    conf = get_context_by_rule()

    if limit_refresh(map_zoom):
        return dash.no_update
    LOGGER.debug("marker_type", marker_type)
    with_agency = True if len(with_agency) else False
    with_parking = True if len(with_parking) else None
    with_balconies = True if len(with_balconies) else None
    is_price_median_pct_range = len(is_price_median_pct_range) > 0
    is_price_discount_pct_range = len(is_price_discount_pct_range) > 0
    is_price_ai_pct_range = len(is_price_ai_pct_range) > 0
    df = conf['func_data']()
    city = search_input if len(search_input) and find_center(df, search_input) else None
    map_bounds = map_bounds if city is None else None

    if active_cell:
        return dash.no_update
    price_from = price_range[0] * conf["price_mul"]
    # when max price is at limits, allow prices above it
    price_to = np.inf if price_range[0] == conf['price-max'] else price_range[1] * conf["price_mul"]
    if n_clicks_around:
        df_f = get_asset_points(df, -np.inf, np.inf, map_bounds=map_bounds)
    else:
        df_f = get_asset_points(df, price_from, price_to, city,
                                price_median_pct_range, price_discount_pct_range, price_ai_pct_range,
                                is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range,
                                date_added, date_updated, rooms_range, floor_range,
                                with_agency, with_parking, with_balconies, map_bounds=map_bounds,
                                asset_status=asset_status, asset_type=asset_type)
    # Can keep a list of points, if after fetch there was no new, no need to build new points, just keep them to save resources
    # out_marker = handle_marker_type(marker_type,
    #                                 [is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range])
    n_rows = len(df_f)
    FETCH_LIMIT = 250
    df_f = df_f[:FETCH_LIMIT]
    deal_points = get_geojsons(df_f, marker_type)
    columns, data, style_data_conditional = get_interactive_table(df_f)
    days_b = df["date_updated_d"].min()
    bot_html = f'נמצאו {n_rows:,.0f} נכסים {"" if (-1 if np.isnan(days_b) else days_b) == 0 else " .."}'
    return deal_points, columns, data, style_data_conditional, bot_html, None


toggle_model_input_outputs = [Output("geojson", "click_feature"),  # output none to reset button for re-click
                              Output("modal", "is_open"),
                              Output("modal-title", "children"),
                              Output("marker", "children"),
                              Output("histogram", "figure"),
                              Input("geojson", "click_feature")]


def toggle_modal(feature):
    if feature:
        props = feature['properties']
        if 'deal_id' in props:
            conf = get_context_by_rule()
            deal_id = feature['properties']['deal_id']
            deal = conf['func_data']().loc[deal_id]
            title_modal, str_html = build_sidebar(deal)
            fig = get_similar_deals(conf['func_data'](), deal, with_nadlan=conf['with_nadlan'])
            return None, True, title_modal, str_html, fig
    return dash.no_update


focus_on_asset_input_outputs = [Output("big-map", "center"),
                                Output("big-map", "zoom"),
                                Output("map-marker", "opacity"),
                                Output("map-marker", "position"),
                                Output("datatable-interactivity", "selected_cells"),
                                Output("datatable-interactivity", "active_cell"),
                                Output("clear-cell-button", "n_clicks"),
                                ##
                                Output("search-input", "invalid"),
                                Output("search-input", "value"),
                                Output("search-clear", "n_clicks"),

                                Input("search-input", "value"),
                                Input("search-clear", "n_clicks"),
                                Input("clear-cell-button", "n_clicks"),
                                Input("table-modal", "is_open"),
                                Input("datatable-interactivity", "active_cell"),
                                State("datatable-interactivity", "data"),
                                ]


# This has 2 properties:
#  1. Focus on asset that has been selected with the table using the map center function
#  2. handles the search bar for a city and its reset button
# dl.Marker(position=[31.7, 32.7], opacity=0, id='map-marker')
def focus_on_asset(keyword, n_clicks_clear_search, n_clicks_clear_marker, table_modal_is_open, table_active_cell, table_data):
    if n_clicks_clear_search:
        return [dash.no_update for _ in range(7)] + [False, "", 0]
    if n_clicks_clear_marker or (not table_modal_is_open and table_active_cell):
        return [dash.no_update, dash.no_update, 0, dash.no_update] + [[], None, 0] + [dash.no_update for _ in range(3)]
    # if not len(keyword) and table_active_cell is None:
    #     return dash.no_update
    conf = get_context_by_rule()
    df = conf['func_data']()
    if table_active_cell:
        id_ = [x for x in table_data if x['id'] == table_active_cell['row_id']][0]['id']
        item = get_asset_points(df, id_=id_).squeeze()
        position = [item['lat'], item['long']]
        return [position, CLUSTER_MAX_ZOOM + 1, 0.75, position] + [dash.no_update for _ in range(6)]
    if len(keyword):
        pos = find_center(df, keyword)
        if pos:
            return pos, 14, *[dash.no_update for _ in range(5)], False, keyword, 0
        else:
            return [dash.no_update for _ in range(7)] + [True, keyword, 0]


show_table_input_output = [Output("table-toggle", "n_clicks"),
                           Output("table-modal", "is_open"),
                           Input("table-toggle", "n_clicks"),
                           State("table-modal", "is_open")]


def show_table_modal(n_clicks, is_open):
    if n_clicks:
        return 0, not is_open
    return dash.no_update


#
# clear_table_selected_input_output = [
#     # Output("map-marker", "opacity"), # already being used, need to rework this part
#     Output("datatable-interactivity", "selected_cells"),
#     Output("datatable-interactivity", "active_cell"),
#     Input("clear-cell-button", "n_clicks"),
#     # Input("table-modal", "is_open")
# ]
#
#
# def clear_selected_if_closed(is_open, n_clicks):
#     print("clear_selected_if_closed", n_clicks, is_open)
#     # if not is_open or n_clicks:
#     #     return [], None#, 0
#     # return dash.no_update


disable_range_input_outputs = [Output("price-median-pct-slider", "disabled"),
                               Output("price-discount-pct-slider", "disabled"),
                               Output("ai-price-pct-slider", "disabled"),
                               Input("price-median-pct-slider-check", "value"),
                               Input("price-discount-pct-slider-check", "value"),
                               Input("ai-price-pct-slider-check", "value"),
                               ]


def disable_range_sliders(is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range):
    is_price_median_pct_range = len(is_price_median_pct_range) == 0
    is_price_discount_pct_range = len(is_price_discount_pct_range) == 0
    is_price_ai_pct_range = len(is_price_ai_pct_range) == 0
    return is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range


toggle_cluster_input_outputs = [
    Output("geojson", "cluster"),
    Input("cluster-check", "value")
]


def toggle_cluster(cluster_check):
    return [len(cluster_check) > 0]


def add_callbacks(app, config):
    # global df_all, config_defaults
    # df_all = df
    name = config['name']
    config_defaults[name] = config
    app.callback(clear_filter_input_outputs)(clear_filter)
    app.callback(show_assets_input_output)(show_assets)
    app.callback(toggle_model_input_outputs)(toggle_modal)
    app.callback(focus_on_asset_input_outputs)(focus_on_asset)
    app.callback(disable_range_input_outputs)(disable_range_sliders)
    app.callback(show_table_input_output)(show_table_modal)
    app.callback(toggle_cluster_input_outputs)(toggle_cluster)
    # app.callback(clear_table_selected_input_output)(clear_selected_if_closed)
