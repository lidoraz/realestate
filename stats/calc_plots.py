from datetime import datetime, timedelta

import pandas as pd

from stats.plots import create_percentiles_per_city_f


def run_for_cities(df, type_, n_cities=9, resample_rule='7D', use_median=True):
    figs = []
    sel_cities = ['חיפה', 'ירושלים', 'תל אביב יפו', 'רמת גן', 'אשדוד', 'ראשון לציון', 'ירשולים', 'באר שבע', 'הרצליה',
                  'נתניה']
    df = df[df['city'].isin(sel_cities)]
    for city, grp in df.groupby('city'):
        fig = create_percentiles_per_city_f(df, city, type_, resample_rule, 'price', use_median)
        figs.append(fig)
    return figs  # create_percentiles_per_city(df, city, type_, resample_rule)


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
