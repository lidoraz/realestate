import numpy as np
import os
from dash import html, Output, Input, State, ctx
import dash
import time
from app_map.util_layout import get_interactive_table, CLUSTER_MAX_ZOOM, marker_type_options, btn_color
from app_map.utils import get_asset_points, get_cords_by_city, get_cords_by_id, get_geojsons, build_sidebar, \
    get_similar_deals, \
    address_to_lat_long_google
import logging
import json
from flask import request

LOGGER = logging.getLogger()

config_defaults = dict()
config_defaults["last_asset_id_input"] = "?"
CLEAR_BUTTON_SELECTED_ASSET_COLOR = "secondary"
FETCH_LIMIT = 150


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


def _process_keyword(df, keyword, search_submit_nclicks):
    res = {"search-submit": 0}
    if not search_submit_nclicks or not len(keyword):
        return res
        pos = get_cords_by_city(df, keyword)
        if pos:
            res.update({"big-map_center": pos, "big-map_zoom": CLUSTER_MAX_ZOOM, "search-input_invalid": False,
                        "search-input_value": keyword,
                        "button-clear_n_clicks": 0})
            return res
    r = get_cords_by_id(df, keyword, 14) or address_to_lat_long_google(keyword)  # Use maps api to get location
    if r:
        res.update({"big-map_center": (r['lat'], r['long']), "big-map_zoom": r['zoom']})
        return res
    res.update({"search-input_invalid": True})
    return res


def _process_asset_url(df, url_path, clear_button_n_clicks):
    output = {}
    is_found_asset_by_search = False
    asset_id = _parse_search(url_path).get('asset_id')
    if clear_button_n_clicks == 0 and asset_id:
        is_found_asset_by_search = (df['id'] == asset_id).any()
        LOGGER.info(f"search {asset_id=}, {is_found_asset_by_search=}")
        if not is_found_asset_by_search:
            if asset_id != config_defaults["last_asset_id_input"]:
                config_defaults["last_asset_id_input"] = asset_id
                LOGGER.info("main-alert_is_open: True")
                output.update({"main-alert_is_open": True})
            asset_id = None
        else:
            r = get_cords_by_id(df, asset_id, 14)
            output.update(
                {"big-map_center": [r['lat'], r['long']], "big-map_zoom": r['zoom'], "search-input_invalid": False,
                 # "search-input_value": asset_id,
                 "button-clear_color": "info",
                 "button-clear_n_clicks": 0})
    if clear_button_n_clicks:
        asset_id = None
        output.update({"button-clear_color": "primary"})
        print("clear_button_n_clicks clicked!")
    return output, asset_id, is_found_asset_by_search


def _process_table(df,
                   n_clicks_clear_marker,
                   table_modal_is_open,
                   table_active_cell,
                   table_data):
    output = {}
    if n_clicks_clear_marker or (not table_modal_is_open and table_active_cell):
        output.update({"datatable-interactivity_selected_cells": [],
                       "datatable-interactivity_active_cell": None,
                       "clear-cell-button_n_clicks": 0})
    if table_active_cell:
        asset_id = [x for x in table_data if x['id'] == table_active_cell['row_id']][0]['id']
        r = get_cords_by_id(df, asset_id, 16)
        output.update({"big-map_center": [r['lat'], r['long']],
                       "big-map_zoom": CLUSTER_MAX_ZOOM + 1})
    return output


show_assets_input_output = [Output("geojson", "data"),
                            Output("main-alert", "is_open"),
                            Output("datatable-interactivity", "columns"),
                            Output("datatable-interactivity", "data"),
                            Output("datatable-interactivity", "style_data_conditional"),
                            Output("fetched-assets", "children"),
                            ####################
                            Output("big-map", "center"),
                            Output("big-map", "zoom"),
                            # Output("map-marker", "opacity"),
                            # Output("map-marker", "position"),
                            Output("datatable-interactivity", "selected_cells"),
                            Output("datatable-interactivity", "active_cell"),
                            Output("clear-cell-button", "n_clicks"),
                            Output("search-input", "invalid"),
                            Output("search-input", "value"),
                            Output('button-clear', "n_clicks"),
                            # Output("button-around", "n_clicks"),
                            Output("updated-at", "children"),
                            Output('search-submit', 'n_clicks'),
                            Output("button-clear", "color"),
                            ######## OPTIONS INPUTS ##
                            Input("price-slider", "value"),
                            Input("max-avg-price-meter-slider", "value"),
                            Input("min-meter-slider", "value"),

                            Input("price-median-pct-slider", "value"),
                            Input("price-discount-pct-slider", "value"),
                            Input("ai-price-pct-slider", "value"),
                            Input("price-median-pct-slider-check", "value"),
                            Input("price-discount-pct-slider-check", "value"),
                            Input("ai-price-pct-slider-check", "value"),
                            Input("date-added", "value"),
                            Input("date-updated", "value"),
                            Input("rooms-slider", "value"),
                            Input("floor-slider", "value"),
                            Input('agency-check', "value"),
                            Input('parking-check', "value"),
                            Input('balconies-check', "value"),
                            Input('elevator-check', "value"),
                            Input('asset-status', "value"),
                            Input('asset-type', "value"),
                            Input('marker-type', 'value'),
                            Input('search-submit', 'n_clicks'),
                            State('search-input', 'value'),
                            ######## OPTIONS INPUTS ##
                            Input('big-map', 'bounds'),
                            State('big-map', 'zoom'),
                            #####
                            Input("path-location", "href"),
                            Input('button-clear', "n_clicks"),
                            Input("clear-cell-button", "n_clicks"),
                            Input("table-modal", "is_open"),
                            Input("datatable-interactivity", "active_cell"),
                            State("datatable-interactivity", "data"),
                            # Input("find-geolocation", "n_clicks"),
                            # Input("geolocation", "position")
                            ]


# Functions:
#  1. Focus on asset that has been selected with the table using the map center function
#  2. handles the search bar for a city and its reset button
#  3. Parse url search if asset is selected from the url
#  4. filter and get out assets!

def show_assets(price_range, max_avg_price_meter,
                min_meter,
                price_median_pct_range, price_discount_pct_range, price_ai_pct_range,
                is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range,
                date_added, date_updated,
                rooms_range, floor_range,
                with_agency, with_parking, with_balconies, with_elevator,
                asset_status, asset_type,
                marker_type, search_submit_nclicks, search_input,
                ## end inputs
                map_bounds, map_zoom,
                url_path, clear_button_n_clicks, n_clicks_clear_marker, table_modal_is_open,
                table_active_cell, table_data):
    conf = get_context_by_rule()
    nthg = dash.no_update
    # dbc.Row(dbc.Label(id="find-geolocation"),
    #                         dcc.Geolocation(id="geolocation"),
    output = {
        "geojson_data": nthg,
        "main-alert_is_open": nthg,
        "datatable-interactivity_columns": nthg,
        "datatable-interactivity_data": nthg,
        "datatable-interactivity_style_data_conditional": nthg,
        "fetched-assets_children": nthg,

        "big-map_center": nthg,
        "big-map_zoom": nthg,
        "datatable-interactivity_selected_cells": nthg,
        "datatable-interactivity_active_cell": nthg,
        "clear-cell-button_n_clicks": nthg,
        "search-input_invalid": nthg,
        "search-input_value": nthg,
        "button-clear_n_clicks": nthg,
        "updated-at_children": nthg,
        "search-submit": nthg,
        "button-clear_color": nthg
    }
    # check submit to make search instantly show assets when clicked
    if search_submit_nclicks == 0 and limit_refresh(map_zoom):
        return dash.no_update

    # if geolocation_n_clicks > 0 and 'lat' in geolocation and 'lon' in geolocation:
    #     print(f"{geolocation=}")
    #     output["big-map_center"] = geolocation['lat'], geolocation['lon']
    #     output["big-map_zoom"] = 14

    df = conf['func_data']()
    output_changes, asset_id, is_found_asset_by_search = _process_asset_url(df, url_path, clear_button_n_clicks)
    output.update(output_changes)
    output.update(_process_table(df,
                                 n_clicks_clear_marker,
                                 table_modal_is_open,
                                 table_active_cell,
                                 table_data))
    output.update(_process_keyword(df, search_input, search_submit_nclicks))

    if is_found_asset_by_search:
        df_f = get_asset_points(df, id_=asset_id)
    else:
        LOGGER.debug(f"{marker_type=}")
        # Used to filter out points not in the city if input has a city value
        city = search_input if len(search_input) and get_cords_by_city(df, search_input) else None
        asset_filter_params = dict(
            price_from=price_range[0] * conf["price_mul"],
            # when max price is at limits, allow prices above it
            price_to=np.inf if price_range[0] == conf['price-max'] else price_range[1] * conf["price_mul"],
            max_avg_price_meter=np.inf if max_avg_price_meter == 50_000 else max_avg_price_meter,
            min_meter=min_meter,
            city=city,
            # remove limits, ADD TO CONF
            rooms_range=rooms_range,
            floor_range=floor_range,
            price_median_pct_range=price_median_pct_range,
            price_discount_pct_range=price_discount_pct_range,
            price_ai_pct_range=price_ai_pct_range,
            is_price_median_pct_range=len(is_price_median_pct_range) > 0,
            is_price_discount_pct_range=len(is_price_discount_pct_range) > 0,
            is_price_ai_pct_range=len(is_price_ai_pct_range) > 0,
            date_added_days=date_added,
            date_updated=date_updated,
            with_agency=True if len(with_agency) else False,
            with_parking=True if len(with_parking) else None,
            with_balconies=True if len(with_balconies) else None,
            with_elevator=True if len(with_elevator) else None,
            asset_status=asset_status,
            asset_type=asset_type,
            map_bounds=map_bounds if city is None else None
        )
        df_f = get_asset_points(df, **asset_filter_params)

    # Can keep a list of points, if after fetch there was no new, no need to build new points, just keep them to save resources
    n_rows = len(df_f)
    df_f = df_f[:FETCH_LIMIT]
    deal_points = get_geojsons(df_f, marker_type)
    columns, data, style_data_conditional = get_interactive_table(df_f)
    days_b = df["date_updated_d"].min()
    bot_html = f'נמצאו {n_rows:,.0f} נכסים {"" if (-1 if np.isnan(days_b) else days_b) == 0 else " .."}'
    updated_at_html = [f"מעודכן ל-{df_f['date_updated'].max().date()}"]
    output.update({
        "geojson_data": deal_points,
        "datatable-interactivity_columns": columns,
        "datatable-interactivity_data": data,
        "datatable-interactivity_style_data_conditional": style_data_conditional,
        "fetched-assets_children": bot_html,
        "updated-at_children": updated_at_html,
    }
    )
    return list(output.values())


toggle_model_input_outputs = [Output("geojson", "click_feature"),  # output none to reset button for re-click
                              Output("modal", "is_open"),
                              Output("modal-title", "children"),
                              Output("modal-body", "children"),
                              Output('data-store', 'data'),
                              Input("geojson", "click_feature")]


def toggle_modal(feature):
    if feature:
        props = feature['properties']
        if 'deal_id' in props:
            conf = get_context_by_rule()
            deal_id = feature['properties']['deal_id']
            deal = conf['func_data']().loc[deal_id]
            fig = get_similar_deals(conf['func_data'](), deal, with_nadlan=conf['with_nadlan'])
            t0 = time.time()
            title_modal, str_html = build_sidebar(deal, fig)
            logging.debug("Compute TIME   ---->", time.time() - t0)
            return None, True, title_modal, str_html, dict(deal_data=deal.to_json())
    return dash.no_update


def gen_plots_lazy(data_store):
    deal = data_store.get("deal_data")
    if deal:
        from app_map.utils import get_sidebar_plots
        html_plots = get_sidebar_plots(json.loads(deal))
        return [html_plots]
    return dash.no_update


gen_plots_lazy_input_outputs = [Output("modal-plots-cont", "children"),
                                Input("data-store", 'data')]

focus_on_asset_input_outputs = [Output("big-map", "center"),
                                Output("big-map", "zoom"),
                                Output("map-marker", "opacity"),
                                Output("map-marker", "position"),
                                Output("datatable-interactivity", "selected_cells"),
                                Output("datatable-interactivity", "active_cell"),
                                Output("clear-cell-button", "n_clicks"),
                                Output("search-input", "invalid"),
                                Output("search-input", "value"),
                                Output('button-clear', "n_clicks"),
                                ]


def parse_params(search):
    return dict(x.split('=') for x in search.split('&')) if search else {}


def _parse_search(url):
    split_by_question = url.split("?")
    os.environ["BASE_URL_PATH"] = split_by_question[0]  # set base path
    if len(split_by_question) == 1:
        return {}
    params_url = split_by_question[1]
    if '=' not in params_url:
        return {'asset_id': params_url}
    params = parse_params(params_url)
    asset_id = params.get('asset_id')
    user_id = params.get('user_id')
    print(f"{asset_id=}, {user_id=}")
    return params


show_table_input_output = [Output("table-toggle", "n_clicks"),
                           Output("table-modal", "is_open"),
                           Input("table-toggle", "n_clicks"),
                           State("table-modal", "is_open")]


def show_table_modal(n_clicks, is_open):
    if n_clicks:
        return 0, not is_open
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


change_polygons_type_input_outputs = [Output(component_id='geogson_', component_property='data'),
                                      Input(component_id='polygon-select-radio', component_property='value'),
                                      Input("big-map", "zoom"),
                                      Input("polygon_toggle", "value")]


def change_polygons_type(value, zoom, toggle):
    # use state to avoid reload json when zoom has not changed enough to pass zoom level
    from app_map.dashboard_neighborhood import get_points_by
    if not len(toggle):
        return [None]
    json_points, _ = get_points_by(value, zoom, "pct_chg")
    return [json_points]


def add_callbacks(app, config):
    # global df_all, config_defaults
    # df_all = df
    name = config['name']
    config_defaults[name] = config
    # app.callback(clear_filter_input_outputs, prevent_initial_call=True)(clear_filter)
    app.callback(show_assets_input_output)(show_assets)
    app.callback(toggle_model_input_outputs)(toggle_modal)
    app.callback(disable_range_input_outputs)(disable_range_sliders)
    app.callback(show_table_input_output)(show_table_modal)
    app.callback(toggle_cluster_input_outputs)(toggle_cluster)
    app.callback(gen_plots_lazy_input_outputs)(gen_plots_lazy)
    app.callback(change_polygons_type_input_outputs)(change_polygons_type)  # polygons
