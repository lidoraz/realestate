import pandas as pd
from dash import html, Output, Input, State, ctx
import dash
import time

from app_map.util_layout import get_interactive_table
from app_map.utils import get_asset_points, preprocess_to_str_deals, get_geojsons, build_sidebar, get_similar_deals

clear_filter_input_outputs = [Output("price-slider", "value"),
                              Output("median-price-pct", "value"),
                              Output("date-added", "value"),
                              Output("rooms-slider", "value"),
                              Output("state-asset", "value"),
                              Input('button-clear', "n_clicks")]


def clear_filter(n_clicks):
    if n_clicks:
        return [1, 3.5], None, None, (1, 6), []
    return dash.no_update


df_all = pd.DataFrame()
config_defaults = dict()

context = dict(map_zoom=300, zoom_ts=time.time())


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
    is_triggered_by_map_bounds = len(ctx.triggered_prop_ids) == 1 and list(ctx.triggered_prop_ids)[0] == "map.bounds"
    if map_zoom != context['map_zoom'] and is_triggered_by_map_bounds:
        context['map_zoom'] = map_zoom
        past_ts = context['zoom_ts']
        context['zoom_ts'] = time.time()
        update_diff = context['zoom_ts'] - past_ts
        if update_diff < 2:
            print(update_diff)
            print("not much time has passed, Zoom changed! - No update")
            return dash.no_update
    # print(locals())
    # print(ctx.triggered_prop_ids, map_zoom)
    # sleep_bounds()


show_assets_input_output = [Output("geojson", "data"),
                            Output("datatable-interactivity", "columns"),
                            Output("datatable-interactivity", "data"),
                            Output("datatable-interactivity", "style_data_conditional"),
                            Output("fetched-assets", "children"),
                            Output("button-around", "n_clicks"),
                            Output("button-return", "n_clicks"),
                            Input("price-slider", "value"), Input("median-price-pct", "value"),
                            Input("discount-price-pct", "value"), Input('ai_pct', "value"),
                            Input("date-added", "value"), Input("date-updated", "value"),
                            Input("rooms-slider", "value"), Input('agency-check', "value"),
                            Input('parking-check', "value"), Input('balconies-check', "value"),
                            Input('state-asset', "value"),
                            Input("button-around", "n_clicks"), Input("button-return", "n_clicks"),
                            Input('marker-type', 'value'),
                            Input('map', 'bounds'), State('map', 'zoom')]


def show_assets(price_range, median_price_pct, discount_price_pct, ai_pct, date_added, date_updated,
                rooms_range, with_agency, with_parking, with_balconies, state_asset, n_clicks_around, n_clicks_return,
                marker_type,
                map_bounds, map_zoom):
    # if table_active_cell is not None:
    #     id_ = table_data[table_active_cell['row']]['id']
    #     df_f = get_asset_points(df_all, id_=id_)
    #     deal_points = get_geojsons(df_f, marker_type)
    #     return deal_points, dash.no_update, dash.no_update, dash.no_update, dash.no_update, None, None
    limit_refresh(map_zoom)
    if n_clicks_around:
        df_f = get_asset_points(df_all, map_bounds=map_bounds, limit=True)
    else:
        price_from = price_range[0] * config_defaults["price_mul"] if price_range[0] is not None else None
        price_to = price_range[1] * config_defaults["price_mul"] if price_range[1] is not None else None
        # if price_to == 3.5:
        #     price_to = 1e30
        with_agency = True if len(with_agency) else False
        with_parking = True if len(with_parking) else None
        with_balconies = True if len(with_balconies) else None
        df_f = get_asset_points(df_all, price_from, price_to,
                                median_price_pct, discount_price_pct, ai_pct,
                                date_added, date_updated, rooms_range,
                                with_agency, with_parking, with_balconies, map_bounds=map_bounds,
                                state_asset=state_asset, limit=True)
    # Can keep a list of points, if after fetch there was no new, no need to build new points, just keep them to save resources
    deal_points = get_geojsons(df_f, marker_type)
    columns, data, style_data_conditional = get_interactive_table(df_f)
    return deal_points, columns, data, style_data_conditional, len(df_f), None, None


toggle_model_input_outputs = [Output("modal", "is_open"), Output("geojson", "click_feature"),
                              Output("marker", "children"), Output("histogram", "figure"),
                              Input("geojson", "click_feature"), Input("close", "n_clicks"),
                              State("modal", "is_open")]


def toggle_modal(feature, n2, is_open):
    print(f'toggle_modal', n2, is_open)
    if feature or n2:
        props = feature['properties']
        if 'deal_id' in props:
            deal_id = feature['properties']['deal_id']
            deal = df_all.loc[deal_id]
            str_html = build_sidebar(deal)
            fig = get_similar_deals(df_all, deal, with_nadlan=config_defaults['with_nadlan'])
            return not is_open, None, str_html, fig
    return is_open, None, None, {}


focus_on_asset_input_outputs = [Output("map", "center"),
                                Output("map", "zoom"),
                                Input("datatable-interactivity", "active_cell"),
                                State("datatable-interactivity", "data"),
                                ]
def focus_on_asset(table_active_cell, table_data):
    if table_active_cell is None:
        return dash.no_update
    id_ = table_data[table_active_cell['row']]['id']
    item = get_asset_points(df_all, id_=id_).squeeze()
    return [item['lat'], item['long']], 14


def add_callbacks(app, df, config):
    global df_all, config_defaults
    df_all = df
    config_defaults = config
    app.callback(clear_filter_input_outputs)(clear_filter)
    app.callback(show_assets_input_output)(show_assets)
    app.callback(toggle_model_input_outputs)(toggle_modal)
    app.callback(focus_on_asset_input_outputs)(focus_on_asset)
