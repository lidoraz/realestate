from forsale.daily_fetch import process_tables
from forsale.utils import get_connetor, get_today, get_price_hist

if __name__ == '__main__':
    conn = get_connetor()
    type = 'rent'
    df_hist = get_price_hist(type, conn)
    df_today = get_today(type, conn)

    df = process_tables(df_today, df_hist)

    df.to_pickle(f'/Users/lidorazulay/Documents/DS/realestate/resources/yad2_{type}_df.pk')
    print()
