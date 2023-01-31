import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from pyproj import Transformer
import pandas as pd
from datetime import datetime


def get_similar_closed_deals(deal, days_back, dist_km, with_room):
    if np.isnan(deal['lat']) or np.isnan(deal['long']):
        raise ValueError('lat or long are not valid')
    wgs84_itm_to_trans = Transformer.from_crs(4326, 2039)
    cor_x, cor_y = wgs84_itm_to_trans.transform(deal['lat'], deal['long'])
    # print(cor_x, cor_y)
    dt_back = (datetime.today() - pd.to_timedelta(f'{days_back}D')).strftime('%Y%m%d')
    sql_dist_cond = f'and sqrt((pow(corX - {cor_x}, 2) + pow(corY - {cor_y}, 2))/1000000)'
    sql_room_cond = f"and round(misHadarim) = round({deal['rooms']})" if with_room else ""
    q = f'select {sql_dist_cond.split("and")[1]} as dist_from_deal, *  from trans where tariska > {dt_back}' \
        f' {sql_dist_cond} < {dist_km}' \
        f' {sql_room_cond}' \
        f' and helekNimkar = 1.0'
    # print(q)
    con_taxes = sqlite3.connect('/Users/lidorazulay/Documents/DS/realestate/resources/nadlan.db')
    df_tax = pd.read_sql(q, con_taxes)
    df_tax.attrs['days_back'] = days_back
    return df_tax


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


def calc_dist(df, deal, distance):
    dist = haversine(df['lat'], df['long'], deal['lat'], deal['long'])
    df['dist'] = dist
    df = df[df['dist'] < distance]
    return df
