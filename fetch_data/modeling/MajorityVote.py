import pandas as pd
from catboost import CatBoostRegressor
from sklearn.model_selection import KFold


class MajorityVote:
    def __init__(self, n_folds, regressor_kwargs):
        self.clfs = [CatBoostRegressor(**regressor_kwargs,
                                       early_stopping_rounds=500,
                                       allow_writing_files=False) for _ in range(n_folds)]
        self.n_folds = n_folds
        self.df_feat_imp = None

    def fit(self, X, y, cat_features):
        if self.n_folds == 1:
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(X, y)
            self.clfs[0].fit(X_train,
                             y_train,
                             cat_features=cat_features,
                             use_best_model=True,
                             eval_set=(X_test, y_test), verbose=100)
        else:
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
        clf_res['ai_std_pct'] = (clf_res['ai_price'] + clf_res['ai_price_std']) / clf_res['ai_price'] - 1
        return clf_res

    def get_feat_importance(self):
        res = []
        for clf in self.clfs:
            res.append({k: v for k, v in zip(clf.feature_names_, clf.feature_importances_)})
        self.df_feat_imp = pd.DataFrame(res)
        return self.df_feat_imp.mean(axis=0).sort_values(ascending=False)
