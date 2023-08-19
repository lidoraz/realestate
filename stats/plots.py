from plotly import graph_objects as go
from plotly.subplots import make_subplots
from api.gateway.api_stats import req_timeseries_recent_quantiles, req_ratio_time_taken_cities
import pandas as pd


def get_heb_type_past(type_):
    return "שהושכרה" if type_ == "rent" else "שנמכרה"


def get_heb_type_present(type_):
    return "שכירות" if type_ == 'rent' else "מכירה"


def _update_multi_trace_layout(fig, title):
    fig.update_layout(showlegend=True,
                      margin=dict(l=20, r=20, t=35, b=20),
                      legend=dict(x=0, y=1),
                      hoverlabel=dict(
                          bgcolor="black",
                      ),
                      title=title)
    fig.update_yaxes(rangemode="tozero")
    return fig


def _get_trace_scatter(x, perc, name, show_perc_legend=True):
    name = f"{name} ({perc})" if show_perc_legend else name
    cnt_col = 'cnt' if 'cnt' in x.columns else 'count'  # replace here
    return go.Scatter(x=x.index, y=x[perc].round(),
                      customdata=x[perc].pct_change(),
                      text=x[cnt_col],
                      hovertemplate="%{x} (%{text:,.0f})<br>₪%{y:,.0f} (%{customdata:.2%})",
                      name=name,
                      mode="lines+markers")


def get_fig_quantiles_city_new_vs_old(df_agg, city, col_name):
    fig = make_subplots()
    if city == "ALL":
        city = "כל הארץ"
    title = f'{city}(מכירה - הלמ״ס) '
    if isinstance(df_agg, list):
        perc = '50%'
        fig.add_trace(_get_trace_scatter(df_agg[0][col_name], perc, "ALL"))
        fig.add_trace(_get_trace_scatter(df_agg[1][col_name], perc, "NEW"))
        fig.add_trace(_get_trace_scatter(df_agg[2][col_name], perc, "OLD"))
    else:
        x = df_agg[col_name]
        for perc in ['75%', '50%', '25%']:
            fig.add_trace(_get_trace_scatter(x, perc, perc, show_perc_legend=False))

    return _update_multi_trace_layout(fig, title)


def get_fig_quantiles_multi_city(df_aggs, multi_city, col_name):
    fig = make_subplots()
    multi_city_str = ', '.join(multi_city)
    title = f'{multi_city_str}50% (מכירה - הלמ״ס) '
    for df_agg, city in zip(df_aggs, multi_city):
        fig.add_trace(_get_trace_scatter(df_agg[col_name], '50%', city, show_perc_legend=False))
    return _update_multi_trace_layout(fig, title)


def get_fig_quantiles_from_api(deal_type, city, time_interval, col_name="price"):
    assert col_name in ("price", "price_meter")  # price_meter_25
    data = req_timeseries_recent_quantiles(deal_type, time_interval, cities=city)
    fig = make_subplots()
    df = pd.DataFrame.from_dict(data)
    # TODO: FINISH HERE!
    if isinstance(city, str):
        # df[df['city'] == 'רמת גן'].sort_values(time_interval)
        title = f'{city} ({get_heb_type_present(deal_type)})'
    elif city is None:
        title = f'({get_heb_type_present(deal_type)})'
    else:
        raise ValueError("CHECK OPTION HERE FOR mULTI CITY")
    df = df.set_index(time_interval)
    for perc in ['75%', '50%', '25%']:
        df[perc] = df[f"{col_name}_{perc[:-1]}"]
        fig.add_trace(_get_trace_scatter(df, perc, perc, show_perc_legend=False))
    return _update_multi_trace_layout(fig, title)


CITIES = ('חיפה', 'ירושלים', 'תל אביב יפו', 'רמת גן', 'אשדוד', 'ראשון לציון', 'גבעתיים', 'באר שבע', 'הרצליה',
          'נתניה')


def get_figs_for_cities(type_, time_interval='week', selected_cities=CITIES):
    figs = []

    for city in selected_cities:
        fig = get_fig_quantiles_from_api(type_, city, time_interval)
        figs.append(fig)
    return figs


def get_scatter(deal_type, min_samples):
    from dash import dcc
    data = req_ratio_time_taken_cities(deal_type, min_samples, days_back=7)
    df = pd.DataFrame.from_dict(data)
    fig = _get_scatter_fig(x=df['median_days_to_not_active'],
                           y=df['ratio'],
                           marker_color=df['active_cnt'],
                           text=df['city'])
    fig.update_layout(template="plotly_dark")
    modeBarButtonsToRemove = ['select2d', 'lasso2d']
    return dcc.Graph(id=f'scatter-ratio-{deal_type}', figure=fig,
                     config={
                         'modeBarButtonsToRemove': modeBarButtonsToRemove,
                         # 'displayModeBar': False,
                         'scrollZoom': False}
                     )


def _get_scatter_fig(x, y, marker_color, text):
    import plotly.graph_objects as go
    fig = go.Figure(data=go.Scatter(x=x, y=y, marker_color=marker_color,
                                    mode='markers+text',
                                    textposition="bottom center",
                                    hovertemplate="%{text}<br>Ratio: %{y:.2f}<br>#Days: %{x:,.0f}</br>#Deals: %{marker.color:,.0f}",
                                    name="",
                                    text=text))  # hover text goes here
    fig.update_layout(
        xaxis_title="זמן חציוני לדירות באתר מרגע הפרסום עד להורדה",
        yaxis_title="יחס דירות באתר מול דירות שירדו בחודש האחרון",
        # template="ggplot2",
        margin=dict(l=20, r=20, t=20, b=20),
        dragmode='pan')
    return fig
