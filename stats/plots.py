from datetime import datetime

from plotly import graph_objects as go
from plotly.subplots import make_subplots


def get_heb_type_past(type_):
    return "שהושכרה" if type_ == "rent" else "שנמכרה"


def get_heb_type_present(type_):
    return "שכירות" if type_ == 'rent' else "מכירה"


def plot_ratio_f(res, type_):
    res_ = res.copy()
    heb_type = "שהושכרה" if type_ == "rent" else "שנמכרה"
    title = f"{datetime.today().date()} " + f"יחס הדירות הפנויות לכל דירה {heb_type} בחודש האחרון "
    fig = go.Figure(data=go.Bar(x=res_.index, y=res_))  # hover text goes here
    fig.update_layout(title=title).update_xaxes(tickangle=300)
    fig.show()


def plot_scatter_f(df, res_ratio, type_):
    df['time_alive'] = (datetime.today() - df['date_added']).dt.days
    df_g = df[~df['active']].groupby('city')['time_alive'].agg(['mean', 'std', 'median', 'size'])
    df_g = df_g.join(res_ratio, how='inner')
    len_b = len(df_g)
    df_g = df_g[df_g['size'] >= 30]
    print(len_b, len(df_g))
    fig = go.Figure(data=go.Scatter(x=df_g['median'], y=df_g['r'], marker_color=df_g['size'],
                                    mode='markers+text',
                                    textposition="bottom center",
                                    hovertemplate="%{text}<br>Ratio: %{y:.2f}<br>#Days: %{x:,.0f}</br>#Deals: %{marker.color:,.0f}",
                                    name="",
                                    text=df_g.index))  # hover text goes here
    fig.update_layout(
        xaxis_title="זמן חציוני לדירות באתר מרגע הפרסום עד להורדה",
        yaxis_title="יחס דירות באתר מול דירות שירדו בחודש האחרון",
        # template="ggplot2",
        margin=dict(l=20, r=20, t=20, b=20),
        dragmode='pan')
    return fig


def _update_multi_trace_layout(fig, title):
    fig.update_layout(showlegend=True,
                      margin=dict(l=20, r=20, t=35, b=20),
                      legend=dict(x=0, y=1),
                      hoverlabel=dict(
                          bgcolor="black",
                      ),
                      title=title)
    return fig


def _get_trace_scatter(x, perc, name, show_perc_legend=True):
    name = f"{name} ({perc})" if show_perc_legend else name
    return go.Scatter(x=x.index, y=x[perc].round(),
                      customdata=x[perc].pct_change(),
                      text=x['count'],
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


def get_fig_quantiles_from_df(df, city, type_, resample_rule, col_name):
    fig = make_subplots()
    if city is not None:
        df = df.query(f"city == '{city}' and active == False")
        title = f'{city} ({get_heb_type_present(type_)})'
    else:
        df = df.query(f"active == False")
        title = f'({get_heb_type_present(type_)})'
    if not len(df):
        raise ValueError("Not cities found")
    x = df.resample(resample_rule, origin='end')[col_name].describe()  # agg(['median', 'mean', 'std', 'size'])
    for perc in ['75%', '50%', '25%']:
        fig.add_trace(_get_trace_scatter(x, perc, perc, show_perc_legend=False))
    return _update_multi_trace_layout(fig, title)


def create_percentiles_per_city_f(df, city, type_, resample_rule, col_name, use_median=True, df_agg=None):
    pass
# else:
#     # USING MEAN AND STD IS REALLY NOISEY, CANT TELL NOTHNIG FROM THIS
#     fig.add_trace(go.Scatter(x=x.index, y=x["mean"], text=x['count'], mode="lines+markers", name=title))
#     fig.add_trace(go.Scatter(x=x.index, y=x["mean"] + x['std'], mode='lines', fill=None))
#     fig.add_trace(go.Scatter(x=x.index, y=x["mean"] - x['std'], mode='lines', fill='tonexty',
#                              fillcolor="rgba(148, 0, 211, 0.15)"))
# fig.add_trace(go.Scatter(x=x.index, y=x['count'], name="count",
#                          mode="lines+markers", opacity=0.1), secondary_y=True)

# fig.show()
# return fig
