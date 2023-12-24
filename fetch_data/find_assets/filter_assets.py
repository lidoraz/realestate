import pandas as pd
from datetime import datetime, timedelta

AI_STD_PCT = 0.07  # checks if ensemble agrees, removes anomalies


def filter_assets_by_config(df, c):
    df = df[df['city'].isin(c['cities'])]
    # print(df['city'].value_counts().to_dict())
    df = df[df['balconies']] if c['must_balcony'] else df
    df = df[df['parking'] > 0] if c['must_parking'] else df
    df = df[~df['is_agency']] if c['must_no_agency'] else df
    # note the change in name
    df = df[df['asset_status'].isin(c['asset_status'])] if c.get('asset_status') else df
    df = df[df['price'].between(c['min_price'], c['max_price'])]
    df = df[df['rooms'].between(c['min_rooms'], c['max_rooms'])]

    df = df[df['ai_std_pct'] < AI_STD_PCT]
    df = df[df['ai_price_pct'] < c['ai_price_pct_less_than']]
    df = df.sort_values('ai_price_pct')
    return df


def filter_assets_by_newly_published(df, days_back=1):
    past24h = pd.to_datetime(datetime.today()) - timedelta(days=days_back)
    df = df[pd.to_datetime(df['date_added']) >= past24h]
    return df


def filter_assets_by_discount(df, min_discount_pct=0.03, days_back=1):
    assert 0 < min_discount_pct < 1
    past24h = pd.to_datetime(datetime.today()) - timedelta(days=days_back)
    df = df[df['n_changes'] > 1].copy()
    df['last_date_price_update'] = pd.to_datetime(df['dt_hist'].str[-1])
    df = df[df['last_date_price_update'] >= past24h]
    df['recent_price_pct'] = df['price_hist'].str[-1] / df['price_hist'].str[-2] - 1
    df['recent_price_diff'] = df['price_hist'].str[-1] - df['price_hist'].str[-2]
    df = df[df['recent_price_pct'] < -min_discount_pct]
    return df


def combine_dfs_and_limit(dfs, sort_by, n_limit):
    dfs = [df.copy() for df in dfs]
    assert len(dfs) >= 2
    for idx, df in enumerate(dfs):
        df['filter_type'] = idx
    df_ = pd.concat(dfs, axis=0).sort_values(sort_by)
    df_ = df_[:n_limit]
    df_lst = []
    for idx in range(len(dfs)):
        df_lst.append(df_[df_['filter_type'] == idx])
    return df_lst
