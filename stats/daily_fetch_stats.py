import os

from fetch_data.daily_fetch import pub_object
from ext.env import get_pg_engine
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

plt.style.use('ggplot')

log_tbl_cols = ['a.id', 'a.processing_date', 'date_updated', 'date_added', 'price', 'rooms', 'a.square_meters',
                'square_meter_build',
                'active', 'city', 'asset_type', 'asset_status'
                # 'neighborhood', 'street', 'square_meters', 'is_agency',  'lat', 'long'
                ]


def fetch_data_log(type_, eng):
    with eng.connect() as conn:
        df = pd.read_sql(
            f"SELECT {','.join(log_tbl_cols)} FROM public.yad2_{type_}_log a left join yad2_{type_}_items_add b on a.id=b.id",
            conn)  #
        df['processing_date'] = pd.to_datetime(df['processing_date'])
        # fix square_meters:
        df['square_meter_build'] = df['square_meter_build'].combine_first(df['square_meters'])
        df = df.set_index('processing_date')
        print(f"Log Table stats: {df.index.min()}, {df.index.max()}")
        return df


# Can create also historic ratio as active will be all relevant items and those who closed AFTER the date.


# def create_percentiles_per_city(df, city, type_, resample_rule):
#     # df_f = df_t.query(f"city == '{c}' and active == False and  rooms_text == 3.0")
#     df = df.query(f"city_ == '{city}' and active == False")
#     x = df.resample(resample_rule, origin='end')['price'].describe()  # agg(['median', 'mean', 'std', 'size'])
#
#     title = f"{city} {get_heb_type_present(type_)} אחוזון {resample_rule[::-1]}"[::-1]
#     fig, ax = plt.subplots(figsize=(20, 10))
#     x[['25%', '50%', '75%']].plot(figsize=(8, 4), kind='line', stacked=False, title=title, ax=ax, marker='o')
#     # plt.ylim([0, None])
#     x.plot(y='count', ax=ax, secondary_y=True, linestyle='-.')
#     plt.savefig(f'resources/stats/plots_daily_{type_}/percentile_{city}.png')
#     # plt.show()
#     plt.close()


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


# def plot_ratio(res, type_):
#     res_ = res.copy()
#     res_.index = [x[::-1] for x in res.index]
#     heb_type = "שהושכרה" if type_ == "rent" else "שנמכרה"
#     res_.plot(kind='bar', figsize=(12, 5),
#               title=f"{datetime.today().date()} " + f"יחס הדירות הפנויות לכל דירה {heb_type} בחודש האחרון "[::-1])
#     print("lower is better for rent as more demand")
#     _ = plt.xticks(rotation=60)
#     plt.tight_layout()
#     plt.savefig(f'resources/stats/plots_daily_{type_}/active_ratio.png')
#     plt.close()


# def plot_scatter(df, res_ratio, type_):
#     df['time_alive'] = (datetime.today() - df['date_added']).dt.days
#     df_g = df[~df['active']].groupby('city')['time_alive'].agg(['mean', 'std', 'median', 'size'])
#     df_g = df_g.join(res_ratio, how='inner')
#     len_b = len(df_g)
#     df_g = df_g[df_g['size'] >= 30]
#     print(len_b, len(df_g))
#     fig, ax = plt.subplots(figsize=(12, 12))
#     ax.scatter(df_g['median'], df_g['r'])
#     ax.set_title("פיזור זמן מול היחס"[::-1])
#     ax.set_ylabel('יחס דירות באתר מול דירות שירדו בחודש האחרון'[::-1])
#     ax.set_xlabel('זמן חציוני לדירות באתר מרגע הפרסום עד להורדה'[::-1])
#
#     for i, txt in enumerate(df_g.index):
#         ax.annotate(txt[::-1], (df_g['median'][i] * 1.01, df_g['r'][i]))
#     plt.savefig(f'resources/stats/plots_daily_{type_}/scatter.png')
#     plt.close()


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


def run_type_stats(type_):
    print(f"Started daily stats for {type_}")
    eng = get_pg_engine()
    df = fetch_data_log(type_, eng)
    file_path = f"resources/df_log_{type_}.pk"
    # df = pd.read_pickle(file_path)
    df.to_pickle(file_path)
    pub_object(file_path)
    #
    os.makedirs(f"resources/stats/plots_daily_{type_}", exist_ok=True)
    get_price_changes(eng, type_)


if __name__ == '__main__':
    run_type_stats('forsale')
    run_type_stats('rent')
