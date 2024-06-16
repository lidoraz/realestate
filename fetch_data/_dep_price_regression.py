# import pandas as pd
# import numpy as np
# from catboost import CatBoostRegressor
# from sklearn.model_selection import KFold
#
#
# class MajorityVote:
#     def __init__(self, n_folds, n_iters=500):
#         self.clfs = [CatBoostRegressor(iterations=n_iters,
#                                        loss_function="RMSE",
#                                        early_stopping_rounds=500,
#                                        allow_writing_files=False) for _ in range(n_folds)]
#         self.n_folds = n_folds
#         self.df_feat_imp = None
#
#     def fit(self, X, y, cat_features):
#         kf = KFold(self.n_folds)
#         for idx, (train_idx, test_idx) in enumerate(kf.split(X, y)):
#             print(idx)
#             clf = self.clfs[idx]
#             clf.fit(X.iloc[train_idx],
#                     y.iloc[train_idx],
#                     cat_features=cat_features,
#                     use_best_model=True,
#                     eval_set=(X.iloc[test_idx], y.iloc[test_idx]), verbose=100)
#
#     def predict(self, x):
#         res = [clf.predict(x) for clf in self.clfs]
#         return res
#
#     def predict_mean(self, x):
#         res = [clf.predict(x) for clf in self.clfs]
#         res = pd.DataFrame(res).T
#         res.index = x.index
#         return res.mean(axis=1)
#
#     def predict_price(self, x):
#         clf_preds = pd.DataFrame(self.predict(x)).T
#         clf_res = pd.DataFrame(dict(ai_price=clf_preds.mean(axis=1).round(),
#                                     ai_price_std=clf_preds.std(axis=1).round()))
#         clf_res.index = x.index
#         print(len(clf_res))
#         # clf_res = y.to_frame().join(clf_res)  # .query('ai_std < 1_000_000').sort_values('ai_std')
#         clf_res['ai_std_pct'] = (clf_res['ai_price'] + clf_res['ai_price_std']) / clf_res['ai_price'] - 1
#         print(len(clf_res))
#         return clf_res
#
#     def get_feat_importance(self):
#         res = []
#         for clf in self.clfs:
#             res.append({k: v for k, v in zip(clf.feature_names_, clf.feature_importances_)})
#         self.df_feat_imp = pd.DataFrame(res)
#         return self.df_feat_imp.mean(axis=0).sort_values(ascending=False)
#
#
# def add_feat(df):
#     df['housing_unit'] = df['housing_unit'].astype(bool)  # .value_counts()
#     df['info_text'] = df['info_text'].fillna('')
#     df['is_keycrap'] = df['info_text'].str.contains('דמי מפתח')
#     # df['is_tama'] = df['info_text'].str.contains('תמא|תמ״א')
#     df['is_tama_be'] = df['info_text'].str.contains('לפני תמ"א|לפני תמא')
#     df['is_tama_af'] = df['info_text'].str.contains('אחרי תמ"א|אחרי תמא')
#     # df[ df['info_text'].str.match('לפני תמ"א|לפני תמא')]['info_text']
#     df['is_zehut'] = df['info_text'].str.match('זכות לדירה')
#     return df
#
#
# def fill_na(df):
#     must_have_cols = ['price', 'lat', 'long']
#     bool_cols = ['renovated', 'balconies', 'elevator', 'is_agency',
#                  'housing_unit',
#                  'is_keycrap', 'is_tama_be', 'is_tama_af', 'is_zehut']
#     num_cols = ['price_pct', 'rooms', 'square_meters',
#                 'square_meter_build', 'garden_area', 'floor', 'parking', 'number_of_floors']
#     cat_features = ['asset_type', 'city', 'neighborhood', 'asset_status']
#     df_d = df.dropna(subset=must_have_cols, axis=0).copy()
#     df_d[bool_cols] = df_d[bool_cols].fillna(False)
#     df_d[num_cols] = df_d[num_cols].fillna(-np.inf)
#     df_d[cat_features] = df_d[cat_features].fillna('')
#     df_d = df_d[must_have_cols + bool_cols + num_cols + cat_features]
#     return df_d, cat_features
#
#
# def remove_anomiles(df_d, type_):
#     if type_ == 'rent':
#         df_d = df_d.query('700 <= price <= 30_000')
#     elif type_ == 'forsale':
#         df_d = df_d.query('250_000 <= price <= 50_000_000')
#     else:
#         raise ValueError()
#     return df_d
#
#
# def get_feat_target(df_d, target):
#     X = df_d.drop(target, axis=1)
#     y = df_d[target]
#     return X, y
#
#
# def add_ai_price(df, type_):
#     print('Calculating AI Price')
#     df = add_feat(df)
#     df_d, cat_features = fill_na(df)
#     df_d = remove_anomiles(df_d, type_)
#     X, y = get_feat_target(df_d, 'price')
#     clf = MajorityVote(5, 5000)
#     clf.fit(X, y, cat_features)
#     print(clf.get_feat_importance())
#     res = clf.predict_price(X)
#     df = pd.concat([df, res], axis=1)
#     print('Finished Calculating AI Price')
#     return df
