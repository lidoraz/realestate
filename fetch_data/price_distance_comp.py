import os
import numpy as np
import pandas as pd

from fetch_data.utils import filter_by_dist


def add_distance(df, dist_km=1):
    print(f'Calculating Distance for dist_km={dist_km}')

    def get_metrics(deal):
        other_prices = None
        length = 0
        if not np.isnan(deal['price']):
            try:
                other_close_deals = filter_by_dist(df, deal, dist_km)
                other_close_deals = other_close_deals[
                    other_close_deals['rooms'].astype(float).astype(int) == int(float(deal['rooms']))]
                if len(other_close_deals):
                    other_prices = other_close_deals['price'].median()
                    length = len(other_close_deals)
            except Exception as e:
                pass
        return other_prices, length

    try:
        from pandas_parallel_apply import DataFrameParallel
        dfp = DataFrameParallel(df, n_cores=os.cpu_count(), pbar=True)
        out_mp = dfp.apply(get_metrics, axis=1)
    except ModuleNotFoundError:
        print('pandas_parallel_apply is not installed! ignoring module')
        from tqdm import tqdm
        tqdm.pandas()
        out_mp = df.progress_apply(get_metrics, axis=1)
    res = pd.DataFrame(out_mp.tolist(), columns=['median_price', 'group_size'], index=out_mp.index)
    df = df.join(res, how="left")
    print('Finished Calculated Distance')
    return df
