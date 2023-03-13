from fetch_data.daily_fetch import run_daily_job, save_to_db, run_nadlan_daily, pub_object
from scrape_nadlan.utils_insert import get_engine


def daily_forsale():
    type_ = 'forsale'
    path = f'resources/yad2_{type_}_df.pk'
    eng = get_engine()
    path_nadlan = "resources/df_nadlan_recent.pk"
    import pandas as pd
    # df = pd.read_pickle(path)
    df = run_daily_job(type_, eng)
    df.to_pickle(path)
    with eng.connect() as conn:
        run_nadlan_daily(conn, 240, path_nadlan)
    pub_object(path)
    pub_object(path_nadlan)

    # conn = sqlite3.connect("resources/dummy.db")
    # problem_cols = ['info_text']

    # df = df.drop(columns=problem_cols)
    # df = df.drop(columns="processing_date")
    # df = df.
    # for c, dtype in df.dtypes.items():
    #     if dtype == "object":
    #         print(c)
    #         df[c] = df[c].str.replace("'", '"')
    # df['info_text'] = df['info_text'].str.replace("'", '"')
    # df.to_sql(type_, conn, if_exists="replace")
    # save_to_db(df, type_, eng, with_nadlan=True)


if __name__ == '__main__':
    daily_forsale()
