# TODO: ADD TO DAILY STATS a flag for ACTIVE and NOT active such that we can see previous deals and investigate.
import os
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import KFold

from fetch_data.utils import filter_by_dist


def preprocess_history(df_hist, today_indexes):
    df_hist = df_hist.dropna()  # remove rows without prices
    # df_hist['price'] = df_hist['price'].astype(int)
    # pd.options.display.float_format = '{:,.2f}'.format
    df_hist = df_hist.drop_duplicates()
    print(len(df_hist))
    df = df_hist[df_hist['id'].isin(today_indexes)]  # filter only to available ids
    print(len(df))
    ids = df_hist.groupby('id').size()
    ids = ids[ids > 1].index

    price_hist = df_hist[df_hist['id'].isin(ids)].sort_values(['id', 'processing_date']).groupby('id').agg(
        dict(price=list, processing_date=list))
    first_price = price_hist['price'].apply(lambda x: x[0]).rename('first_price')
    # first_date = price_hist['processing_date'].apply(lambda x: x[0])
    last_price = price_hist['price'].apply(lambda x: x[-1]).rename('last_price')
    # last_date = price_hist['processing_date'].apply(lambda x: x[-1])
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


def add_distance(df, dist_km=1):
    print('Calculating Distance')

    def get_metrics(deal):
        pct = None
        length = 0
        if not np.isnan(deal['price']):
            try:
                other_close_deals = filter_by_dist(df, deal, dist_km)  # .join(df)
                other_close_deals = other_close_deals[
                    other_close_deals['rooms'].astype(float).astype(int) == int(float(deal['rooms']))]
                if len(other_close_deals):
                    # print(deal['last_price'], other_close_deals['last_price'].median())
                    pct = deal['price'] / other_close_deals['price'].median() - 1
                    length = len(other_close_deals)
            except:
                pass
        return pct, length

    try:
        from pandas_parallel_apply import DataFrameParallel
        dfp = DataFrameParallel(df, n_cores=os.cpu_count(), pbar=True)
        out_mp = dfp.apply(get_metrics, axis=1)
    except ModuleNotFoundError:
        print('pandas_parallel_apply is not installed! ignoring module')
        from tqdm import tqdm
        tqdm.pandas()
        out_mp = df.progress_apply(get_metrics, axis=1)
    res = pd.DataFrame(out_mp.tolist(), columns=['pct_diff_median', 'group_size'], index=out_mp.index)
    df = df.join(res)
    print('Finished Calculated Distance')
    return df


class MajorityVote:
    def __init__(self, n_folds, n_iters=500):
        self.clfs = [CatBoostRegressor(iterations=n_iters,
                                       loss_function="RMSE",
                                       early_stopping_rounds=500,
                                       allow_writing_files=False) for _ in range(n_folds)]
        self.n_folds = n_folds
        self.df_feat_imp = None

    def fit(self, X, y, cat_features):
        kf = KFold(self.n_folds)
        for idx, (train_idx, test_idx) in enumerate(kf.split(X, y)):
            print(idx)
            clf = self.clfs[idx]
            clf.fit(X.iloc[train_idx],
                    y.iloc[train_idx],
                    cat_features=cat_features,
                    use_best_model=True,
                    eval_set=(X.iloc[test_idx], y.iloc[test_idx]), verbose=100)

    def predict(self, x):
        res = [clf.predict(x) for clf in self.clfs]
        return res

    def predict_mean(self, x):
        res = [clf.predict(x) for clf in self.clfs]
        res = pd.DataFrame(res).T
        res.index = x.index
        return res.mean(axis=1)

    def predict_price(self, x):
        clf_preds = pd.DataFrame(self.predict(x)).T
        clf_res = pd.DataFrame(dict(ai_price=clf_preds.mean(axis=1).round(),
                                    ai_price_std=clf_preds.std(axis=1).round()))
        clf_res.index = x.index
        print(len(clf_res))
        # clf_res = y.to_frame().join(clf_res)  # .query('ai_std < 1_000_000').sort_values('ai_std')
        clf_res['ai_std_pct'] = (clf_res['ai_price'] + clf_res['ai_price_std']) / clf_res['ai_price'] - 1
        print(len(clf_res))
        return clf_res

    def get_feat_importance(self):
        res = []
        for clf in self.clfs:
            res.append({k: v for k, v in zip(clf.feature_names_, clf.feature_importances_)})
        self.df_feat_imp = pd.DataFrame(res)
        return self.df_feat_imp.mean(axis=0).sort_values(ascending=False)
        # feat_import [x for x ]
        # self.clfs._feature_importance


def add_ai_price(df, type_):
    print('Calculating AI Price')
    df['housing_unit'] = df['housing_unit'].astype(bool)  # .value_counts()
    df['info_text'] = df['info_text'].fillna('')
    df['is_keycrap'] = df['info_text'].str.contains('דמי מפתח')
    df['is_tama'] = df['info_text'].str.contains('תמא|תמ״א')
    must_have_cols = ['price', 'lat', 'long']
    bool_cols = ['renovated', 'balconies', 'elevator', 'is_agency',
                 'housing_unit',
                 'is_keycrap', 'is_tama'
                 ]
    num_cols = ['price_pct', 'rooms', 'square_meters',
                'square_meter_build', 'garden_area', 'floor', 'parking', 'number_of_floors']
    cat_features = ['asset_type', 'city', 'neighborhood', 'asset_status']
    df_d = df.dropna(subset=must_have_cols, axis=0).copy()
    df_d[bool_cols] = df_d[bool_cols].fillna(False)
    df_d[num_cols] = df_d[num_cols].fillna(-np.inf)
    df_d[cat_features] = df_d[cat_features].fillna('')
    df_d = df_d[must_have_cols + bool_cols + num_cols + cat_features]
    # remove anomalies
    if type_ == 'rent':
        df_d = df_d.query('700 <= price <= 30_000')
    elif type_ == 'forsale':
        df_d = df_d.query('250_000 <= price <= 50_000_000')
    else:
        raise ValueError()
    X = df_d.drop('price', axis=1)
    y = df_d['price']
    clf = MajorityVote(5, 5000)
    clf.fit(X, y, cat_features)
    print(clf.get_feat_importance())
    res = clf.predict_price(X)
    # mask_invalid = res['ai_std_pct'] > 0.3
    # # res['ai_price'] = res['ai_price']
    # res.loc[res[mask_invalid].index, 'ai_price'] = None
    df = pd.concat([df, res], axis=1)
    print('Finished Calculating AI Price')
    return df
