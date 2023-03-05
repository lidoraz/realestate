import pandas as pd
from fetch_data.daily_fetch import process_tables, add_distance, add_ai_price
from fetch_data.utils import get_today, get_price_hist, get_nadlan
from scrape_nadlan.utils_insert import get_engine

# os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    eng = get_engine()
    with eng.connect() as conn:
        df = get_nadlan(conn, 180)
        df.to_pickle("resources/df_nadlan_recent.pk")
        type_ = 'forsale'
        df_hist = get_price_hist(type_, conn)
        df_today = get_today(type_, conn)
        df = process_tables(df_today, df_hist)
        df = add_distance(df)
        df.to_pickle("test.pk")
        df = pd.read_pickle('test.pk')
        df = add_ai_price(df, type_)
        path = f'resources/yad2_{type_}_df.pk'
        df.to_pickle(path)
