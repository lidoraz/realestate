from forsale.daily_fetch import process_tables, add_ai_price
from forsale.utils import get_connetor, get_today, get_price_hist

if __name__ == '__main__':
    conn = get_connetor()
    type = 'rent'
    df_hist = get_price_hist(type, conn)
    df_today = get_today(type, conn)

    df = process_tables(df_today, df_hist)
    df = add_ai_price(df, type)
    df.to_pickle(f'resources/yad2_{type}_df.pk')
    print()
