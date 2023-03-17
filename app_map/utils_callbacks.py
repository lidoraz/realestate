import numpy as np
import pandas as pd
from dash import html, Output, Input, State, ctx
import dash
import time
from app_map.util_layout import get_interactive_table, CLUSTER_MAX_ZOOM, get_marker_type_options, marker_type_default
from app_map.utils import get_asset_points, preprocess_to_str_deals, get_geojsons, build_sidebar, get_similar_deals


def handle_marker_type(marker_type, marker_types):
    # global context
    marker_type_bool = np.array(marker_types)
    marker_type_sum = marker_type_bool.sum()
    if marker_type_sum == 1:
        out_marker = get_marker_type_options()[marker_type_bool.argmax()]
    else:
        out_marker = marker_type
    return out_marker


def get_clear_filter_input_outputs(name):
    return [
        Output(f'{name}-button-clear', "n_clicks"),
        Output(f"{name}-price-median-pct-slider", "value"),
        Output(f"{name}-price-discount-pct-slider", "value"),
        Output(f"{name}-ai-price-pct-slider", "value"),
        Output(f"{name}-price-median-pct-slider-check", "value"),
        Output(f"{name}-price-discount-pct-slider-check", "value"),
        Output(f"{name}-ai-price-pct-slider-check", "value"),
        Output(f"{name}-date-added", "value"),
        Output(f"{name}-rooms-slider", "value"),
        Output(f"{name}-status-asset", "value"),
        Input(f'{name}-button-clear', "n_clicks")]


def clear_filter(n_clicks):
    if n_clicks:
        return 0, [-100, 0], [-100, 0], [-100, 0], [], [], [], None, (1, 6), []
    return dash.no_update


df_all = pd.DataFrame()
config_defaults = dict()

context = dict(map_zoom=300, zoom_ts=time.time(), marker_type=marker_type_default)


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
            return dash.no_update
    # print(locals())
    # print(ctx.triggered_prop_ids, map_zoom)
    # sleep_bounds()


def get_show_assets_input_output(name):
    return [Output(f"{name}-geojson", "data"),
            Output(f'{name}-marker-type', 'value'),
            Output(f"{name}-datatable-interactivity", "columns"),
            Output(f"{name}-datatable-interactivity", "data"),
            Output(f"{name}-datatable-interactivity", "style_data_conditional"),
            Output(f"{name}-fetched-assets", "children"),
            Output(f"{name}-button-around", "n_clicks"),
            Input(f"{name}-price-slider", "value"),
            Input(f"{name}-price-median-pct-slider", "value"),
            Input(f"{name}-price-discount-pct-slider", "value"),
            Input(f"{name}-ai-price-pct-slider", "value"),

            Input(f"{name}-price-median-pct-slider-check", "value"),
            Input(f"{name}-price-discount-pct-slider-check", "value"),
            Input(f"{name}-ai-price-pct-slider-check", "value"),
            #
            Input(f"{name}-date-added", "value"),
            Input(f"{name}-date-updated", "value"),
            Input(f"{name}-rooms-slider", "value"),
            Input(f'{name}-agency-check', "value"),
            Input(f'{name}-parking-check', "value"),
            Input(f'{name}-balconies-check', "value"),
            Input(f'{name}-status-asset', "value"),
            Input(f'{name}-asset-type', "value"),
            Input(f"{name}-button-around", "n_clicks"),
            Input(f'{name}-marker-type', 'value'),
            Input(f'{name}-big-map', 'bounds'),
            State(f'{name}-big-map', 'zoom'),
            State(f"{name}-datatable-interactivity", "active_cell")]


def show_assets(price_range,
                price_median_pct_range, price_discount_pct_range, price_ai_pct_range,
                is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range,
                date_added, date_updated,
                rooms_range, with_agency, with_parking, with_balconies, asset_status, asset_type, n_clicks_around,
                marker_type,
                map_bounds, map_zoom, active_cell=None):
    print("marker_type", marker_type)
    with_agency = True if len(with_agency) else False
    with_parking = True if len(with_parking) else None
    with_balconies = True if len(with_balconies) else None
    is_price_median_pct_range = len(is_price_median_pct_range) > 0
    is_price_discount_pct_range = len(is_price_discount_pct_range) > 0
    is_price_ai_pct_range = len(is_price_ai_pct_range) > 0
    limit_refresh(map_zoom)
    if active_cell:
        return dash.no_update
    if n_clicks_around:
        df_f = get_asset_points(df_all, map_bounds=map_bounds, limit=True)
    else:
        # special case - max over 10M
        if price_range[0] == config_defaults['price-max'] and price_range[0] == price_range[1]:
            price_from = config_defaults['price-max'] * config_defaults["price_mul"]
            price_to = np.inf
        else:
            price_from = price_range[0] * config_defaults["price_mul"]
            price_to = price_range[1] * config_defaults["price_mul"]

        df_f = get_asset_points(df_all, price_from, price_to,
                                price_median_pct_range, price_discount_pct_range, price_ai_pct_range,
                                is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range,
                                date_added, date_updated, rooms_range,
                                with_agency, with_parking, with_balconies, map_bounds=map_bounds,
                                asset_status=asset_status, asset_type=asset_type, limit=True)
    # Can keep a list of points, if after fetch there was no new, no need to build new points, just keep them to save resources
    out_marker = handle_marker_type(marker_type,
                                    [is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range])
    deal_points = get_geojsons(df_f, out_marker)
    columns, data, style_data_conditional = get_interactive_table(df_f)

    return deal_points, out_marker, columns, data, style_data_conditional, len(df_f), None


def get_toggle_model_input_outputs(name):
    return [Output(f"{name}-geojson", "click_feature"),  # output none to reset button for re-click
            Output(f"{name}-modal", "is_open"),
            Output(f"{name}-modal-title", "children"),
            Output(f"{name}-marker", "children"),
            Output(f"{name}-histogram", "figure"),
            Input(f"{name}-geojson", "click_feature")]


def toggle_modal(feature):
    if feature:
        props = feature['properties']
        if 'deal_id' in props:
            deal_id = feature['properties']['deal_id']
            deal = df_all.loc[deal_id]
            title_modal, str_html = build_sidebar(deal)
            fig = get_similar_deals(df_all, deal, with_nadlan=config_defaults['with_nadlan'])
            return None, True, title_modal, str_html, fig
    return dash.no_update


def get_focus_on_asset_input_outputs(name):
    return [Output(f"{name}-big-map", "center"),
            Output(f"{name}-big-map", "zoom"),
            Output(f"{name}-map-marker", "opacity"),
            Output(f"{name}-map-marker", "position"),
            Input(f"{name}-datatable-interactivity", "active_cell"),
            State(f"{name}-datatable-interactivity", "data"),
            ]


# dl.Marker(position=[31.7, 32.7], opacity=0, id='map-marker')
def focus_on_asset(table_active_cell, table_data):
    if table_active_cell is None:
        return dash.no_update
    id_ = [x for x in table_data if x['id'] == table_active_cell['row_id']][0]['id']
    item = get_asset_points(df_all, id_=id_).squeeze()
    position = [item['lat'], item['long']]
    return position, CLUSTER_MAX_ZOOM + 1, 0.75, position


def get_show_table_input_output(name):
    return [Output(f"{name}-table-toggle", "n_clicks"),
            Output(f"{name}-table-modal", "is_open"),
            Input(f"{name}-table-toggle", "n_clicks"),
            State(f"{name}-table-modal", "is_open")
            ]


def show_table_modal(n_clicks, is_open):
    if n_clicks:
        return 0, not is_open
    return dash.no_update


def get_clear_table_selecetd_input_output(name):
    return [
        # Output("map-marker", "opacity"),
        Output(f"{name}-datatable-interactivity", "selected_cells"),
        Output(f"{name}-datatable-interactivity", "active_cell"),
        Input(f"{name}-table-modal", "is_open")]


def clear_selected_if_closed(is_open):
    if not is_open:
        return [], None
    return dash.no_update


def get_disable_range_input_outputs(name):
    return [Output(f"{name}-price-median-pct-slider", "disabled"),
            Output(f"{name}-price-discount-pct-slider", "disabled"),
            Output(f"{name}-ai-price-pct-slider", "disabled"),
            Input(f"{name}-price-median-pct-slider-check", "value"),
            Input(f"{name}-price-discount-pct-slider-check", "value"),
            Input(f"{name}-ai-price-pct-slider-check", "value"),
            ]


def disable_range_sliders(is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range):
    is_price_median_pct_range = len(is_price_median_pct_range) == 0
    is_price_discount_pct_range = len(is_price_discount_pct_range) == 0
    is_price_ai_pct_range = len(is_price_ai_pct_range) == 0
    return is_price_median_pct_range, is_price_discount_pct_range, is_price_ai_pct_range


def get_toggle_cluster_input_outputs(name):
    return [
        Output(f"{name}-geojson", "cluster"),
        Input(f"{name}-cluster-check", "value")
    ]


def toggle_cluster(cluster_check):
    return [len(cluster_check) > 0]


def add_callbacks(app, df, config):
    global df_all, config_defaults
    config_defaults = config
    df_all = df
    name = config_defaults['name']
    app.callback(get_clear_filter_input_outputs(name))(clear_filter)
    app.callback(get_show_assets_input_output(name))(show_assets)
    app.callback(get_toggle_model_input_outputs(name))(toggle_modal)
    app.callback(get_focus_on_asset_input_outputs(name))(focus_on_asset)
    app.callback(get_disable_range_input_outputs(name))(disable_range_sliders)
    app.callback(get_show_table_input_output(name))(show_table_modal)
    app.callback(get_toggle_cluster_input_outputs(name))(toggle_cluster)
    app.callback(get_clear_table_selecetd_input_output(name))(clear_selected_if_closed)
