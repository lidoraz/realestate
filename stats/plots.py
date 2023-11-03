from plotly import graph_objects as go
from plotly.subplots import make_subplots
from api.gateway.api_stats import req_timeseries_recent_quantiles, req_ratio_time_taken_cities, \
    req_timeseries_nadlan_prices
from ext.format import format_number
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


def plot_timeseries_nadlan_prices(black=True):
    x = 'month'
    hover_data = 'pct_median'
    y = 'median_price'  # 'median_avg_meter_price'
    color = 'blue'
    color = None
    data = req_timeseries_nadlan_prices(x)
    df = pd.DataFrame.from_dict(data)
    df[hover_data] = df[hover_data].round(2).astype('str') + '%'  # pct_median error

    fig = go.Figure([
        go.Bar(
            x=df[x],
            y=df['cnt'],
            opacity=0.7,
            name='# Transactions',
            # marker=dict(color=color),
        ),
        go.Scatter(x=df[x], y=df[y], name="ALL", hovertext=df[hover_data], line_shape='spline',
                   # legendgroup="ALL",
                   line_color=color, line_width=2,
                   mode='lines+markers',
                   opacity=1,
                   yaxis='y2'),
    ])
    # fig.update_yaxes(rangemode="tozero")
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        height=400,
        yaxis=dict(side='left',
                   visible=False,
                   showgrid=False),
        yaxis2=dict(side='right',
                    visible=True,
                    overlaying='y',
                    showgrid=True),
        dragmode=False)
    fig.update_yaxes(  # rangemode="tozero"
        # range=(500_000, None)
    )
    fig.update_layout(
        # dragmode=False,
        # legend=dict(# orientation="h",
        #             yanchor="bottom",
        #             #y=1.02,
        #             xanchor="left",
        #             x=0)
    )
    if black:
        fig.update_layout(
            template="plotly_dark",
            legend=dict(x=0, y=1),
            # dragmode=False
        )
    return fig


def plot_line(df, x, y, y2, hover_data, color='Blue'):
    df = df.ffill()
    fig = go.Figure([
        go.Scatter(x=df[x], y=df[y], name="ALL", hovertext=df[hover_data], line_shape='spline',
                   legendgroup="ALL",
                   line_color=color, line_width=2,
                   mode='lines',
                   opacity=0.9),
        go.Scatter(x=df[x], y=df[y2], name="SameRooms", hovertext=df['cnt_room'], line_shape='spline',
                   legendgroup="SameRooms",
                   line_color=color, line_width=2,
                   mode='lines+markers'),  # lines+markers
        go.Bar(
            x=df[x],
            y=df['cnt'],
            opacity=0.1,
            name='#Transactions',
            marker=dict(color=color),
            yaxis='y2'
        )
    ])
    # Add last value at the end on scatter
    for i, d in enumerate(fig.data):
        if d.type == 'scatter':
            text = str(format_number(d.y[-1]))
            fig.add_annotation(x=d.x[-1], y=d.y[-1],
                               text=text,
                               showarrow=False,
                               bgcolor='white',
                               font=dict(size=10),
                               # yshift=10
                               )

    fig.update_yaxes(rangemode="tozero")
    fig.update_layout(
        yaxis=dict(side='left',
                   showgrid=True),
        yaxis2=dict(side='right',
                    visible=False,
                    overlaying='y',
                    showgrid=False, ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=250,
        dragmode=False,
        legend=dict(orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0)
    )
    return fig


if __name__ == '__main__':
    fig = plot_timeseries_nadlan_prices()
    fig.show()
    print(fig)
