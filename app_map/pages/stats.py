import os
import sys
import dash
import dash_bootstrap_components as dbc
from dash import dcc
# from app_map.utils import *
# from app_map.util_layout import get_layout
# from app_map.utils_callbacks import add_callbacks
from dash import html, Output, Input, State, ctx
import pandas as pd

dash.register_page(__name__, path='/analytics', title="Analytics", theme=dbc.themes.CYBORG)
from app_map.util_layout import get_page_menu
from stats.daily_fetch_stats import plot_scatter_f, create_ratio, run_for_cities

is_prod = False
if len(sys.argv) > 1:
    is_prod = sys.argv[1] == "prod"

# df_all = get_df_with_prod(is_prod, filename="../resources/yad2_rent_df.pk")
# df_all = app_preprocess_df(df_all)
# app = dash.Dash(external_stylesheets=[dbc.themes.CYBORG])

type_ = 'rent'
# fname = f'test_log_{type_}.pk'
fname = '../resources/df_log_{}.pk'
df_rent = pd.read_pickle(fname.format("rent"))
df_forsale = pd.read_pickle(fname.format("forsale"))

days_back = 30
min_samples = 200


def get_scatter(df, type_, min_samples):
    res_ratio = create_ratio(df, days_back=days_back, min_samples=min_samples)
    fig = plot_scatter_f(df, res_ratio, type_)
    fig.update_layout(template="plotly_dark")
    layout = dbc.Col([
        dcc.Graph(id=f'scatter-ratio-{type_}', figure=fig,
                  # config={'displayModeBar': False,
                  #         'scrollZoom': False}
                  )])
    return layout


def _gen_multi_html(figs):
    n_cols = 4
    n_rows = len(figs) // n_cols
    [fig.update_layout(template="plotly_dark", dragmode=False) for fig in figs]
    graphs = [dbc.Row([dbc.Col(
        dcc.Graph(id=f'graph-city-{i * j + j}', figure=figs[i * n_cols + j],
                  config={'displayModeBar': False,
                          'scrollZoom': False}
                  ),
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


def get_multi_price_parts():
    return [
        dbc.Row(dbc.Col(html.H2("מכירה - תנועות בערים נבחרות של המחיר בזמן, לפי אחוזונים"))),
        *_get_multi_price(df_forsale, "forsale"),
        dbc.Row(dbc.Col(html.H2("שכירות - תנועות בערים נבחרות של המחיר בזמן, לפי אחוזונים"))),
        *_get_multi_price(df_rent, "rent"),
    ]


def get_multi_price_by_side():
    figs1 = _get_multi_price(df_forsale, "forsale", only_figs=True)
    figs2 = _get_multi_price(df_rent, "rent", only_figs=True)
    figs = [item for pair in zip(figs1, figs2) for item in pair]
    graphs = _gen_multi_html(figs)
    return graphs


# https://community.plotly.com/t/how-to-log-client-ip-addresses/6613


layout = html.Div(
    [
        dbc.Row([dbc.Col(html.H1("ניתוח מתקדם - דירות"), style=dict(color="white")), dbc.Col(get_page_menu())]),
        dbc.Row([get_scatter(df_rent, 'rent', 200), get_scatter(df_forsale, 'forsale', 300)],
                style=dict(margin="10px")),
        *get_multi_price_by_side(),
        dbc.Row(
            [
                dbc.Col(html.Div("One of three columns")),
                dbc.Col(html.Div("One of three columns")),
                dbc.Col(html.Div("One of three columns")),
            ]
        ),
    ],
    style={"direction": "rtl", "background-color": "black"}

)

# @app.callback(
#     Output("graph-1", "figure"),
#     Input("graph-1-input", "value"),
# )
# def get_fig(min_samples=200):
#     try:
#         min_samples = int(min_samples)
#     except ValueError:
#         min_samples = 200
#     res_ratio = create_ratio(df_rent, days_back=30, min_samples=min_samples)
#     fig = plot_scatter_f(df_rent, res_ratio, type_)
#     fig.update_layout(template="plotly_dark")
#     return fig


# if __name__ == '__main__':
#     if is_prod:
#         app.run_server(debug=True, host="0.0.0.0")
#     else:
#         app.run_server(debug=True)
