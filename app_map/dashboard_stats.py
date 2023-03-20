import dash
import dash_bootstrap_components as dbc
import numpy as np
from dash import dcc
import pickle
from smart_open import open as s_open

# from app_map.utils import *
# from app_map.util_layout import get_layout
# from app_map.utils_callbacks import add_callbacks
from dash import html, Output, Input, State, ctx

import pandas as pd

from app_map.util_layout import get_page_menu
from app_map.utils import get_df_with_prod
from stats.daily_fetch_nadlan_stats import get_plot_agg_by_feat
from stats.plots import create_percentiles_per_city_f
from stats.calc_plots import run_for_cities, create_ratio
from stats.plots import plot_scatter_f

# df_all = get_df_with_prod(is_prod, filename="../resources/yad2_rent_df.pk")
# df_all = app_preprocess_df(df_all)
config_figure_disable_all = {'displayModeBar': False,
                             'scrollZoom': False}

def get_from_s3_any(filename):
    s3_file = "https://real-estate-public.s3.eu-west-2.amazonaws.com/resources/{filename}"
    with s_open(s3_file.format(filename=filename), "rb") as f:
        # with open("resources/fig_timeline_new_vs_old.pk", "rb") as f:
        file = pickle.load(f)
        return file

def preprocess(df):
    df['price_meter'] = df['price'] / df['square_meter_build']
    df['price_meter'] = df['price_meter'].replace(np.inf, np.nan)
    df.sort_values('price_meter', ascending=False)
    return df


type_ = 'rent'
fname = 'df_log_{}.pk'
df_rent = get_df_with_prod(fname.format("rent"))
df_forsale = get_df_with_prod(fname.format("forsale"))

dict_df_agg = get_from_s3_any("dict_df_agg_nadlan.pk")

cities = df_forsale['city'].value_counts()
cities = cities[cities > 50].sort_index()

# label=f'{city} ({cnt:,.0f})'
cities_options = [dict(label="בכל הארץ", value="ALL")] + [dict(label=f'{city}', value=city) for city, cnt in
                                                          cities.items()]

cities_long_term_options = [dict(label=f'{city}', value=city) for city in
                            sorted(dict_df_agg.keys())]
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
fig = get_from_s3_any("fig_timeline_new_vs_old.pk")
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
    app = dash.Dash(server=server, external_stylesheets=[dbc.themes.CYBORG],
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
                     get_scatter(df_forsale, 'forsale', 300)]),
                    dbc.Col([html.H4("RENT", style={"background-color": "#e28743"}),
                             get_scatter(df_rent, 'rent', 200)])],
                className="analysis-main-multi-grid"),
            dbc.Row(dbc.Col(html.H3("תנועות המחיר בזמן"))),
            dbc.Row(dbc.Col(html.Span("בכל הארץ, כל גרף מייצג אחוזון, כאשר האמצע הוא החציון"))),
            # dbc.Row(get_single_price(None), ),
            dbc.Row(dbc.Col(html.H5("שינוי בטווח ארוך"))),
            dbc.Row(dbc.Col([dbc.Select(id="city-long-term-select", options=cities_long_term_options,
                                        value="ALL",
                                        style=dict(width="200px", direction="ltr")),
                             dbc.RadioItems(
                                 options=[
                                     {"label": "מחיר", "value": "price"},
                                     {"label": "מחיר למ״ר", "value": "price_meter"},
                                 ],
                                 value="price",
                                 inline=True,
                                 id="metric-long-term-select",
                             ),
                             ])),
            dbc.Row(dbc.Col(id='longterm-output')),
            dbc.Row(dbc.Col([dbc.Select(id="city-select", options=cities_options,
                                        value="ALL",
                                        style=dict(width="200px", direction="ltr")),
                             dbc.RadioItems(
                                 options=[
                                     {"label": "מחיר", "value": "price"},
                                     {"label": "מחיר למ״ר", "value": "price_meter"},
                                 ],
                                 value="price",
                                 inline=True,
                                 id="metric-select",
                             ),
                             ])),
            dbc.Row(dbc.Col(html.H5("שינוי בטווח הקצר"))),
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
        print(list(dict_df_agg.keys()))
        fig = get_plot_agg_by_feat(dict_df_agg, city, col_name)
        fig.update_layout(template="plotly_dark")
        graph = dcc.Graph(id=f'graph-long-price-{type_}-{city}', figure=fig,
                          config=config_figure_disable_all)
        return children

    @app.callback(
        Output("longterm-output", "children"),
        Input("city-long-term-select", "value"),
        Input("metric-long-term-select", "value"),
    )
    def get_by_city(city, col_name):
        if city == "ALL":
            city = None
        if col_name not in ['price', 'price_meter']:
            col_name = 'price'
        print(list(dict_df_agg.keys()))
        fig = get_plot_agg_by_feat(dict_df_agg, city, col_name)
        fig.update_layout(template="plotly_dark")
        graph = dcc.Graph(id=f'graph-long-price-{type_}-{city}', figure=fig,
                          config=config_figure_disable_all)
        return graph

    return server, app


if __name__ == '__main__':
    _, app = get_dash(True)
    app.run_server(debug=True, port=8047)
