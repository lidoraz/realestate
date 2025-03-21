from ext.env import get_query, get_df_from_pg
from fetch_data.modeling.MajorityVote import MajorityVote
from fetch_data.modeling.utils import get_model_cols_n_cat, filter_bad_loc_assets
import pandas as pd
import os
import pickle
import time

FILE_PATH = "resources/regressor_majority_{asset_type}_{n_folds}_{iterations}.pk"
# MAJORITY_N_FOLDS = 5
# ITERATIONS = 5000
metric = 'MAE'  # 'RMSE'


##  IF TRAINING MODEL ONCE PER WEEK // NEED TO DEVELOP WAY TO FILTER OUT LOCATIONS AS NULL
##  MAYBE HAVE SEPARATE LIST OF BAD LOCATIONS


def get_train_config(iterations=5_000):
    regressor_config = {
        'iterations': iterations,  # 15_000,
        'objective': metric,
        # 'learning_rate': 0.0238,
        # 'colsample_bylevel': 0.0922,
        # 'max_depth': 10,
        # 'boosting_type': 'Ordered',
        # 'bootstrap_type': 'MVS'
    }
    return regressor_config


def _limit_prices(asset_type):
    if asset_type == 'rent':
        price_between_sql = "AND price between 700 and 30000"
    elif asset_type == 'forsale':
        price_between_sql = "AND price between 250000 and 50000000"
    else:
        raise ValueError()
    return price_between_sql


def calc_within_pct(y_true, y_pred, tol_pct=7, verbose=False):
    assert y_pred.shape == y_true.shape
    # Calculate the tolerance amount
    tolerance_amount = (tol_pct / 100) * y_true
    # Create a column to indicate whether the prediction is within the tolerance range
    within_tolerance = abs(y_true - y_pred) <= tolerance_amount
    # Calculate the percentage of accurate predictions within the tolerance range
    accurate_predictions_percentage = (within_tolerance.sum() / len(y_true)) * 100
    if verbose:
        print(f"Accuracy within {tol_pct}% tolerance range: {accurate_predictions_percentage:.2f}%")
    return accurate_predictions_percentage


def train_model(asset_type, n_folds, log_y, regressor_config=None):
    print(f"Training Regressor Majority vote model, {n_folds=}, {log_y=}, {asset_type=}")
    if regressor_config is None:
        regressor_config = get_train_config()
    path = os.path.join(os.path.dirname(__file__), 'query_train.sql')
    query = get_query(path)
    price_between_sql = _limit_prices(asset_type)
    query = query.format(asset_type=asset_type, price_between_sql=price_between_sql)
    df = get_df_from_pg(query)
    print(f"Fetched {len(df)} rows from pg ({asset_type}), {price_between_sql=}")  # data updated to {df['processing_date'].max()}

    cols, cat_features = get_model_cols_n_cat()
    x, y = get_feat_target(df[cols])
    clf = MajorityVote(n_folds, log_y, regressor_config)
    clf.fit(x, y, cat_features)
    print(clf.get_feat_importance())
    y_pred = clf.predict_price(x[x['is_active']])['ai_price']
    y_true = y[x['is_active']]
    _ = calc_within_pct(y_true, y_pred, verbose=True)
    return clf


def add_ai_price(df, asset_type, model_params, set_no_active=True, filter_bad_locs=True):
    print(f'Predicting AI Price (v2) - {asset_type=}')
    path = FILE_PATH.format(asset_type=asset_type,
                            n_folds=model_params['n_folds'],
                            iterations=model_params['iterations'])
    assert os.path.exists(path), f"Model is missing, train first.\n({path})"
    with open(path, 'rb') as f:
        clf = pickle.load(f)
        print("model created at:", pd.to_datetime(os.path.getctime(path), unit='s'))
    cols, _ = get_model_cols_n_cat()
    df_f = df.copy()
    if filter_bad_locs:
        df_f = filter_bad_loc_assets(df, asset_type)
    df_f = df_f[cols].drop(columns=['price'])
    if set_no_active:  # setting to no active to emulate sold conditions
        df_f['is_active'] = False
    df_preds = clf.predict_price(df_f)
    df = df.join(df_preds, how='left')
    print(f"Added {len(df_preds):,.0f} predictions to {len(df):,.0f} assets")
    print(clf.get_feat_importance())
    print('Finished Calculating and Adding AI Price')
    return df


def add_rent_price_to_forsale(df, rent_model_params):
    ai_cols = ['ai_price', 'ai_price_std', 'ai_std_pct']

    df_to_predict = df.drop(columns=ai_cols).copy()
    # reset these columns to avoid extreme deviations in the predictions
    df_to_predict['price_pct'] = 0
    df_to_predict['std_price_chg'] = 0
    df_ = add_ai_price(df_to_predict, 'rent', rent_model_params)
    df_ = df_[ai_cols]
    df_.columns = [f"{c}_rent" for c in df_.columns]
    df = pd.concat([df, df_], axis=1)
    df['estimated_rent_annual_return'] = 12 * df['ai_price_rent'] / df['price']
    return df


def get_feat_target(df_d, target='price'):
    X = df_d.drop(target, axis=1)
    y = df_d[target]
    return X, y


def plot_train_history(clf, asset_type):
    import matplotlib.pyplot as plt
    learn = clf.evals_result_['learn'][metric]
    validation = clf.evals_result_['validation'][metric]
    plt.plot(learn, label='train')
    plt.plot(validation, label='val')
    plt.legend()
    plt.ylabel(metric)
    plt.xlabel('it')
    plt.title(f"Cat Regressor {asset_type}")
    plt.savefig(f'regressor_train_{asset_type}.png')


def save_model(clfs, asset_type, n_folds, regressor_config):
    path = FILE_PATH.format(asset_type=asset_type,
                            n_folds=n_folds,
                            iterations=regressor_config['iterations'])
    with open(path, "wb") as f:
        pickle.dump(clfs, f)


def test_train_pipeline(asset_type, n_folds, log_y, cfg):
    t0 = time.time()
    clfs = train_model(asset_type, n_folds, log_y, cfg)
    save_model(clfs, asset_type, n_folds, cfg)
    plot_train_history(clfs.clfs[0], asset_type)
    elapsed = (time.time() - t0) / 3600
    print(f"FINISHED {asset_type} training :: {elapsed:.2f} hours")


if __name__ == '__main__':
    # Tests for 25 June 2024
    # n_folds=5, log_y=True, asset_type='forsale' MAE (loc fix) => Accuracy within 7% tolerance range: 53.74%
    # Accuracy within 7% tolerance range: 53.74%
    # Accuracy within 7% tolerance range: 53.53% (LOG, MAE)
    # Accuracy within 7% tolerance range: 52.69% (NO LOG, MAE)
    # Accuracy within 7% tolerance range: 52.88% (NO LOG, after fix locations, MAE)
    # Accuracy within 7% tolerance range: 52.56% (WITH LOG, after fix locations, RMSE)
    # n_folds=5, log_y=False, asset_type='forsale' RMSE (loc fix) => Accuracy within 7% tolerance range: 46.41%
    cfg = get_train_config()
    cfg['iterations'] = 5_000  # 100_000 # 50000  # 5000
    log_y = True
    n_folds = 5
    test_train_pipeline("forsale", n_folds, log_y, cfg)
    # test_train_pipeline("rent", n_folds, log_y, cfg)
