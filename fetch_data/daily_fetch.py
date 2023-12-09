# TODO: ADD TO DAILY STATS a flag for ACTIVE and NOT active such that we can see previous deals and investigate.
import pandas as pd
from fetch_data.utils import get_price_hist, get_today, get_nadlan

q_path = 'fetch_data/modeling/query_predict.sql'


def preprocess_history(df_hist, today_indexes):
    df_hist = df_hist.dropna()  # remove rows without prices
    df_hist = df_hist.drop_duplicates()
    print(len(df_hist))
    df = df_hist[df_hist['id'].isin(today_indexes)]  # filter only to available ids
    print(len(df))
    ids = df_hist.groupby('id').size()
    ids = ids[ids > 1].index
    price_hist = df_hist[df_hist['id'].isin(ids)].sort_values(['id', 'processing_date']).groupby('id').agg(
        dict(price=list, processing_date=list))
    first_price = price_hist['price'].apply(lambda x: x[0]).rename('first_price')
    last_price = price_hist['price'].apply(lambda x: x[-1]).rename('last_price')
    price_hist.columns = ['price_hist', 'dt_hist']
    price_pct = (last_price / first_price - 1).rename('price_pct')
    price_diff = (last_price - first_price).rename('price_diff')
    df_metrics = pd.concat([first_price, last_price, price_diff, price_pct, price_hist], axis=1)
    return df_metrics


def process_tables(df_today, df_hist):
    df_today = df_today.set_index('id')
    df_today = df_today[~df_today.index.duplicated()]
    today_indexes = df_today.index.to_list()
    df_metrics = preprocess_history(df_hist, today_indexes)
    df = df_today.join(df_metrics)
    return df


def run_daily_job(type_):
    # from fetch_data.price_regression import add_ai_price
    from ext.env import get_df_from_pg, get_query
    from fetch_data.modeling.calc_ai import add_ai_price
    from fetch_data.price_distance_comp import add_distance
    query = get_query(q_path)
    df = get_df_from_pg(query.format(asset_type=type_))
    df = df.set_index('id')

    # df = fetch_prepare(type_, eng)
    model_params = dict(n_folds=5, iterations=5000)
    df = add_ai_price(df, type_, model_params)
    df = add_distance(df)
    return df


def fetch_prepare(type_, eng):
    with eng.connect() as conn:
        df_hist = get_price_hist(type_, conn)
        df_today = get_today(type_, conn)
    return process_tables(df_today, df_hist)


def run_nadlan_daily(conn, day_backs, path_nadlan):
    print("Getting nadlan daily")
    df = get_nadlan(conn, day_backs)
    df.to_pickle(path_nadlan)
