import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html, Output, Input
from app_map.util_layout import get_page_menu
from stats.plots import get_fig_quantiles_from_df, get_fig_quantiles_multi_city
from stats.calc_plots import run_for_cities, create_ratio
from stats.plots import plot_scatter_f

config_figure_disable_all = {'displayModeBar': False,
                             'scrollZoom': False}

from app_map.persistance_utils import get_stats_data

stats_data = get_stats_data()
cities = stats_data['df_log_forsale']['city'].value_counts()
cities = cities[cities > 100].sort_index()

additional_all_key = [dict(label="בכל הארץ", value="ALL")]
cities_options = additional_all_key + [dict(label=f'{city}', value=city) for city, cnt in
                                       cities.items()]
# Removing first key:
dict_df_agg_nadlan_all = stats_data['dict_combined']['ALL']
dict_df_agg_keys = sorted([k for k in dict_df_agg_nadlan_all.keys() if k != 'ALL'])
cities_long_term_options = additional_all_key + [dict(label=f'{city}', value=city) for city in dict_df_agg_keys]

days_back = 30
min_samples = 200


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


def _gen_multi_html(figs, n_cols=4):
    n_rows = len(figs) // n_cols
    import uuid
    [fig.update_layout(template="plotly_dark", dragmode=False) for fig in figs]
    graphs = [dbc.Row([dbc.Col(
        dcc.Graph(id=f'graph-{uuid.uuid4()}-city-{i * j + j}', figure=figs[i * n_cols + j],
                  config=config_figure_disable_all),
        style=dict(margin="10px")) for j in range(n_cols)])

        for i in range(n_rows)]
    return graphs


def _get_multi_price(df, type_):
    days_back = 7
    figs = run_for_cities(df, type_, n_cities=8, resample_rule=f'{days_back}D', use_median=True)
    return figs


def _get_single_price(df, type_, city, col_name):
    days_back = 7
    fig = get_fig_quantiles_from_df(df, city, type_, f'{days_back}D', col_name)
    fig.update_layout(template="plotly_dark", dragmode=False)
    return dcc.Graph(id=f'graph-single-price-{type_}-{city}', figure=fig,
                     config=config_figure_disable_all)


def get_single_price(city=None, col_name='price'):
    return [dbc.Col(_get_single_price(get_stats_data()['df_log_forsale'], "sale", city, col_name)),
            dbc.Col(_get_single_price(get_stats_data()['df_log_rent'], "rent", city, col_name))]


def get_multi_price_by_side(n_cols):
    figs1 = _get_multi_price(get_stats_data()['df_log_forsale'], "forsale")
    figs2 = _get_multi_price(get_stats_data()['df_log_rent'], "rent")
    figs = [item for pair in zip(figs1, figs2) for item in pair]
    graphs = _gen_multi_html(figs, n_cols)
    cont = [dbc.Row(dbc.Col(html.H3("תנועות בערים נבחרות של המחיר בזמן, לפי אחוזונים"))),
            dbc.Row(graphs)]
    return cont


# MAIN NADLAN # DEALS

fig = get_stats_data()['fig_timeline_new_vs_old']
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
            # dcc.Loading(
            #     id="loading-1",
            #     type="default",
            #     fullscreen=True,
            #     children=html.Div(id="loading-output-1")
            # ),
            dbc.Row([dbc.Col(get_page_menu()),
                     dbc.Col(html.H1("Real Estate Analytics"), width=8, style=dict(direction="ltr"))]),
            dbc.Row(dbc.Col(html.H6(id="updated-at-line"))),
            dbc.Row(dbc.Col(html.H3("מכירות דירות מול השפעת הריבית"))),
            dbc.Row(dbc.Col(graph_obj)),

            dbc.Row(dbc.Col()),
            dbc.Row(dbc.Col(html.H3("פיזור הביקוש מול ההיצע"))),
            dbc.Row(dbc.Col(html.Span(
                "פיזור בין הזמן החציוני לדירה להפוך ללא רלוונטית מול מדד ההיצע - כלומר כמה דירות פנויות יש מול דירות שכבר לא רלוונטיות"))),
            dbc.Row(
                [dbc.Col(
                    [html.H4("SALE", style={"background-color": "#1e81b0"}),
                     get_scatter(get_stats_data()['df_log_forsale'], 'forsale', 300)], width=6, xs=12),
                    dbc.Col([html.H4("RENT", style={"background-color": "#e28743"}),
                             get_scatter(get_stats_data()['df_log_rent'], 'rent', 200)], width=6, xs=12)],
                className="analysis-main-multi-grid"),
            # dbc.Row(),
            # dbc.Row(dbc.Col(html.Span("בכל הארץ, כל גרף מייצג אחוזון, כאשר האמצע הוא החציון"))),
            # dbc.Row(get_single_price(None), ),
            # dbc.Row(dbc.Col()),
            html.H3("תנועות המחיר בזמן"),
            dbc.Row([
                dbc.Col([
                    html.H5("בטווח ארוך"),
                    html.Div([html.Label("בחר עיר"),
                              dbc.Switch(id="city-long-term-select-multi-switch", value=False),
                              html.Span('בחירה מרובה', style={"font-size": "smaller"})],
                             style={"display": "flex"}),
                    html.Div([dcc.Dropdown(
                        cities_long_term_options,
                        value='ALL',
                        placeholder="multi",
                        multi=False,
                        id="city-long-term-select-multi",
                        clearable=False,
                        # className="form-select",
                        style={"width": "250px", "color": "black", "font-size": "initial"}
                    )], style={"display": "flex"}),

                    # dbc.Select(id="city-long-term-select", options=cities_long_term_options,
                    #            value="ALL",
                    #            style=dict(width="200px", direction="ltr"),
                    #            className="form-select"),
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
                            {"label": "חדש / יד שניה", "value": "CMP"},
                            {"label": "הכל", "value": "ALL"},
                            {"label": "חדש", "value": "NEW"},
                            {"label": "יד שניה", "value": "OLD"},
                        ],
                        value="CMP",
                        inline=True,
                        id="year-built-long-term-select",
                        labelClassName="btn btn-outline-primary",
                        className="btn-group",
                        inputClassName="btn-check"
                    ),
                ], className="form-group"),
                dbc.Col([html.Div(id="pct-stats-long-term",
                                  style={"display": "flex", "margin": "10px", "font-size": "smaller"}),
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
            dbc.Row(dbc.Col(html.H5("בטווח הקצר"))),
            # dbc.Row(),
            dbc.Row(dbc.Col([
                dcc.Dropdown(
                    cities_options,
                    value='ALL',
                    placeholder="בטווח הקצר",
                    multi=False,
                    id="city-select",
                    clearable=False,
                    # className="form-select",
                    style={"width": "150px", "color": "black", "font-size": "initial", "margin": "7px"}
                ),
                dbc.RadioItems(
                    options=[
                        {"label": "מחיר", "value": "price"},
                        {"label": "מחיר למ״ר", "value": "price_meter"},
                    ],
                    value="price",
                    inline=True,
                    id="metric-select",
                    labelClassName="btn btn-outline-primary",
                    className="btn-group",
                    inputClassName="btn-check"
                ),
            ])),
            dbc.Row(get_single_price(), id="city-output"),
            *get_multi_price_by_side(n_cols=2),
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
        children = [dbc.Col(_get_single_price(get_stats_data()['df_log_forsale'], "sale", city, col_name)),
                    dbc.Col(_get_single_price(get_stats_data()['df_log_rent'], "rent", city, col_name))]
        return children

    @app.callback(
        Output("updated-at-line", "children"),
        Output("pct-stats-long-term", "children"),
        Output("longterm-output", "children"),
        Output("alert-auto", "children"),
        Output("alert-auto", "is_open"),
        Input("city-long-term-select-multi", "value"),
        Input("metric-long-term-select", "value"),
        Input("year-built-long-term-select", "value")
    )
    def get_by_city_long_term(multi_city, col_name, asset_year):
        from app_map.utils import create_pct_bar
        show_pct_bar = True
        dict_combined = get_stats_data()['dict_combined']
        if isinstance(multi_city, list):
            df_agg = [dict_combined["ALL"][c] for c in multi_city]
            fig = get_fig_quantiles_multi_city(df_agg, multi_city, col_name)
            show_pct_bar = False
        else:
            city = multi_city
            from stats.plots import get_fig_quantiles_city_new_vs_old
            if asset_year != 'CMP':
                dict_df_agg = dict_combined[asset_year]
                df_agg = dict_df_agg[city]
                print(df_agg.columns)

                fig = get_fig_quantiles_city_new_vs_old(df_agg, city, col_name)
                # HERE IT WILL SHOW AS USUAL
            else:
                df_agg = [dict_combined["ALL"][city],
                          dict_combined["NEW"][city],
                          dict_combined["OLD"][city]]
                fig = get_fig_quantiles_city_new_vs_old(df_agg, city, col_name)
                df_agg = df_agg[0]  # Take ALL, used for pct_bar
        fig.update_layout(template="plotly_dark", dragmode=False)
        html_pct_bar = create_pct_bar(df_agg, col_name) if show_pct_bar else []

        fig.update_layout(template="plotly_dark", dragmode=False)
        graph = dcc.Graph(id=f'graph-long-price-sale', figure=fig,
                          config=config_figure_disable_all)
        update_at_line = [f"מעודכן ל-{get_stats_data()['date_updated']}"]
        return update_at_line, html_pct_bar, graph, "", False

    @app.callback(
        Output('city-long-term-select-multi', 'multi'),
        Output('city-long-term-select-multi', 'value'),
        Input('city-long-term-select-multi-switch', 'value'),
        Input('city-long-term-select-multi', 'value')

    )
    def switch_long_term_select(switch_val, value):
        val_b = value
        if not switch_val:
            value = value[0] if isinstance(value, list) else value
        if value is None:
            value = "ALL"
        if val_b == value:
            value = dash.no_update
        return switch_val, value

    return server, app


if __name__ == '__main__':
    _, app = get_dash(True)
    app.run_server(debug=True, port=8047)
