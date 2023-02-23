# TODO: ADD TO DAILY STATS a flag for ACTIVE and NOT active such that we can see previous deals and investigate.


import json
import pandas as pd

from forsale.utils import additional_columns_lst

print("connecting to remote")


# df_hist = get_price_hist()

# df_today = pd.read_sql(f"Select {','.join(info_cols)} from {today_tbl} a", conn)


# df_today = get_today()
# print("Fetched rows:", len(df_today))
# df_today = df_today[~df_today['id'].duplicated()]
# print("After rem dup:", len(df_today))


def preproccess(df_today):
    info_rename = dict(row_2='city', row_1='street', line_1='rooms', line_2='floor', date='updated_at',
                       assetclassificationid_text='status', search_text='info_text')
    df_today['is_agency'] = df_today['feed_source'].apply(
        lambda x: True if x == 'commercial' else False if x == 'private' else None)
    df_today = df_today.set_index('id').rename(columns=info_rename)
    df_today['coordinates'] = df_today['coordinates'].apply(lambda x: json.loads(x.replace("'", '"')))
    # df_today['info_text'] = df_today['info_text'].apply(
    #     lambda x: x.split('תאור לקוח')[1] if len(x.split('תאור לקוח')) > 1 else None)

    df_today['floor'] = df_today['floor'].apply(
        lambda x: 0 if x == 'קומת קרקע' else x.split(' ')[1].replace('-', '') if len(
            x.split(' ')) > 1 else None).astype(float).astype('Int32')
    df_today['rooms'] = df_today['rooms'].apply(
        lambda x: None if x == 'לא צויינו חדרים' else '1' if x == 'חדר אחד' else x.split(' ')[0]).astype(float)
    df_today['type'] = df_today['city'].apply(lambda x: x.split(',')[0])
    df_today['city_loc'] = df_today['city'].apply(lambda x: ','.join(x.split(',')[1:-1]))
    df_today['city'] = df_today['city'].apply(lambda x: x.split(',')[-1])
    df_today['lat'] = df_today['coordinates'].apply(lambda x: x.get('latitude'))
    df_today['long'] = df_today['coordinates'].apply(lambda x: x.get('longitude'))
    return df_today


def preprocess_history(df_hist, today_indexes):
    df_hist = df_hist.dropna()
    df_hist['price'] = df_hist['price'].astype(int)
    # pd.options.display.float_format = '{:,.2f}'.format
    df_hist = df_hist.drop_duplicates()
    print(len(df_hist))
    df = df_hist[df_hist['id'].isin(today_indexes)]  # filter only to available ids
    print(len(df))
    df_p = df.pivot(index='id', columns='processing_date', values='price')
    df_p = df_p.ffill(axis=1).bfill(axis=1)
    ids = df_hist.groupby('id').size()
    ids = ids[ids > 1]
    # ids.index
    price_hist = df_hist[df_hist['id'].isin(ids.index)].sort_values(['id', 'processing_date']).groupby('id').agg(
        dict(price=list, processing_date=list))
    price_hist.columns = ['price_hist', 'dt_hist']
    price_pct = df_p.apply(lambda x: (x[-1] / x[0]) - 1, axis=1).rename('price_pct')
    price_diff = df_p.apply(lambda x: x[0] - x[-1], axis=1).rename('price_diff')
    first_price = df_p.apply(lambda x: x[0], axis=1).rename('first_price')
    last_price = df_p.apply(lambda x: x[-1], axis=1).rename('last_price')
    df_metrics = pd.concat([first_price, last_price, price_diff, price_pct, price_hist], axis=1)
    return df_metrics


def process_tables(df_today, df_hist):
    df_today = preproccess(df_today)
    cols_order = ['type', 'city', 'city_loc', 'rooms', 'square_meters', 'floor',
                  'status', 'is_agency', 'neighborhood', 'street',
                  'address_more', 'info_text', 'date_added', 'updated_at', 'lat', 'long'] + additional_columns_lst
    df_today = df_today[cols_order]
    today_indexes = df_today.index.to_list()
    df_metrics = preprocess_history(df_hist, today_indexes)
    df = pd.concat([df_metrics, df_today[~df_today.index.duplicated()]], axis=1)
    return df


import numpy as np

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


def add_distance(df, dist_km=1):
    from pandas_parallel_apply import DataFrameParallel
    def get_metrics(deal):
        pct = None
        length = 0
        if not np.isnan(deal['last_price']):
            try:
                other_close_deals = calc_dist(df, deal, dist_km)  # .join(df)
                other_close_deals = other_close_deals[
                    other_close_deals['rooms'].astype(float).astype(int) == int(float(deal['rooms']))]
                if len(other_close_deals):
                    # print(deal['last_price'], other_close_deals['last_price'].median())
                    pct = deal['last_price'] / other_close_deals['last_price'].median() - 1
                    length = len(other_close_deals)
            except:
                pass
        return pct, length

    dfp = DataFrameParallel(df, n_cores=8, pbar=True)
    out = dfp.apply(get_metrics, axis=1)
    df = df.join(pd.DataFrame(out.tolist(), columns=['pct_diff_median', 'group_size'], index=out.index))
    return df
    # df.to_pickle(f'/Users/lidorazulay/Documents/DS/realestate/resources/{output_df}.pk')
