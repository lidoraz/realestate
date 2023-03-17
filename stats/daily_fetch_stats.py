import os

from fetch_data.daily_fetch import pub_object
from scrape_nadlan.utils_insert import get_engine
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.graph_objects as go

plt.style.use('ggplot')

log_tbl_cols = ['id', 'processing_date', 'date_updated', 'date_added', 'price', 'asset_type', 'rooms',
                'asset_status', 'active', 'city',
                # 'neighborhood', 'street', 'square_meters', 'is_agency',  'lat', 'long'
                ]


def get_heb_type_past(type_):
    return "שהושכרה" if type_ == "rent" else "שנמכרה"


def get_heb_type_present(type_):
    return "שכירות" if type_ == 'rent' else "מכירה"


def fetch_data_log(type_, eng):
    with eng.connect() as conn:
        df = pd.read_sql(f"SELECT {','.join(log_tbl_cols)} FROM public.yad2_{type_}_log", conn)  #
        df['processing_date'] = pd.to_datetime(df['processing_date'])
        df = df.set_index('processing_date')
        print(f"Log Table stats: {df.index.min()}, {df.index.max()}")
        return df


# Can create also historic ratio as active will be all relevant items and those who closed AFTER the date.
def create_ratio(df, days_back=21, min_samples=200):
    rent_active = df[df['active']].groupby('city').size()
    rent_active = rent_active[rent_active >= min_samples].rename('active')
    rent_unactive = df[
        (~df['active']) & (df.index >= datetime.today() - timedelta(days=days_back))].groupby(
        'city').size()
    rent_unactive = rent_unactive.rename('unactive')
    df_r = rent_unactive.to_frame().join(rent_active)
    df_r['r'] = df_r.apply(lambda r: (r['active']) / r['unactive'], axis=1).rename('active_to_taken')
    df_r = df_r[~pd.isna(df_r['active'])]
    df_r = df_r.sort_values('r', ascending=False)
    res = df_r['r']
    return res


def run_for_cities(df, type_, n_cities=9, resample_rule='7D', use_median=True):
    sel_cities = ['חיפה', 'ירושלים', 'תל אביב יפו', 'רמת גן', 'אשדוד', 'ראשון לציון', 'ירשולים', 'באר שבע', 'נתניה']
    # sel_cities = df['city'].value_counts().index[:n_cities].to_list()
    df['city_'] = df['city'].apply(lambda x: x if x in sel_cities else "שאר הערים")
    figs = []
    for city, grp in df.groupby('city_'):
        fig = create_percentiles_per_city_f(df, city, type_, resample_rule, use_median)
        figs.append(fig)
    return figs  # create_percentiles_per_city(df, city, type_, resample_rule)


def create_percentiles_per_city(df, city, type_, resample_rule):
    # df_f = df_t.query(f"city == '{c}' and active == False and  rooms_text == 3.0")
    df = df.query(f"city_ == '{city}' and active == False")
    x = df.resample(resample_rule, origin='end')['price'].describe()  # agg(['median', 'mean', 'std', 'size'])

    title = f"{city} {get_heb_type_present(type_)} אחוזון {resample_rule[::-1]}"[::-1]
    fig, ax = plt.subplots(figsize=(20, 10))
    x[['25%', '50%', '75%']].plot(figsize=(8, 4), kind='line', stacked=False, title=title, ax=ax, marker='o')
    # plt.ylim([0, None])
    x.plot(y='count', ax=ax, secondary_y=True, linestyle='-.')
    plt.savefig(f'resources/stats/plots_daily_{type_}/percentile_{city}.png')
    # plt.show()
    plt.close()


def create_percentiles_per_city_f(df, city, type_, resample_rule, use_median=True):
    df = df.query(f"city_ == '{city}' and active == False")
    x = df.resample(resample_rule, origin='end')['price'].describe()  # agg(['median', 'mean', 'std', 'size'])
    heb_type = "שכירות" if type_ == 'rent' else "מכירה"
    title = f"{city} {heb_type} אחוזון {resample_rule}"

    from plotly.subplots import make_subplots
    fig = make_subplots(
        # specs=[[{"secondary_y": True}]]
    )

    if use_median:
        for perc in ['25%', '50%', '75%']:
            fig.add_trace(go.Scatter(x=x.index, y=x[perc].round(),
                                     text=x['count'],
                                     hovertemplate="%{x} (#%{text})<br>₪%{y}",
                                     name="",
                                     mode="lines+markers"))
    else:
        # USING MEAN AND STD IS REALLY NOISEY, CANT TELL NOTHNIG FROM THIS
        fig.add_trace(go.Scatter(x=x.index, y=x["mean"], text=x['count'], mode="lines+markers", name=title))
        fig.add_trace(go.Scatter(x=x.index, y=x["mean"] + x['std'], mode='lines', fill=None))
        fig.add_trace(go.Scatter(x=x.index, y=x["mean"] - x['std'], mode='lines', fill='tonexty',
                                 fillcolor="rgba(148, 0, 211, 0.15)"))
    # fig.add_trace(go.Scatter(x=x.index, y=x['count'], name="count",
    #                          mode="lines+markers", opacity=0.1), secondary_y=True)
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20),
                      title=f'{city} ({get_heb_type_present(type_)})', )
    fig.update_layout()
    return fig

    # fig, ax = plt.subplots(figsize=(20, 10))
    # x[['25%', '50%', '75%']].plot(figsize=(8, 4), kind='line', stacked=False, title=title, ax=ax, marker='o')
    # # plt.ylim([0, None])
    # x.plot(y='count', ax=ax, secondary_y=True, linestyle='-.')
    # plt.savefig(f'resources/stats/plots_daily_{type_}/percentile_{city}.png')
    # # plt.show()
    # plt.close()


def get_price_changes(eng, type_):
    q = f"""
    with t0 as (
    SELECT id, count(*) as cnt from yad2_{type_}_history where price > 0 group by id order by cnt desc),
    t1 as (SELECT b.* from t0 a join yad2_{type_}_history b on a.id = b.id  where cnt > 1)
    select * from t1 where id in (SELECT id from yad2_{type_}_today)
    """
    with eng.connect() as conn:
        df_rent_prices = pd.read_sql(q, conn)
    df_rent_prices = df_rent_prices.sort_values(['id', 'processing_date'])
    df_rent_g = df_rent_prices.groupby('id').agg(price_lst=('price', list),
                                                 dt_lst=('processing_date', list),
                                                 dt_last=('processing_date', 'last'))
    df_rent_g['price_pct'] = df_rent_g['price_lst'].apply(lambda x: x[-1] / x[0] - 1)
    df_rent_g['days'] = (df_rent_g['dt_lst'].apply(lambda x: x[-1] - x[0])).dt.days
    df_rent_g['dt_last'] = pd.to_datetime(df_rent_g['dt_last'])
    df_g = df_rent_g[df_rent_g['dt_last'] > datetime.now() - pd.to_timedelta('8D')].query("price_pct > -0.8")
    res = df_g.reset_index().sort_values(['price_pct', 'days'], ascending=[True, False])[:30]
    res.to_html(f'resources/stats/plots_daily_{type_}/price_changes.html')


def plot_ratio(res, type_):
    res_ = res.copy()
    res_.index = [x[::-1] for x in res.index]
    heb_type = "שהושכרה" if type_ == "rent" else "שנמכרה"
    res_.plot(kind='bar', figsize=(12, 5),
              title=f"{datetime.today().date()} " + f"יחס הדירות הפנויות לכל דירה {heb_type} בחודש האחרון "[::-1])
    print("lower is better for rent as more demand")
    _ = plt.xticks(rotation=60)
    plt.tight_layout()
    plt.savefig(f'resources/stats/plots_daily_{type_}/active_ratio.png')
    plt.close()


def plot_ratio_f(res, type_):
    res_ = res.copy()
    heb_type = "שהושכרה" if type_ == "rent" else "שנמכרה"
    title = f"{datetime.today().date()} " + f"יחס הדירות הפנויות לכל דירה {heb_type} בחודש האחרון "
    fig = go.Figure(data=go.Bar(x=res_.index, y=res_))  # hover text goes here
    fig.update_layout(title=title).update_xaxes(tickangle=300)
    fig.show()


def plot_scatter(df, res_ratio, type_):
    df['time_alive'] = (datetime.today() - df['date_added']).dt.days
    df_g = df[~df['active']].groupby('city')['time_alive'].agg(['mean', 'std', 'median', 'size'])
    df_g = df_g.join(res_ratio, how='inner')
    len_b = len(df_g)
    df_g = df_g[df_g['size'] >= 30]
    print(len_b, len(df_g))
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.scatter(df_g['median'], df_g['r'])
    ax.set_title("פיזור זמן מול היחס"[::-1])
    ax.set_ylabel('יחס דירות באתר מול דירות שירדו בחודש האחרון'[::-1])
    ax.set_xlabel('זמן חציוני לדירות באתר מרגע הפרסום עד להורדה'[::-1])

    for i, txt in enumerate(df_g.index):
        ax.annotate(txt[::-1], (df_g['median'][i] * 1.01, df_g['r'][i]))
    plt.savefig(f'resources/stats/plots_daily_{type_}/scatter.png')
    plt.close()


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
                                    hovertemplate="%{text}<br>Ratio: %{y}<br>#Days: %{x}</br>#Deals: %{marker.color}",
                                    name="",
                                    text=df_g.index))  # hover text goes here
    fig.update_layout(title=f"פיזור זמן מול היחס על דירה {get_heb_type_past(type_)}",
                      xaxis_title="זמן חציוני לדירות באתר מרגע הפרסום עד להורדה",
                      yaxis_title="יחס דירות באתר מול דירות שירדו בחודש האחרון",
                      # template="ggplot2",
                      margin=dict(l=20, r=20, t=20, b=20),
                      dragmode='pan')
    return fig
    # fig.show()
    #
    # fig, ax = plt.subplots(figsize=(12, 12))
    # ax.scatter(df_g['median'], df_g['r'])
    # ax.set_title("פיזור זמן מול היחס"[::-1])
    # ax.set_ylabel('יחס דירות באתר מול דירות שירדו בחודש האחרון'[::-1])
    # ax.set_xlabel('זמן חציוני לדירות באתר מרגע הפרסום עד להורדה'[::-1])
    #
    # for i, txt in enumerate(df_g.index):
    #     ax.annotate(txt[::-1], (df_g['median'][i] * 1.01, df_g['r'][i]))
    # plt.savefig(f'resources/stats/plots_daily_{type_}/scatter.png')
    # plt.close()


def test_1(df):
    grp_by = ['city', 'rooms', 'asset_status']
    filter_by = 'active == False and rooms == 3.0'
    agg_what = 'price'
    agg_by = ['mean', 'std', 'size']
    having_by = 'size > 15'
    df.query(filter_by).groupby(grp_by)[agg_what].agg(agg_by).round().query(having_by)  # .mean()


def get_compare_closed_vs_active_median_price(df, city):
    # city = 'גבעתיים'
    # city = 'הרצליה'
    # city = 'רמת גן'
    # city = 'באר שבע'
    # city = 'קרית ים'
    # FILTER HERE BY ACTIVE LAST MONTH.
    # and price > 1000
    # q = f"city == '{city}' and active == True| and rooms_text <= 5 "
    print(city)
    q = f"city == '{city}' and 3.0 <= rooms <= 4 "
    df_g_p = df.query(q).groupby(['rooms', 'asset_status', 'active'])['price'].agg(
        ['median', 'mean', 'std', 'size']).query(
        'size > 5').round()  # .agg(['mean', 'median', len]) # .hist(stacked=True)
    df_g_p.name = city
    print(df_g_p)


def run(type_):
    print(f"Started daily stats for {type_}")
    eng = get_engine()
    df = fetch_data_log(type_, eng)
    file_path = f"resources/df_log_{type_}.pk"
    # df = pd.read_pickle(fname)
    df.to_pickle(file_path)
    pub_object(file_path)
    #
    os.makedirs(f"resources/stats/plots_daily_{type_}", exist_ok=True)
    res_ratio = create_ratio(df, days_back=30, min_samples=200)
    plot_ratio(res_ratio, type_)
    plot_scatter(df, res_ratio, type_)
    run_for_cities(df, type_, n_cities=9, resample_rule='7D')
    get_price_changes(eng, type_)


if __name__ == '__main__':
    run('forsale')
    run('rent')
