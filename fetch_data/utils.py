import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from scrape_yad2.config import sql_today_dtypes, sql_items_dtypes

DF_NADLAN_RECENT_PK = "resources/df_nadlan_recent.pk"


TABLES = dict(forsale=dict(hist_tbl="yad2_forsale_history",
                           today_tbl="yad2_forsale_today",
                           item_tbl="yad2_forsale_items_add",
                           output_df="yad2_forsale_df"),
              rent=dict(hist_tbl="yad2_rent_history",
                        today_tbl="yad2_rent_today",
                        item_tbl="yad2_rent_items_add",
                        output_df="yad2_rent_df"))


def get_tbl(type, tbl_type):
    type_dict = TABLES.get(type)
    tbl = type_dict.get(tbl_type)
    return tbl


# additional_columns_lst = ['parking', 'balconies', 'number_of_floors', 'renovated', 'asset_exclusive_declaration',
#                           'air_conditioner', 'bars', 'elevator', 'boiler', 'accessibility', 'shelter', 'warhouse',
#                           'tadiran_c', 'furniture', 'flexible_enter_date', 'kosher_kitchen', 'housing_unit',
#                           'info_text', 'image_urls']
# info_cols = ['a.id', 'row_2', 'row_1', 'line_1', 'a.square_meters', 'line_2', 'neighborhood', 'merchant',
#              'assetclassificationid_text', 'coordinates', 'feed_source', 'address_more', 'date_added',  # 'search_text',
#              'date']


def get_price_hist(type_, conn):
    hist_tbl = get_tbl(type_, "hist_tbl")
    df_hist = pd.read_sql(f"select id, price, processing_date from {hist_tbl}", conn)
    print(df_hist.groupby('processing_date').size())
    max_date = df_hist['processing_date'].max()
    print(f"DATA ON REMOTE IS UPDATED TO::", max_date)
    if (datetime.today() - pd.to_datetime(max_date)).days > 1:
        raise AssertionError("Data is not updated, check remote!!")
    return df_hist


def get_today(type, conn):
    today_tbl = get_tbl(type, "today_tbl")
    item_tbl = get_tbl(type, "item_tbl")
    tbl_today_cols = [f'a.{c}' for c in sql_today_dtypes.keys()]
    tbl_items_cols = [f'b.{c}' for c in sql_items_dtypes.keys() if c not in ('id', 'square_meters', 'processing_date')]
    q = f"""
    SELECT {','.join(tbl_today_cols)}, {','.join(tbl_items_cols)} FROM {today_tbl} a inner join {item_tbl} b on a.id = b.id
    """ # 56691
    df_today = pd.read_sql(q, conn)
    return df_today


def get_nadlan(conn, days_back):
    q = """SELECT {cols_str} from nadlan_trans where 
    trans_date > TO_DATE('{from_date}', 'YYYY-MM-DD')
    and price_declared = price_estimated
    and deal_part = 1
    """
    used_cols = ["trans_date", "city", "n_rooms", "price_declared",
                 "sq_m_gross", "sq_m_net", "floor", "n_floors",
                 "year_built", "parking", "lat", "long",
                 'gush', 'helka']
    dt = (datetime.today() - pd.to_timedelta(f"{days_back}D")).date()
    q_frmt = q.format(cols_str=', '.join(used_cols), from_date=str(dt))
    #     conn.execute(wrap(q)).all()
    df = pd.read_sql(q_frmt, conn)

    df['trans_date'] = pd.to_datetime(df['trans_date'])
    df = df.set_index('trans_date')
    return df


def get_nadlan_trans(deal, days_back, dist_km, filter_room):
    if np.isnan(deal['lat']) or np.isnan(deal['long']):
        raise ValueError('lat or long are not valid')
    dt_back = datetime.today() - pd.to_timedelta(f'{days_back}D')
    df_nadlan = pd.read_pickle(DF_NADLAN_RECENT_PK)
    df_nadlan = df_nadlan[df_nadlan.index > dt_back]
    if filter_room:
        df_nadlan = df_nadlan[df_nadlan['n_rooms'].round() == deal['rooms'].round()]
    df_nadlan = filter_by_dist(df_nadlan, deal, dist_km)
    df_nadlan.attrs['days_back'] = days_back
    return df_nadlan


def plot_deal_vs_sale_sold(other_close_deals, df_tax, deal, round_rooms=True):
    # When the hist becomes square thats because there a huge anomaly in terms of extreme value
    if round_rooms:
        sale_items = \
            other_close_deals[other_close_deals['rooms'].astype(float).astype(int) == int(float(deal['rooms']))][
                'last_price']
    else:
        sale_items = other_close_deals[other_close_deals['rooms'] == deal['rooms']]['last_price']
    sale_items.rename(f'last_price #{len(sale_items)}').hist(bins=min(70, len(sale_items)), legend=True, alpha=0.8)
    sold_items = df_tax['mcirMorach']
    days_back = df_tax.attrs['days_back']
    if len(sold_items):
        sold_items.rename(f'realPrice{days_back}D #{len(sold_items)}').hist(bins=min(70, len(sold_items)), legend=True,
                                                                            alpha=0.8)
    plt.axvline(deal['last_price'], color='red', label=f"{deal['last_price']:,.0f}", linewidth=2)
    str_txt = f"{'חדרים'[::-1]} {deal['rooms']},{deal['type'][::-1]}, {deal['street'][::-1]}, {deal['city'][::-1]}, {deal['price_pct']:0.2%}"
    plt.xlim([deal['last_price'] // 2, deal['last_price'] * 3])
    plt.title(str_txt)
    plt.legend()

    # plt.show()


def haversine(lat1, lon1, lat2, lon2, to_radians=True, earth_radius=6371):
    """
    slightly modified version: of http://stackoverflow.com/a/29546836/2901002

    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees or in radians)

    All (lat, lon) coordinates must have numeric dtypes and be of equal length.

    """
    if to_radians:
        lat1, lon1 = np.radians([lat1, lon1])
        lat2, lon2 = np.radians([lat2, lon2])

    a = np.sin((lat2 - lat1) / 2.0) ** 2 + \
        np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2.0) ** 2

    return earth_radius * 2 * np.arcsin(np.sqrt(a))


def filter_by_dist(df, deal, distance):
    dist = haversine(df['lat'], df['long'], deal['lat'], deal['long'])
    df['dist'] = dist
    df = df[df['dist'] < distance]
    return df
