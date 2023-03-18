import os

import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from fetch_data.daily_fetch import pub_object
from plotly.subplots import make_subplots

plt.style.use('ggplot')
timeline_size = (14, 5)
from scrape_nadlan.utils_insert import get_engine

used_cols = ["trans_date", "city", "n_rooms", "price_declared",
             "sq_m_gross", "sq_m_net", "floor", "n_floors",
             "year_built", "parking", "lat", "long",
             'gush', 'helka'
             ]
q = """SELECT {cols_str} from nadlan_trans where 
trans_date > TO_DATE('{from_date}', 'YYYY-MM-DD')
and price_declared = price_estimated
and deal_part = 1
"""


def get_data_nadlan(eng):
    q_frmt = q.format(cols_str=', '.join(used_cols), from_date='2015-01-01')
    with eng.connect() as conn:
        df = pd.read_sql(q_frmt, conn)
    df['trans_date'] = pd.to_datetime(df['trans_date'])
    df = df.set_index('trans_date')
    return df


def print_recent(df):
    print(df.index.min(), df.index.max(), (datetime.now() - df.index.max()).days)
    print(df.groupby(df.index).size()[-5:].sort_index(ascending=False).to_frame())


def get_ir():
    df_rates = pd.read_csv("resources/il_ir.csv")
    df_rates['dt'] = pd.to_datetime(df_rates['dt'])
    df_rates = df_rates.set_index('dt')
    df_rates = df_rates.sort_index()
    return df_rates


def calc_timeline_new_vs_old(df, resample_rule, df_rates=None):
    df['year_sold_built_diff'] = df.index.year - df['year_built']
    df['newOrUsed'] = df['year_sold_built_diff'].apply(lambda x: "new" if x <= 0 else "used")
    res = df.resample(resample_rule, origin='end')['newOrUsed'].value_counts().unstack()  # [:-1]
    return res


def plot_timeline_new_vs_old(df, resample_rule, df_rates=None):
    res = calc_timeline_new_vs_old(df, resample_rule, df_rates)
    fig, ax = plt.subplots(figsize=timeline_size)
    # make a plot
    ax.plot(res.index, res['new'], marker="*", label='new')
    ax.plot(res.index, res['used'], marker="*", label='used')
    ax.set_xlabel("year", fontsize=14)
    ax.set_ylabel("# Units", fontsize=14)
    ax.legend()
    # twin object for two different y-axis on the sample plot
    if df_rates is not None:
        ax2 = ax.twinx()
        # make a plot with different y-axis using second axis object
        ax2.plot(df_rates.index, df_rates['p'], color="gray", label='prime')
        ax2.set_ylabel("prime", fontsize=14)
        ax2.legend()
    fig.savefig(f'resources/plots_daily_nadlan/timeline_new_vs_old.png',
                dpi=100,
                bbox_inches='tight')
    plt.close()


def plot_timeline_new_vs_old_f(df, resample_rule, df_rates=None):
    res = calc_timeline_new_vs_old(df, resample_rule, df_rates)
    import plotly.graph_objects as go
    fig = make_subplots( specs=[[{"secondary_y": True}]]
    )
    fig.add_trace(go.Scatter(x=res.index, y=res['new'],
                             hovertemplate="%{x}<br>%{y:,.0f}",
                             name="new",
                             mode="lines+markers"))
    fig.add_trace(go.Scatter(x=res.index, y=res['used'],
                             hovertemplate="%{x}<br>%{y:,.0f}",
                             name="used",
                             mode="lines+markers"))
    if df_rates is not None:
        fig.add_trace(go.Scatter(x=df_rates.index, y=df_rates['p'], name="prime",
                                 mode="lines+markers", opacity=0.5), secondary_y=True)
    fig.update_layout(
        # title=f"פיזור זמן מול היחס על דירה {get_heb_type_past(type_)}",
        xaxis_title="year",
        yaxis_title="# Units",
        # template="ggplot2",
        margin=dict(l=20, r=20, t=20, b=20),
        dragmode='pan')
    fig.update_layout(template="plotly_dark", dragmode=False)
    import pickle
    file_path = "resources/fig_timeline_new_vs_old.pk"
    pub_object(file_path)
    with open(file_path, 'wb') as f:
        pickle.dump(fig, f)
    fig.show()
    # return fig


def plot_timeline_rooms(df):
    ax = df.resample('M')['n_rooms_'].value_counts().unstack().plot(kind='area', stacked=True, figsize=timeline_size)
    fig = ax.get_figure()
    fig.savefig('resources/plots_daily_nadlan/timeline_rooms.png', dpi=100,
                bbox_inches='tight')
    plt.close()


def plot_timeline_rooms_median_prices(df, n_months_back):
    df = df[df.index > datetime.now() - pd.to_timedelta(f'{30 * n_months_back}D')]
    df.groupby('n_rooms_').resample('M', convention='end', closed="left")['price_declared'].median().unstack(0)[
        ['3', '4', '5']].plot(figsize=timeline_size)
    # df.resample('M', convention='end', closed="left")['price_declared'].median().plot()
    plt.ylim([0, None])
    plt.savefig('resources/plots_daily_nadlan/timeline_rooms_median_price.png', dpi=100,
                bbox_inches='tight')
    plt.close()


def plot_timeline_rooms_city(df, n_months_back):
    df = df[df.index > datetime.now() - pd.to_timedelta(f'{30 * n_months_back}D')]
    dff = df.groupby(['city_', 'n_rooms_']).resample('M', convention='end', closed="left")['price_declared'].agg(
        ['mean', 'size', 'std', 'median'])  # .mean() # .T.pct_change().dropna()
    # colors = ['Red', 'Blue', 'Orange', 'Yellow', 'Green', 'Gray', 'Black', 'Lime']
    metric = "median"
    title_suff = ' מחיר חציוני '[::-1]
    for idx, tup in enumerate(dff.groupby(level=0)):
        row_id, data = tup
        city = row_id
        pivot = data.reset_index().pivot(index='trans_date', columns='n_rooms_', values=metric)
        pivot.drop(columns=['+6', '-2']).plot(kind='line', figsize=timeline_size, title=title_suff + city[::-1])
        plt.savefig(f'resources/plots_daily_nadlan/timeline_rooms_city_{city}.png')
        plt.close()


def _plot_colorize_pct(df, reverse=True, axis=None):
    # https://stackoverflow.com/questions/38246559/how-to-create-a-heat-map-in-python-that-ranges-from-green-to-red
    from matplotlib.colors import LinearSegmentedColormap
    c = ["darkred", "red", "lightcoral", "white", "palegreen", "green", "darkgreen"]
    if reverse:
        c = c[::-1]
    v = [0, .1, .4, .5, .6, .9, 1.]
    l = list(zip(v, c))
    cmap = LinearSegmentedColormap.from_list('rg', l, N=256)
    return df.style.background_gradient(cmap, axis=axis, vmin=-0.5, vmax=0.5).format('{:,.2%}')


def get_n_sales(df):
    # cmap=LinearSegmentedColormap.from_list('rg',["darkred", "w", "darkgreen"], N=256)
    print("Number of sales")
    # [cond_yeshuv_most & cond_full_sale]
    dff = df.groupby(['city_']).resample('Q', convention='end', closed="left").size().T.pct_change().dropna()
    # display(dff)
    _plot_colorize_pct(dff).to_html("resources/plots_daily_nadlan/n_sales.html")


def get_monthly_counts(df):
    # Was in Keshet 12, can tell a change in pct of sells between month to month, compared to rest
    df_monthly_counts = df.groupby(['city_']).resample('Q', convention='end', closed="left").size().T
    df_monthly_counts = df_monthly_counts.divide(df_monthly_counts.sum(axis=1).values, axis=0)
    df_style = df_monthly_counts.style.background_gradient('RdBu', axis=0).format('{:,.2%}')
    df_style.to_html("resources/plots_daily_nadlan/monthly_counts.html")


def get_pct_change(df):
    print("Change in price")
    dff = df.groupby(['city_']).resample('Q', convention='end', closed="left")[
        'price_declared'].mean()  # .T.pct_change().dropna()
    _plot_colorize_pct(dff.unstack().T.pct_change().dropna()).to_html("resources/plots_daily_nadlan/pct_change.html")


def add_columns(df):
    def apply_room(x):
        if x >= 6:
            return '+6'
        elif x <= 2.5:
            return '-2'
        else:
            return str(int(x))

    df['n_rooms_'] = df['n_rooms'].apply(apply_room)
    limit_cities = 9
    yeshuv_lst = df['city'].value_counts()[:limit_cities].index.tolist()
    df['city_'] = df['city'].apply(lambda x: x if x in yeshuv_lst else "_השאר")
    return df


def run_nadlan_stats():
    eng = get_engine()
    df = get_data_nadlan(eng)
    os.makedirs("resources/plots_daily_nadlan", exist_ok=True)
    # df.to_pickle("resources/nadlan.pk")
    # df = pd.read_pickle("resources/nadlan.pk")
    # TODO ADD HERE, but first must auth bucket.
    print_recent(df)
    # plot_timeline_new_vs_old(df, '14D', get_ir())
    plot_timeline_new_vs_old_f(df, '30D', get_ir())

    df = add_columns(df)
    get_monthly_counts(df)
    get_n_sales(df)
    get_pct_change(df)
    plot_timeline_rooms(df)
    plot_timeline_rooms_median_prices(df, n_months_back=24)
    plot_timeline_rooms_city(df, n_months_back=24)


if __name__ == '__main__':
    run_nadlan_stats()
