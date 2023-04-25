# TODO: ADD TO DAILY STATS a flag for ACTIVE and NOT active such that we can see previous deals and investigate.
import pandas as pd
from fetch_data.utils import get_price_hist, get_today, get_nadlan

BUCKET_NAME = 'real-estate-public'


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


def run_daily_job(type_, eng):
    from fetch_data.price_regression import add_ai_price
    from fetch_data.price_distance_comp import add_distance
    df = fetch_prepare(type_, eng)
    df = add_ai_price(df, type_)
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


def pub_object(path):
    import boto3
    session = boto3.Session()
    s3 = session.resource('s3')
    buck = s3.Bucket(BUCKET_NAME)
    print(f"Uploading file:: {path} bucket: {BUCKET_NAME}")
    buck.upload_file(path, path)


def save_to_db(df, type_, eng, with_nadlan):
    # Not Used
    for t in range(5):
        try:
            with eng.connect() as conn:
                print(f"Pushing to daily {type_} to db")
                df.to_sql(f"dashboard_{type_}", conn, if_exists="replace")
                # if with_nadlan:
                #     run_nadlan_daily(conn, 210)
                break
        except Exception as e:
            print("failed to insert", t)

    # df = app_preprocess_df(df)
    # df = df.loc[:, ~df.columns.duplicated()].copy()
    # df = df.drop(columns=["img_url", "image_urls"])
