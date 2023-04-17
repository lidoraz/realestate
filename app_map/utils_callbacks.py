import numpy as np
from dash import html, Output, Input, State, ctx
import dash
import time
from app_map.util_layout import get_interactive_table, CLUSTER_MAX_ZOOM, marker_type_options
from app_map.utils import get_asset_points, preprocess_to_str_deals, get_geojsons, build_sidebar, get_similar_deals

clear_filter_input_outputs = [
    Output('button-clear', "n_clicks"),
    # Output("price-slider", "value"),
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
        return 0, [-100, 0], [-100, 0], [-100, 0], [], [], [], None, (1, 6), [], []
    return dash.no_update


# df_all = pd.DataFrame()
config_defaults = dict()


def get_context_by_rule():
    from flask import request
    print("$$$$", request.url_rule)
    name = request.url_rule.endpoint.split('/')[1]
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
            print(update_diff)
            print("not much time has passed, Zoom changed! - No update")
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
                            Input('big-map', 'bounds'), State('big-map', 'zoom'),
                            State("datatable-interactivity", "active_cell")]


def show_assets(price_range,
                price_median_pct_range, price_discount_pct_range, price_ai_pct_range,
                is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range,
                date_added, date_updated,
                rooms_range, floor_range,
                with_agency, with_parking, with_balconies, asset_status, asset_type, n_clicks_around,
                marker_type,
                map_bounds, map_zoom, active_cell=None):
    conf = get_context_by_rule()
    if limit_refresh(map_zoom):
        return dash.no_update
    print("marker_type", marker_type)
    with_agency = True if len(with_agency) else False
    with_parking = True if len(with_parking) else None
    with_balconies = True if len(with_balconies) else None
    is_price_median_pct_range = len(is_price_median_pct_range) > 0
    is_price_discount_pct_range = len(is_price_discount_pct_range) > 0
    is_price_ai_pct_range = len(is_price_ai_pct_range) > 0

    if active_cell:
        return dash.no_update
    if n_clicks_around:
        df_f = get_asset_points(conf['func_data'](), map_bounds=map_bounds, limit=True)
    else:
        # special case - max over 10M
        if price_range[0] == conf['price-max'] and price_range[0] == price_range[1]:
            price_from = conf['price-max'] * conf["price_mul"]
            price_to = np.inf
        else:
            price_from = price_range[0] * conf["price_mul"]
            price_to = price_range[1] * conf["price_mul"]
        df_f = get_asset_points(conf['func_data'](), price_from, price_to,
                                price_median_pct_range, price_discount_pct_range, price_ai_pct_range,
                                is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range,
                                date_added, date_updated, rooms_range, floor_range,
                                with_agency, with_parking, with_balconies, map_bounds=map_bounds,
                                asset_status=asset_status, asset_type=asset_type, limit=True)
    # Can keep a list of points, if after fetch there was no new, no need to build new points, just keep them to save resources
    out_marker = handle_marker_type(marker_type,
                                    [is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range])
    deal_points = get_geojsons(df_f, out_marker)
    columns, data, style_data_conditional = get_interactive_table(df_f)
    return deal_points, columns, data, style_data_conditional, len(df_f), None


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
                                Input("datatable-interactivity", "active_cell"),
                                State("datatable-interactivity", "data"),
                                ]


# dl.Marker(position=[31.7, 32.7], opacity=0, id='map-marker')
def focus_on_asset(table_active_cell, table_data):
    if table_active_cell is None:
        return dash.no_update
    id_ = [x for x in table_data if x['id'] == table_active_cell['row_id']][0]['id']
    conf = get_context_by_rule()
    item = get_asset_points(conf['func_data'](), id_=id_).squeeze()
    position = [item['lat'], item['long']]
    return position, CLUSTER_MAX_ZOOM + 1, 0.75, position


show_table_input_output = [Output("table-toggle", "n_clicks"),
                           Output("table-modal", "is_open"),
                           Input("table-toggle", "n_clicks"),
                           State("table-modal", "is_open")
                           ]


def show_table_modal(n_clicks, is_open):
    if n_clicks:
        return 0, not is_open
    return dash.no_update


clear_table_selecetd_input_output = [
    # Output("map-marker", "opacity"),
    Output("datatable-interactivity", "selected_cells"),
    Output("datatable-interactivity", "active_cell"),
    Input("table-modal", "is_open")]


def clear_selected_if_closed(is_open):
    if not is_open:
        return [], None
    return dash.no_update


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
    app.callback(clear_table_selecetd_input_output)(clear_selected_if_closed)
