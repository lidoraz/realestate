import dash
import dash_bootstrap_components as dbc
import numpy as np
from dash import dcc

# from app_map.utils import *
# from app_map.util_layout import get_layout
# from app_map.utils_callbacks import add_callbacks
from dash import html, Output, Input, State, ctx

import pandas as pd

from app_map.util_layout import get_page_menu
from app_map.utils import get_file_from_remote
from stats.daily_fetch_nadlan_stats import get_plot_agg_by_feat
from stats.plots import create_percentiles_per_city_f
from stats.calc_plots import run_for_cities, create_ratio
from stats.plots import plot_scatter_f

# df_all = get_df_with_prod(is_prod, filename="../resources/yad2_rent_df.pk")
# df_all = app_preprocess_df(df_all)
config_figure_disable_all = {'displayModeBar': False,
                             'scrollZoom': False}


def preprocess(df):
    df['price_meter'] = df['price'] / df['square_meter_build']
    df['price_meter'] = df['price_meter'].replace(np.inf, np.nan)
    df.sort_values('price_meter', ascending=False)
    return df


type_ = 'rent'
fname = 'df_log_{}.pk'
df_rent = get_file_from_remote(fname.format("rent"))
df_forsale = get_file_from_remote(fname.format("forsale"))

dict_df_agg_nadlan_all = get_file_from_remote("dict_df_agg_nadlan_all.pk")
dict_df_agg_nadlan_new = get_file_from_remote("dict_df_agg_nadlan_new.pk")
dict_df_agg_nadlan_old = get_file_from_remote("dict_df_agg_nadlan_old.pk")

dict_combined = dict(ALL=dict_df_agg_nadlan_all,
                     NEW=dict_df_agg_nadlan_new,
                     OLD=dict_df_agg_nadlan_old)

cities = df_forsale['city'].value_counts()
cities = cities[cities > 50].sort_index()

# label=f'{city} ({cnt:,.0f})'
additional_all_key = [dict(label="בכל הארץ", value="ALL")]
cities_options = additional_all_key + [dict(label=f'{city}', value=city) for city, cnt in
                                       cities.items()]
# Removing first key:
dict_df_agg_keys = sorted([k for k in dict_df_agg_nadlan_all.keys() if k != 'ALL'])
cities_long_term_options = additional_all_key + [dict(label=f'{city}', value=city) for city in dict_df_agg_keys]
df_rent = preprocess(df_rent)
df_forsale = preprocess(df_forsale)

date_df = df_rent['date_updated'].max().date()
str_update = f'מעודכן ל-{date_df}'
days_back = 30
min_samples = 200


# def get_bars():
#     plot_ratio_f(res, type_)

def get_scatter(df, type_, min_samples):
    res_ratio = create_ratio(df, days_back=days_back, min_samples=min_samples)
    fig = plot_scatter_f(df, res_ratio, type_)
    fig.update_layout(template="plotly_dark")
    modeBarButtonsToRemove = ['select2d', 'lasso2d']
    return dcc.Graph(id=f'scatter-ratio-{type_}', figure=fig,
                     config={
                         'modeBarButtonsToRemove': modeBarButtonsToRemove,
                         # 'displayModeBar': False,
                         'scrollZoom': False}
                     )


def _gen_multi_html(figs):
    n_cols = 4
    n_rows = len(figs) // n_cols
    import uuid
    [fig.update_layout(template="plotly_dark", dragmode=False) for fig in figs]
    graphs = [dbc.Row([dbc.Col(
        dcc.Graph(id=f'graph-{uuid.uuid4()}-city-{i * j + j}', figure=figs[i * n_cols + j],
                  config=config_figure_disable_all),
        style=dict(margin="10px")) for j in range(n_cols)])

        for i in range(n_rows)]
    return graphs


def _get_multi_price(df, type_, only_figs=True):
    days_back = 7
    figs = run_for_cities(df, type_, n_cities=8, resample_rule=f'{days_back}D', use_median=True)
    if only_figs:
        return figs
    graphs = _gen_multi_html(figs)
    return graphs


def _get_single_price(df, type_, city, col_name):
    days_back = 7
    fig = create_percentiles_per_city_f(df, city=city, type_=type_, resample_rule=f'{days_back}D', col_name=col_name,
                                        use_median=True)
    fig.update_layout(template="plotly_dark", dragmode=False)
    return dcc.Graph(id=f'graph-single-price-{type_}-{city}', figure=fig,
                     config=config_figure_disable_all)


def get_single_price(city=None, col_name='price'):
    return [dbc.Col(_get_single_price(df_forsale, "sale", city, col_name)),
            dbc.Col(_get_single_price(df_rent, "rent", city, col_name))]


# def get_multi_price_parts():
#     return [
#         dbc.Row(dbc.Col(html.H2("מכירה - תנועות בערים נבחרות של המחיר בזמן, לפי אחוזונים"))),
#         *_get_multi_price(df_forsale, "forsale"),
#         dbc.Row(dbc.Col(html.H2("שכירות - תנועות בערים נבחרות של המחיר בזמן, לפי אחוזונים"))),
#         *_get_multi_price(df_rent, "rent"),
#     ]


def get_multi_price_by_side():
    figs1 = _get_multi_price(df_forsale, "forsale", only_figs=True)
    figs2 = _get_multi_price(df_rent, "rent", only_figs=True)
    figs = [item for pair in zip(figs1, figs2) for item in pair]
    graphs = _gen_multi_html(figs)
    cont = [dbc.Row(dbc.Col(html.H3("תנועות בערים נבחרות של המחיר בזמן, לפי אחוזונים"))),
            dbc.Row(graphs)]
    return cont


# MAIN NADLAN # DEALS
fig = get_file_from_remote("fig_timeline_new_vs_old.pk")
fig.update_layout(legend=dict(x=0, y=1))

modeBarButtonsToRemove = ['select2d', 'lasso2d']
graph_obj = dcc.Graph(id=f'timeline-new-vs-old', figure=fig,
                      config={
                          'modeBarButtonsToRemove': modeBarButtonsToRemove,
                          # 'displayModeBar': False,
                          'scrollZoom': False}
                      )


# https://community.plotly.com/t/how-to-log-client-ip-addresses/6613
def get_dash(server):
    app = dash.Dash(server=server, external_stylesheets=[dbc.themes.CYBORG],  # dbc.themes.DARKLY
                    title="Analytics", url_base_pathname='/analytics/')

    app.layout = html.Div(
        [
            dbc.Row([dbc.Col(get_page_menu()), dbc.Col(html.H1("Advanced Analytics"), style=dict(direction="ltr"))]),
            dbc.Row(dbc.Col(html.H6(str_update))),
            dbc.Row(dbc.Col(html.H3("מכירות דירות מול השפעת הריבית"))),
            dbc.Row(dbc.Col(graph_obj)),

            dbc.Row(dbc.Col()),
            dbc.Row(dbc.Col(html.H3("פיזור הביקוש מול ההיצע"))),
            dbc.Row(dbc.Col(html.Span(
                "פיזור בין הזמן החציוני לדירה להפוך ללא רלוונטית מול מדד ההיצע - כלומר כמה דירות פנויות יש מול דירות שכבר לא רלוונטיות"))),
            dbc.Row(
                [dbc.Col(
                    [html.H4("SALE", style={"background-color": "#1e81b0"}),
                     get_scatter(df_forsale, 'forsale', 300)], width=6, xs=12),
                    dbc.Col([html.H4("RENT", style={"background-color": "#e28743"}),
                             get_scatter(df_rent, 'rent', 200)], width=6, xs=12)],
                className="analysis-main-multi-grid"),
            # dbc.Row(),
            # dbc.Row(dbc.Col(html.Span("בכל הארץ, כל גרף מייצג אחוזון, כאשר האמצע הוא החציון"))),
            # dbc.Row(get_single_price(None), ),
            # dbc.Row(dbc.Col()),
            html.H3("תנועות המחיר בזמן"),
            dbc.Row([
                dbc.Col([
                    html.H5("בטווח ארוך"),
                    html.Label("בחר עיר", className="col-sm-2 col-form-label"),
                    # dcc.Dropdown(
                    #     cities_long_term_options,
                    #     [],
                    #     placeholder="multi",
                    #     multi=True,
                    #     id="city-long-term-select-multi",
                    #     # className="form-select",
                    #     style=dict(width="300px", color="black")
                    # ),
                    dbc.Select(id="city-long-term-select", options=cities_long_term_options,
                               value="ALL",
                               style=dict(width="200px", direction="ltr"),
                               className="form-select"),
                    html.Label("מחיר לפי", className="col-sm-2 col-form-label"),
                    dbc.RadioItems(
                        options=[
                            {"label": "מחיר", "value": "price_declared"},
                            {"label": "מחיר למ״ר", "value": "price_square_meter"},
                        ],
                        value="price_declared",
                        inline=True,
                        id="metric-long-term-select",
                        labelClassName="btn btn-outline-primary",
                        className="btn-group",
                        inputClassName="btn-check"
                    ),
                    html.Label("מצב הנכס", className="col-sm-2 col-form-label"),
                    dbc.RadioItems(
                        options=[
                            {"label": "הכל", "value": "ALL"},
                            {"label": "חדש", "value": "NEW"},
                            {"label": "יד שניה", "value": "OLD"},
                            {"label": "השוואה", "value": "CMP"}
                        ],
                        value="ALL",
                        inline=True,
                        id="year-built-long-term-select",
                        labelClassName="btn btn-outline-primary",
                        className="btn-group",
                        inputClassName="btn-check"
                    ),
                ], className="form-group"),
                dbc.Col([html.Div(id="pct-stats-long-term", style=dict(display="flex", margin="10px")),
                         html.Div(id='longterm-output')], width=9, md=12, sm=12, xs=12)
            ]),
            dbc.Alert(
                "asfsaf",
                id="alert-auto",
                is_open=False,
                color="danger",
                # duration=10_000,
            ),
            dbc.Row(dbc.Col()),
            # dbc.Row(),
            dbc.Row(dbc.Col([dbc.Select(id="city-select", options=cities_options,
                                        value="ALL",
                                        style=dict(width="200px", direction="ltr")),
                             dbc.RadioItems(
                                 options=[
                                     {"dlabel": "מחיר", "value": "price"},
                                     {"label": "מחיר למ״ר", "value": "price_meter"},
                                 ],
                                 value="price",
                                 inline=True,
                                 id="metric-select",
                             ),
                             ])),
            dbc.Row(dbc.Col(html.H5("בטווח הקצר"))),
            dbc.Row(get_single_price(), id="city-output"),
            *get_multi_price_by_side(),
            # dbc.Row(
            #     [
            #         dbc.Col(html.Div("One of three columns")),
            #         dbc.Col(html.Div("One of three columns")),
            #         dbc.Col(html.Div("One of three columns")),
            #     ]
            # ),
        ],
        className="analysis-main",

    )

    @app.callback(

        Output("city-output", "children"),
        Input("city-select", "value"),
        Input("metric-select", "value"),
    )
    def get_by_city(city, col_name):
        if city == "ALL":
            city = None
        if col_name not in ['price', 'price_meter']:
            col_name = 'price'
        children = get_single_price(city, col_name)
        return children

    @app.callback(
        Output("pct-stats-long-term", "children"),
        Output("longterm-output", "children"),
        Output("alert-auto", "children"),
        Output("alert-auto", "is_open"),
        Input("city-long-term-select", "value"),
        Input("metric-long-term-select", "value"),
        Input("year-built-long-term-select", "value")
    )
    def get_by_city_long_term(city, col_name, asset_year):
        from app_map.utils import create_pct_bar
        if asset_year != 'CMP':
            dict_df_agg = dict_combined[asset_year]
            df_agg = dict_df_agg[city]
            print(df_agg.columns)
            fig = get_plot_agg_by_feat(df_agg, city, col_name)
            # HERE IT WILL SHOW AS USUAL
        else:
            df_agg = dict_combined["ALL"][city]
            df_agg_new = dict_combined["NEW"][city]
            df_agg_old = dict_combined["OLD"][city]
            fig = get_plot_agg_by_feat([df_agg, df_agg_new, df_agg_old], city, col_name)
        html_pct_bar = create_pct_bar(df_agg, col_name)
        # is it CMP - CMP NEW VS OLD, and ALL:

        #     # if asset_year not in ['ALL', 'NEW', 'OLD', 'CMP']:
        #     #     asset_year = 'ALL'
        #     if city == "ALL":
        #         city = None
        #     # if col_name not in ['price', 'price_meter']:
        #     #     col_name = 'price_declared'
        #     if col_name == 'price':
        #         col_name = 'price_declared'
        #     if col_name == 'price_meter':
        #         col_name = 'price_square_meter'
        #     if asset_year != 'CMP':
        # if city == 'ALL' or city is None:
        #     if asset_year != 'CMP':
        #         df_agg = dict_df_agg['ALL']
        # else:
        #     if city not in dict_df_agg:
        #         alert_txt = "לא נמצא"
        #         return dash.no_update, dash.no_update, alert_txt, True
        #     df_agg = dict_df_agg[city]
        # dict_df_agg = dict_combined[asset_year]
        # print(city, col_name, asset_year)

        fig.update_layout(template="plotly_dark", dragmode=False)
        graph = dcc.Graph(id=f'graph-long-price-{type_}-{city}', figure=fig,
                          config=config_figure_disable_all)
        return html_pct_bar, graph, "", False

    return server, app


if __name__ == '__main__':
    _, app = get_dash(True)
    app.run_server(debug=True, port=8047)
