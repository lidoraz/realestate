import os
import numpy as np
import pandas as pd
from fetch_data.utils import filter_by_dist


def add_median_distance(df, dist_km=1):
    print(f'Calculating median distance for dist_km={dist_km}')
    cols_r = ['lat_r', 'long_r', 'rooms_r']
    df[cols_r[0]] = np.radians(df['lat'])
    df[cols_r[1]] = np.radians(df['long'])
    df[cols_r[2]] = df['rooms'].astype(float).astype(int)
    df_r = df[cols_r + ['price']]

    def get_metrics(deal):
        other_close_deals = filter_by_dist(df_r[df_r['rooms_r'] == deal['rooms_r']],
                                           deal,
                                           dist_km,
                                           is_cords_radians=True)
        return other_close_deals['price'].median(), other_close_deals.shape[0]

    try:
        from pandas_parallel_apply import DataFrameParallel
        dfp = DataFrameParallel(df, n_cores=os.cpu_count(), pbar=True)
        out_mp = dfp.apply(get_metrics, axis=1)
    except ModuleNotFoundError:
        print('pandas_parallel_apply is not installed! ignoring module')
        from tqdm import tqdm
        tqdm.pandas()
        out_mp = df.progress_apply(get_metrics, axis=1)
    df = df.drop(columns=cols_r)
    res = pd.DataFrame(out_mp.tolist(), columns=['median_price', 'group_size'], index=out_mp.index)
    df = df.join(res, how="left")
    print('Finished Calculated Distance')
    return df


if __name__ == '__main__':
    df = pd.read_pickle("../resources/yad2_rent_df.pk")
    assert not df['price'].isna().any()
    print(df.columns)
    df = add_median_distance(df[:5000], 2)
    print(df.columns)
