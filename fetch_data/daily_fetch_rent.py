from fetch_data.daily_fetch import process_tables, add_ai_price, add_distance
from fetch_data.utils import get_today, get_price_hist
from scrape_nadlan.utils_insert import get_engine

if __name__ == '__main__':
    eng = get_engine()
    with eng.connect() as conn:
        type_ = 'rent'
        df_hist = get_price_hist(type_, conn)
        df_today = get_today(type_, conn)

        df = process_tables(df_today, df_hist)
        df = add_distance(df)
        df = add_ai_price(df, type_)
        df.to_pickle(f'resources/yad2_{type_}_df.pk')
        print()
