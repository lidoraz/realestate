from datetime import datetime

from plotly import graph_objects as go


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


def create_percentiles_per_city_f(df, city, type_, resample_rule, col_name, use_median=True, df_agg=None):
    # TODO: REWRIET THIS FUNCTION
    if df_agg is None:
        if city is not None:
            df = df.query(f"city == '{city}' and active == False")
            title = f'{city} ({get_heb_type_present(type_)})'
        else:
            df = df.query(f"active == False")
            title = f'({get_heb_type_present(type_)})'
        if not len(df):
            raise ValueError("Not cities found")
        x = df.resample(resample_rule, origin='end')[col_name].describe()  # agg(['median', 'mean', 'std', 'size'])

    else:
        x = df_agg[col_name]
        if city is None:
            city = "כל הארץ"
        title = f'{city}(מכירה - הלמ״ס) '
    from plotly.subplots import make_subplots
    fig = make_subplots(
        # specs=[[{"secondary_y": True}]]
    )

    if use_median:
        for perc in ['25%', '50%', '75%']:
            pct_chg_str = x[perc].pct_change()
            # text = pct_chg_str.apply(lambda x: f'{x}% ') + x['count'].astype(str).apply(lambda x: f"(#{x})")
            # print(text)
            fig.add_trace(go.Scatter(x=x.index, y=x[perc].round(),
                                     customdata=pct_chg_str,
                                     text=x['count'],
                                     hovertemplate="%{x} (%{text:,.0f})<br>₪%{y:,.0f} (%{customdata:.2%})",
                                     name=perc,
                                     mode="lines+markers"))
    else:
        # USING MEAN AND STD IS REALLY NOISEY, CANT TELL NOTHNIG FROM THIS
        fig.add_trace(go.Scatter(x=x.index, y=x["mean"], text=x['count'], mode="lines+markers", name=title))
        fig.add_trace(go.Scatter(x=x.index, y=x["mean"] + x['std'], mode='lines', fill=None))
        fig.add_trace(go.Scatter(x=x.index, y=x["mean"] - x['std'], mode='lines', fill='tonexty',
                                 fillcolor="rgba(148, 0, 211, 0.15)"))
    # fig.add_trace(go.Scatter(x=x.index, y=x['count'], name="count",
    #                          mode="lines+markers", opacity=0.1), secondary_y=True)
    fig.update_layout(showlegend=False,
                      margin=dict(l=20, r=20, t=35, b=20),
                      hoverlabel=dict(
                          bgcolor="black",
                          # bgcolor="white",
                          # font_size=16,
                          # font_family="Rockwell"
                      ),
                      title=title)
    # fig.show()
    return fig
